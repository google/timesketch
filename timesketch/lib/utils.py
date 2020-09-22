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
import sys
import time
import codecs
import six

from dateutil import parser
from flask import current_app

from timesketch.lib import errors

logger = logging.getLogger('timesketch.utils')

# Set CSV field size limit to systems max value.
csv.field_size_limit(sys.maxsize)

# Fields to scrub from timelines.
FIELDS_TO_REMOVE = ['_id', '_type', '_index', '_source']


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
    return '{0:02X}{1:02X}{2:02X}'.format(rgb[0], rgb[1], rgb[2])


def _parse_tag_field(row):
    """Reading in a tag field and converting to a list of strings."""
    if isinstance(row, (list, tuple)):
        return row

    if not isinstance(row, str):
        row = str(row)

    if row.startswith('[') and row.endswith(']'):
        return json.loads(row)

    if row == '-':
        return []

    if ',' in row:
        return row.split(',')

    return [row]


def _scrub_special_tags(dict_obj):
    """Remove Elastic specific fields from a dict."""
    for field in FIELDS_TO_REMOVE:
        if field in dict_obj:
            _ = dict_obj.pop(field)


def read_and_validate_csv(file_handle, delimiter=','):
    """Generator for reading a CSV file.

    Args:
        file_handle: a file-like object containing the CSV content.
        delimiter: character used as a field separator, default: ','

    Raises:
        RuntimeError: when there are missing fields.
        DataIngestionError: when there are issues with the data ingestion.
    """
    # Columns that must be present in the CSV file.
    mandatory_fields = ['message', 'datetime', 'timestamp_desc']

    # Ensures delimiter is a string.
    if not isinstance(delimiter, six.text_type):
        delimiter = codecs.decode(delimiter, 'utf8')

    # Due to issues with python2.
    if six.PY2:
        delimiter = str(delimiter)

    reader = csv.DictReader(file_handle, delimiter=delimiter)
    csv_header = reader.fieldnames
    missing_fields = []
    # Validate the CSV header
    for field in mandatory_fields:
        if field not in csv_header:
            missing_fields.append(field)
    if missing_fields:
        raise RuntimeError(
            'Missing fields in CSV header: {0:s}'.format(
                ','.join(missing_fields)))
    try:
        for row in reader:
            # There is a condition in which the CSV reader can read a
            # single lines as multiple, causing issues with importing.
            # TODO: Swap the CSV library for the user of pandas.
            if not row:
                continue
            if not row['datetime']:
                logger.warning(
                    'Row missing a datetime object, skipping [{0:s}]'.format(
                        ','.join([str(x).replace(
                            '\n', '').strip() for x in row.values()])))
                continue
            try:
                # normalize datetime to ISO 8601 format if it's not the case.
                parsed_datetime = parser.parse(row['datetime'])
                row['datetime'] = parsed_datetime.isoformat()

                normalized_timestamp = int(
                    time.mktime(parsed_datetime.utctimetuple()) * 1000000)
                normalized_timestamp += parsed_datetime.microsecond
                row['timestamp'] = str(normalized_timestamp)
                if 'tag' in row:
                    row['tag'] = [x for x in _parse_tag_field(row['tag']) if x]

                _scrub_special_tags(row)
            except ValueError:
                continue

            yield row
    except csv.Error as e:
        error_string = 'Unable to read file, with error: {0!s}'.format(e)
        logger.error(error_string)
        raise errors.DataIngestionError(error_string)


def read_and_validate_redline(file_handle):
    """Generator for reading a Redline CSV file.
    Args:
        file_handle: a file-like object containing the CSV content.
    """
    # Columns that must be present in the CSV file
    mandatory_fields = ['Alert', 'Tag', 'Timestamp', 'Field', 'Summary']

    csv.register_dialect(
        'myDialect', delimiter=',', quoting=csv.QUOTE_ALL,
        skipinitialspace=True)
    reader = csv.DictReader(file_handle, delimiter=',', dialect='myDialect')

    csv_header = reader.fieldnames
    missing_fields = []
    # Validate the CSV header
    for field in mandatory_fields:
        if field not in csv_header:
            missing_fields.append(field)
    if missing_fields:
        raise RuntimeError(
            'Missing fields in CSV header: {0:s}'.format(missing_fields))
    for row in reader:
        dt = parser.parse(row['Timestamp'])
        timestamp = int(time.mktime(dt.timetuple())) * 1000
        dt_iso_format = dt.isoformat()
        timestamp_desc = row['Field']

        summary = row['Summary']
        alert = row['Alert']
        tag = row['Tag']

        row_to_yield = {}
        row_to_yield["message"] = summary
        row_to_yield["timestamp"] = timestamp
        row_to_yield["datetime"] = dt_iso_format
        row_to_yield["timestamp_desc"] = timestamp_desc
        row_to_yield["alert"] = alert #extra field
        tags = [tag]
        row_to_yield["tag"] = tags # extra field

        yield row_to_yield


