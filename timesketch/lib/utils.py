# Copyright 2015 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Common functions and utilities."""

from __future__ import unicode_literals

import colorsys
import csv
import datetime
import email
import json
import logging
import random
import smtplib
import time
import codecs

import pandas
import six

from dateutil import parser
from flask import current_app
from pandas import Timestamp

from timesketch.lib import errors

logger = logging.getLogger("timesketch.utils")

# Fields to scrub from timelines.
FIELDS_TO_REMOVE = ["_id", "_type", "_index", "_source", "__ts_timeline_id"]

# Number of rows processed at once when ingesting a CSV file.
DEFAULT_CHUNK_SIZE = 10000

# Columns that must be present in ingested timesketch files.
TIMESKETCH_FIELDS = frozenset({"message", "datetime", "timestamp_desc"})

# Columns that must be present in ingested redline files.
REDLINE_FIELDS = frozenset({"Alert", "Tag", "Timestamp", "Field", "Summary"})


def random_color():
    """Generates a random color.

    Returns:
        Color as string in HEX
    """
    hue = random.random()
    golden_ratio_conjugate = (1 + 5**0.5) / 2
    hue += golden_ratio_conjugate
    hue %= 1
    rgb = tuple(int(i * 256) for i in colorsys.hsv_to_rgb(hue, 0.5, 0.95))
    return "{0:02X}{1:02X}{2:02X}".format(rgb[0], rgb[1], rgb[2])


def _parse_tag_field(row):
    """Reading in a tag field and converting to a list of strings."""
    if isinstance(row, (list, tuple)):
        return row

    if not isinstance(row, str):
        row = str(row)

    if row.startswith("[") and row.endswith("]"):
        return json.loads(row)

    if row == "-":
        return []

    if "," in row:
        return row.split(",")

    return [row]


def _scrub_special_tags(dict_obj):
    """Remove OpenSearch specific fields from a dict."""
    for field in FIELDS_TO_REMOVE:
        if field in dict_obj:
            _ = dict_obj.pop(field)


def _validate_csv_fields(mandatory_fields, data, headers_mapping=None):
    """Validate parsed CSV fields against mandatory fields.

    Args:
        mandatory_fields: a list of fields that must be present.
        data: a DataFrame built from the ingested file.
        headers_mapping: list of dicts containing:
                         (i) target header we want to insert [key=target],
                         (ii) sources header we want to rename/combine [key=source],
                         (iii) def. value if we add a new column [key=default_value]
    Raises:
        RuntimeError: if there are missing fields.
    """

    mandatory_set = set(mandatory_fields)
    parsed_set = set(data.columns)
    headers_missing = mandatory_set - parsed_set

    if headers_mapping:
        check_mapping_errors(parsed_set, headers_mapping)
        headers_mapping_set = set(m["target"] for m in headers_mapping)
        headers_missing = headers_missing - headers_mapping_set
    else:
        headers_mapping_set = {}

    if headers_missing:
        headers_missing_string = ", ".join(list(headers_missing))
    else:
        return

    if headers_mapping_set:
        headers_mapping_string = ", ".join(list(headers_mapping_set))
    else:
        headers_mapping_string = "None"

    if parsed_set:
        parset_set_string = ", ".join(list(parsed_set))
    else:
        parset_set_string = "None"

    raise RuntimeError(
        f"Missing mandatory CSV headers."
        f"Mandatory headers: {', '.join(list(mandatory_set))}"
        f"Headers found in the file: {parset_set_string}"
        f"Headers provided in the mapping: {headers_mapping_string}"
        f"Headers missing: {headers_missing_string}"
    )


def validate_indices(indices, datastore):
    """Returns a list of valid indices.

    This function takes a list of indices, checks to see if they exist
    and then returns the list of indices that exist within the datastore.

    Args:
        indices (list): List of indices.
        datastore (OpenSearchDataStore): a data store object.

    Returns:
        list of indices that exist within the datastore.
    """
    return [i for i in indices if datastore.client.indices.exists(index=i)]


