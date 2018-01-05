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


def read_and_validate_csv(path):
    """Generator for reading a CSV file.

    Args:
        path: Path to the CSV file
    """
    # Columns that must be present in the CSV file
    mandatory_fields = [u'message', u'datetime', u'timestamp_desc']

    with open(path, 'rb') as fh:

        reader = csv.DictReader(fh)
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


def read_and_validate_jsonl(path):
    """Generator for reading a JSONL (json lines) file.

    Args:
        path: Path to the JSONL file
    """
    # Fields that must be present in each entry of the JSONL file.
    # We normally require datetime here, but plaso jsonl only has timestamp
    # need to learn if this is necessary or can be changed
    mandatory_fields = [u'message', u'timestamp', u'timestamp_desc']

    with open(path, 'rb') as fh:

        lineno = 0
        for line in fh:
            lineno += 1
            try:
                linedict = json.loads(line)
                missing_fields = []
                for field in mandatory_fields:
                    if field not in linedict.keys():
                        missing_fields.append(field)
                if missing_fields:
                    raise RuntimeError(
                        u"Missing fields in JSON at line {0:n}: {1:s}"
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