def read_and_validate_jsonl(file_handle):
    """Generator for reading a JSONL (json lines) file.

    Args:
        file_handle: a file-like object containing the CSV content.

    Raises:
        RuntimeError: if there are missing fields.
        DataIngestionError: If the ingestion fails.

    Yields:
        A dict that's ready to add to the datastore.
    """
    # Fields that must be present in each entry of the JSONL file.
    mandatory_fields = ['message', 'datetime', 'timestamp_desc']
    lineno = 0
    for line in file_handle:
        lineno += 1
        try:
            linedict = json.loads(line)
            ld_keys = linedict.keys()
            if 'datetime' not in ld_keys and 'timestamp' in ld_keys:
                epoch = int(str(linedict['timestamp'])[:10])
                dt = datetime.datetime.fromtimestamp(epoch)
                linedict['datetime'] = dt.isoformat()
            if 'timestamp' not in ld_keys and 'datetime' in ld_keys:
                linedict['timestamp'] = parser.parse(linedict['datetime'])

            missing_fields = [x for x in mandatory_fields if x not in linedict]
            if missing_fields:
                raise RuntimeError(
                    'Missing field(s) at line {0:n}: {1:s}'.format(
                        lineno, ','.join(missing_fields)))

            if 'tag' in linedict:
                linedict['tag'] = [
                    x for x in _parse_tag_field(linedict['tag']) if x]
            _scrub_special_tags(linedict)
            yield linedict

        except ValueError as e:
            raise errors.DataIngestionError(
                'Error parsing JSON at line {0:n}: {1:s}'.format(lineno, e))


def get_validated_indices(indices, sketch_indices):
    """Exclude any deleted search index references.

    Args:
        indices: List of indices from the user
        sketch_indices: List of indices in the sketch

    Returns:
        Set of indices with those removed that is not in the sketch
    """
    exclude = set(indices) - set(sketch_indices)
    if exclude:
        indices = [index for index in indices if index not in exclude]

    return indices


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
    email_enabled = current_app.config.get('ENABLE_EMAIL_NOTIFICATIONS')
    email_domain = current_app.config.get('EMAIL_DOMAIN')
    email_smtp_server = current_app.config.get('EMAIL_SMTP_SERVER')
    email_from_user = current_app.config.get('EMAIL_FROM_ADDRESS', 'timesketch')
    email_user_whitelist = current_app.config.get('EMAIL_USER_WHITELIST', [])

    if not email_enabled:
        raise RuntimeError('Email notifications are not enabled, aborting.')

    if not email_domain:
        raise RuntimeError('Email domain is not configured, aborting.')

    if not email_smtp_server:
        raise RuntimeError('Email SMTP server is not configured, aborting.')

    # Only send mail to whitelisted usernames.
    if to_username not in email_user_whitelist:
        return

    from_address = '{0:s}@{1:s}'.format(email_from_user, email_domain)
    # TODO: Add email address to user object and pick it up from there.
    to_address = '{0:s}@{1:s}'.format(to_username, email_domain)
    email_content_type = 'text'
    if use_html:
        email_content_type = 'text/html'

    msg = email.message.Message()
    msg['Subject'] = subject
    msg['From'] = from_address
    msg['To'] = to_address
    msg.add_header('Content-Type', email_content_type)
    msg.set_payload(body)

    smtp = smtplib.SMTP(email_smtp_server)
    smtp.sendmail(msg['From'], [msg['To']], msg.as_string())
    smtp.quit()