def check_mapping_errors(headers, headers_mapping):
    """Sanity check for headers mapping

    Args:
        csv_headers: list of headers found in the CSV file.
        headers_mapping: list of dicts containing:
                         (i) target header we want to insert [key=target],
                         (ii) sources header we want to rename/combine [key=source],
                         (iii) def. value if we add a new column [key=default_value]

    Raises:
        RuntimeError: if there are errors in the headers mapping.
    """

    # 1. Do the mapping only if the mandatory header is missing, and
    # 2. When create a new column, need to set a default value
    candidate_headers = []
    for mapping in headers_mapping:
        if mapping["target"] in headers:
            raise RuntimeError(
                "Headers mapping is wrong.\n"
                "Mapping done only if the mandatory header is missing"
            )
        if mapping["source"]:
            # 3. Check if any of the headers specified in headers mapping
            # is in the headers list
            for source in mapping["source"]:
                if source not in headers:
                    raise RuntimeError(
                        f"Value specified in the headers mapping not found in the CSV\n"
                        f"Headers mapping: {', '.join(mapping['source'])}\n"
                        f"Sources column/s: {source}\n"
                        f"All Headers: {', '.join(headers)}"
                    )

            # Update the headers list that we will substitute/rename
            # we do this check only over the header column that will be renamed,
            # i.e., when mapping["source"] has only 1 value
            if len(mapping["source"]) == 1:
                candidate_headers.append(mapping["source"][0])

        else:
            if not mapping["default_value"]:
                raise RuntimeError(
                    f"Headers mapping is wrong.\n"
                    f"Error to create new column {mapping['target']}. "
                    f"When create a new column, a default value must be assigned"
                )
    # 4. check if two or more mandatory headers are mapped
    #    to the same existing header
    if len(candidate_headers) != len(set(candidate_headers)):
        raise RuntimeError(
            "Headers mapping is wrong.\n"
            "2 or more mandatory headers are "
            "mapped to the same existing CSV headers"
        )


def rename_csv_headers(chunk, headers_mapping):
    """ "Rename the headers of the dataframe

    Args:
        chunk: dataframe to be modified
        headers_mapping: list of dicts containing:
                         (i) target header we want to insert [key=target],
                         (ii) sources header we want to rename/combine [key=source],
                         (iii) def. value if we add a new column [key=default_value]

    Returns: the dataframe with renamed headers
    """
    headers_mapping.sort(
        key=lambda x: len(x["source"]) if x["source"] else 0, reverse=True
    )
    for mapping in headers_mapping:
        if not mapping["source"]:
            # create new column with a given default value
            chunk[mapping["target"]] = mapping["default_value"]
        elif len(mapping["source"]) > 1:
            # concatanete multiple source headers into a new one
            chunk[mapping["target"]] = ""
            for column in mapping["source"]:
                chunk[mapping["target"]] += (
                    column + ":" + chunk[column].map(str) + " | "
                )
        else:
            # just rename the header
            chunk.rename(
                columns={mapping["source"][0]: mapping["target"]}, inplace=True
            )
    return chunk


