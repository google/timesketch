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

import colorsys
import csv
import datetime
import json
import random
import time

from dateutil import parser


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
    return u'{0:02X}{1:02X}{2:02X}'.format(rgb[0], rgb[1], rgb[2])

# to avoid hickups in timesketch, some newlines, commas etc will be removed
def clean_summary(argument):
    argument = argument.replace('\n', '')
    argument = argument.replace(',', '.') # otherwise timesketch will be confused
    argument = argument.replace('\t', '')
    return argument


# method to create the datetime
def convert_date_to_datetime(argument):
    argument = argument.replace('Z', '')
    d = datetime.datetime.strptime(argument, '%Y-%m-%d %H:%M:%S')
    iso_date = d.isoformat()
    iso_date_new = iso_date + "+00:00"
    return  iso_date_new

# helper to create the timestamp
def convert_date_to_timestamp(argument):
    argument = argument.replace('Z', '')
    d = datetime.datetime.strptime(argument, '%Y-%m-%d %H:%M:%S')
    unixtime = time.mktime(d.timetuple())
    unix_print = int(unixtime)
    unix_print = unix_print*1000
    return unix_print

def read_and_validate_csv(path, delimiter):
    """Generator for reading a CSV or TSV file.

    Args:
        path: Path to the file
        delimiter: character used as a field separator
    """
    # Columns that must be present in the CSV file
    mandatory_fields = [u'message', u'datetime', u'timestamp_desc']

    with open(path, 'rb') as fh:

        reader = csv.DictReader(fh, delimiter=delimiter.decode('string_escape'))
        csv_header = reader.fieldnames
        missing_fields = []
        # Validate the CSV header
        for field in mandatory_fields:
            if field not in csv_header:
                missing_fields.append(field)
        if missing_fields:
            raise RuntimeError(
                u'Missing fields in CSV header: {0:s}'.format(missing_fields))
        for row in reader:
            if u'timestamp' not in csv_header and u'datetime' in csv_header:
                try:
                    parsed_datetime = parser.parse(row[u'datetime'])
                    row[u'timestamp'] = str(
                        int(time.mktime(parsed_datetime.timetuple())))
                except ValueError:
                    continue

            yield row

def read_and_validate_redline(path):
    """Generator for reading a Redline CSV file.
    Args:
        path: Path to the file
        delimiter: character used as a field separator
    """
    # Columns that must be present in the CSV file

    # check if it is the right redline format
    mandatory_fields = [u'Alert', u'Tag', u'Timestamp', u'Field', u'Summary']

    with open(path, 'rb') as fh:
        csv.register_dialect('myDialect',
                             delimiter=',',
                             quoting=csv.QUOTE_ALL,
                             skipinitialspace=True)
        reader = csv.DictReader(fh, delimiter=',', dialect='myDialect')

        csv_header = reader.fieldnames
        missing_fields = []
        # Validate the CSV header
        for field in mandatory_fields:
            if field not in csv_header:
                missing_fields.append(field)
        if missing_fields:
            raise RuntimeError(
                u'Missing fields in CSV header: {0:s}'.format(missing_fields))
        for row in reader:

            entry_unix_timestamp = convert_date_to_timestamp(row['Timestamp'])
            entry_timestamp = convert_date_to_datetime(row['Timestamp'])
            timestamp_desc = row['Field']
            summary = clean_summary(row['Summary'])
            alert = row['Alert']
            tag = row['Tag']

            row_to_yield = {}

            row_to_yield["message"] = summary
            row_to_yield["timestamp"] = str(entry_unix_timestamp)
            row_to_yield["datetime"] = entry_timestamp
            row_to_yield["timestamp_desc"] = timestamp_desc
            row_to_yield["alert"] = alert #extra field
            row_to_yield["tag"] = tag # extra field

            yield row_to_yield

def read_and_validate_jsonl(path, _):
    """Generator for reading a JSONL (json lines) file.

    Args:
        path: Path to the JSONL file
    """
    # Fields that must be present in each entry of the JSONL file.
    mandatory_fields = [u'message', u'datetime', u'timestamp_desc']
    with open(path, 'rb') as fh:

        lineno = 0
        for line in fh:
            lineno += 1
            try:
                linedict = json.loads(line)
                ld_keys = linedict.keys()
                if u'datetime' not in ld_keys and u'timestamp' in ld_keys:
                    epoch = int(str(linedict[u'timestamp'])[:10])
                    dt = datetime.datetime.fromtimestamp(epoch)
                    linedict[u'datetime'] = dt.isoformat()
                if u'timestamp' not in ld_keys and u'datetime' in ld_keys:
                    linedict[u'timestamp'] = parser.parse(linedict[u'datetime'])

                missing_fields = []
                for field in mandatory_fields:
                    if field not in linedict.keys():
                        missing_fields.append(field)
                if missing_fields:
                    raise RuntimeError(
                        u"Missing field(s) at line {0:n}: {1:s}"
                        .format(lineno, missing_fields))

                yield linedict

            except ValueError as e:
                raise RuntimeError(
                    u"Error parsing JSON at line {0:n}: {1:s}"
                    .format(lineno, e))


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