def read_and_validate_csv(
    file_handle, delimiter=",", mandatory_fields=None, headers_mapping=None
):
    """Generator for reading a CSV file.

    Args:
        file_handle: a file-like object containing the CSV content.
        delimiter: character used as a field separator, default: ','
        mandatory_fields: list of fields that must be present in the CSV header
        headers_mapping: list of dicts containing:
                         (i) target header we want to insert [key=target],
                         (ii) sources header we want to rename/combine [key=source],
                         (iii) def. value if we add a new column [key=default_value]
    Raises:
        RuntimeError: when there are missing fields.
        DataIngestionError: when there are issues with the data ingestion.
    """
    if not mandatory_fields:
        mandatory_fields = TIMESKETCH_FIELDS

    # Ensures delimiter is a string.
    if not isinstance(delimiter, six.text_type):
        delimiter = codecs.decode(delimiter, "utf8")

    # Ensure that required headers are present
    header_reader = pandas.read_csv(file_handle, sep=delimiter, nrows=0)
    _validate_csv_fields(mandatory_fields, header_reader, headers_mapping)

    if hasattr(file_handle, "seek"):
        file_handle.seek(0)

    try:
        reader = pandas.read_csv(
            file_handle, sep=delimiter, chunksize=DEFAULT_CHUNK_SIZE
        )
        for idx, chunk in enumerate(reader):
            if headers_mapping:
                # rename columns according to the mapping
                chunk = rename_csv_headers(chunk, headers_mapping)

            # Check if the datetime field is present and not empty.
            # TODO(jaegeral): Do we really want to skip rows with empty datetime
            # we could also calculate the datetime from timestamp if present.
            skipped_rows = chunk[chunk["datetime"].isnull()]
            if not skipped_rows.empty:
                logger.warning(
                    "{0} rows skipped since they were missing datetime field "
                    "or it was empty ".format(len(skipped_rows))
                )

            try:
                # Normalize datetime to ISO 8601 format if it's not the case.
                # Lines with unrecognized datetime format will result in "NaT"
                # (not available) as its value and the event row will be
                # dropped in the next line
                chunk["datetime"] = pandas.to_datetime(
                    chunk["datetime"], errors="coerce"
                )
                num_chunk_rows = chunk.shape[0]

                chunk.dropna(subset=["datetime"], inplace=True)
                if len(chunk) < num_chunk_rows:
                    logger.warning(
                        "{0} rows dropped from Rows {1} to {2} due to invalid "
                        "datetime values".format(
                            num_chunk_rows - len(chunk),
                            idx * reader.chunksize,
                            idx * reader.chunksize + num_chunk_rows,
                        )
                    )

                chunk["datetime"] = (
                    chunk["datetime"].apply(Timestamp.isoformat).astype(str)
                )

            except ValueError:
                logger.warning(
                    "Rows {0} to {1} skipped due to malformed "
                    "datetime values ".format(
                        idx * reader.chunksize,
                        idx * reader.chunksize + chunk.shape[0],
                    )
                )
                continue

            if "tag" in chunk:
                chunk["tag"] = chunk["tag"].apply(_parse_tag_field)

            for _, row in chunk.iterrows():
                _scrub_special_tags(row)

                # Remove all NAN values from the pandas.Series.
                row.dropna(inplace=True)

                # Make sure we always have a timestamp
                if not "timestamp" in row:
                    row["timestamp"] = int(
                        pandas.Timestamp(row["datetime"]).value / 1000
                    )

                yield row.to_dict()
    except (pandas.errors.EmptyDataError, pandas.errors.ParserError) as e:
        error_string = "Unable to read file, with error: {0!s}".format(e)
        logger.error(error_string)
        raise errors.DataIngestionError(error_string) from e


def read_and_validate_redline(file_handle):
    """Generator for reading a Redline CSV file.

    Args:
        file_handle: a file-like object containing the CSV content.

    Raises:
        RuntimeError: if there are missing fields.
    """

    csv.register_dialect(
        "redlineDialect",
        delimiter=",",
        quoting=csv.QUOTE_ALL,
        skipinitialspace=True,
    )
    reader = pandas.read_csv(file_handle, delimiter=",", dialect="redlineDialect")

    _validate_csv_fields(REDLINE_FIELDS, reader)
    for row in reader:
        dt = parser.parse(row["Timestamp"])
        timestamp = int(time.mktime(dt.timetuple())) * 1000
        dt_iso_format = dt.isoformat()
        timestamp_desc = row["Field"]

        summary = row["Summary"]
        alert = row["Alert"]
        tag = row["Tag"]

        row_to_yield = {}
        row_to_yield["message"] = summary
        row_to_yield["timestamp"] = timestamp
        row_to_yield["datetime"] = dt_iso_format
        row_to_yield["timestamp_desc"] = timestamp_desc
        tags = [tag]
        row_to_yield["alert"] = alert  # Extra field
        row_to_yield["tag"] = tags  # Extra field

        yield row_to_yield


def rename_jsonl_headers(linedict, headers_mapping, lineno):
    """Rename the headers of the dictionary

    Args:
        linedict: dictionary to be modified
        headers_mapping: list of dicts containing:
                         (i) target header we want to insert [key=target],
                         (ii) sources header we want to rename/combine [key=source],
                         (iii) def. value if we add a new column [key=default_value]
        lineno: line of the JSONL file

    Returns: the dictionary with renamed headers


    """
    headers_mapping.sort(
        key=lambda x: len(x["source"]) if x["source"] else 0, reverse=True
    )
    ld_keys = linedict.keys()

    # sanity check of the headers_mapping
    check_mapping_errors(ld_keys, headers_mapping)

    for mapping in headers_mapping:
        if mapping["target"] not in ld_keys:
            if mapping["source"]:
                # mapping["source"] is not None
                if len(mapping["source"]) == 1:
                    # 1. rename header
                    if mapping["source"][0] in ld_keys:
                        linedict[mapping["target"]] = linedict.pop(mapping["source"][0])
                    else:
                        raise RuntimeError(
                            f"Source mapping {mapping['source'][0]} not found in JSON\n"
                            f"JSON line:\n{linedict}\n"
                            f"Line no: {lineno}"
                        )
                else:
                    # 2. combine headers
                    linedict[mapping["target"]] = ""
                    for source in mapping["source"]:
                        if source in ld_keys:
                            linedict[mapping["target"]] += f"{source} : "
                            linedict[mapping["target"]] += f"{linedict[source]} |"
                        else:
                            raise RuntimeError(
                                f"Source mapping {source} not found in JSON\n"
                                f"JSON line:\n{linedict}\n"
                                f"Line no: {lineno}"
                            )
            else:
                # 3. create new entry with the default value
                linedict[mapping["target"]] = mapping["default_value"]
    return linedict


def read_and_validate_jsonl(
    file_handle, delimiter=None, headers_mapping=None
):  # pylint: disable=unused-argument
    """Generator for reading a JSONL (json lines) file.

    Args:
        file_handle: a file-like object containing the CSV content.
        delimiter: not used in this function
        headers_mapping: list of dicts containing:
                         (i) target header we want to insert [key=target],
                         (ii) sources header we want to rename/combine [key=source],
                         (iii) def. value if we add a new column [key=default_value]

    Raises:
        RuntimeError: if there are missing fields.
        DataIngestionError: If the ingestion fails.

    Yields:
        A dict that's ready to add to the datastore.
    """
    # Fields that must be present in each entry of the JSONL file.
    mandatory_fields = ["message", "datetime", "timestamp_desc"]
    lineno = 0
    for line in file_handle:
        lineno += 1
        try:
            linedict = json.loads(line)
            ld_keys = linedict.keys()
            if headers_mapping:
                linedict = rename_jsonl_headers(linedict, headers_mapping, lineno)
            if "datetime" not in ld_keys and "timestamp" in ld_keys:
                epoch = int(str(linedict["timestamp"])[:10])
                dt = datetime.datetime.fromtimestamp(epoch)
                linedict["datetime"] = dt.isoformat()
            if "timestamp" not in ld_keys and "datetime" in ld_keys:
                try:
                    linedict["timestamp"] = int(
                        parser.parse(linedict["datetime"]).timestamp() * 1000000
                    )
                # TODO: REcord this somewhere else and make available to the user.
                except TypeError:
                    logger.error(
                        "Unable to parse timestamp, skipping line "
                        "{0:d}".format(lineno),
                        exc_info=True,
                    )
                    continue
                except parser.ParserError:
                    logger.error(
                        "Unable to parse timestamp, skipping line "
                        "{0:d}".format(lineno),
                        exc_info=True,
                    )
                    continue

            missing_fields = [x for x in mandatory_fields if x not in linedict]
            if missing_fields:
                raise RuntimeError(
                    f"Missing field(s) at line {lineno}: {','.join(missing_fields)}\n"
                    f"Line: {linedict}\n"
                    f"Mapping: {headers_mapping}"
                )

            if "tag" in linedict:
                linedict["tag"] = [x for x in _parse_tag_field(linedict["tag"]) if x]
            _scrub_special_tags(linedict)
            yield linedict

        except ValueError as e:
            raise errors.DataIngestionError(
                "Error parsing JSON at line {0:n}: {1:s}".format(lineno, str(e))
            )


def get_validated_indices(indices, sketch):
    """Exclude any deleted search index references.

    Args:
        indices: List of indices from the user
        sketch: A sketch object (instance of models.sketch.Sketch).

    Returns:
        Tuple of two items:
          List of indices with those removed that is not in the sketch
          List of timeline IDs that should be part of the output.
    """
    sketch_structure = {}
    for timeline in sketch.timelines:
        if timeline.get_status.status.lower() != "ready":
            continue
        index_ = timeline.searchindex.index_name
        sketch_structure.setdefault(index_, [])
        sketch_structure[index_].append(
            {
                "name": timeline.name,
                "id": timeline.id,
            }
        )

    sketch_indices = set(sketch_structure.keys())
    exclude = set(indices) - sketch_indices
    timelines = set()

    if exclude:
        indices = [index for index in indices if index not in exclude]
        for item in exclude:
            for index, timeline_list in sketch_structure.items():
                for timeline_struct in timeline_list:
                    timeline_id = timeline_struct.get("id")
                    timeline_name = timeline_struct.get("name")

                    if not timeline_id:
                        continue

                    if isinstance(item, str) and item.isdigit():
                        item = int(item)

                    if item == timeline_id:
                        timelines.add(timeline_id)
                        indices.append(index)

                    if isinstance(item, str) and item.lower() == timeline_name.lower():
                        timelines.add(timeline_id)
                        indices.append(index)

    return list(set(indices)), list(timelines)


def send_email(subject, body, to_username, use_html=False):
    """Send email using configure SMTP server.

    Args:
        subject: Email subject string.
        body: Email message body.
        to_username: User to send email to.
        use_html: Boolean indicating if the email body should be sent as html.

    Raises:
        RuntimeError if not properly configured or if the recipient user is no
        in the whitelist.
    """
    email_enabled = current_app.config.get("ENABLE_EMAIL_NOTIFICATIONS")
    email_domain = current_app.config.get("EMAIL_DOMAIN")
    email_smtp_server = current_app.config.get("EMAIL_SMTP_SERVER")
    email_from_user = current_app.config.get("EMAIL_FROM_ADDRESS", "timesketch")
    email_user_whitelist = current_app.config.get("EMAIL_USER_WHITELIST", [])
    email_login_username = current_app.config.get("EMAIL_AUTH_USERNAME")
    email_login_password = current_app.config.get("EMAIL_AUTH_PASSWORD")
    email_ssl = current_app.config.get("EMAIL_SSL")
    email_tls = current_app.config.get("EMAIL_TLS")

    if not email_enabled:
        raise RuntimeError("Email notifications are not enabled, aborting.")

    if not email_domain:
        raise RuntimeError("Email domain is not configured, aborting.")

    if not email_smtp_server:
        raise RuntimeError("Email SMTP server is not configured, aborting.")

    # Only send mail to whitelisted usernames.
    if to_username not in email_user_whitelist:
        return

    from_address = "{0:s}@{1:s}".format(email_from_user, email_domain)
    # TODO: Add email address to user object and pick it up from there.
    to_address = "{0:s}@{1:s}".format(to_username, email_domain)
    email_content_type = "text"
    if use_html:
        email_content_type = "text/html"

    msg = email.message.Message()
    msg["Subject"] = subject
    msg["From"] = from_address
    msg["To"] = to_address
    msg.add_header("Content-Type", email_content_type)
    msg.set_payload(body)

    # EMAIL_SSL in timesketch.conf must be set to True
    if email_ssl:
        smtp = smtplib.SMTP_SSL(email_smtp_server)
        if email_login_username and email_login_password:
            smtp.login(email_login_username, email_login_password)
        smtp.sendmail(msg["From"], [msg["To"]], msg.as_string())
        smtp.quit()
        return
    # EMAIL_TLS in timesketch.conf must be set to True
    if email_tls:
        smtp = smtplib.SMTP(email_smtp_server)
        smtp.ehlo()
        smtp.starttls()
        if email_login_username and email_login_password:
            smtp.login(email_login_username, email_login_password)
        smtp.sendmail(msg["From"], [msg["To"]], msg.as_string())
        smtp.quit()
        return

    # default - no SSL/TLS configured
    smtp = smtplib.SMTP(email_smtp_server)
    if email_login_username and email_login_password:
        smtp.login(email_login_username, email_login_password)
    smtp.sendmail(msg["From"], [msg["To"]], msg.as_string())
    smtp.quit()
