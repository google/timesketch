# Copyright 2020 Google Inc. All rights reserved.
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
"""Some utility functions for the Timesketch importer."""

import datetime
import string

import six
import dateutil.parser


# When there is no defined format message string a default one is used
# that is generated using the available columns or keys in the dataset.
# This constant defines what columns or keys should be skipped while
# generating this message field.
FIELDS_TO_SKIP_IN_FORMAT_STRING = frozenset([
    'timestamp_desc', 'time', 'timestamp', 'data_type', 'datetime',
    'source_short', 'source_long', 'source'
])
# This constant defines patterns that are used to skip columns or keys
# that start with the strings defined here.
FIELDS_TO_SKIP_STARTSWITH = frozenset([
    '_',
])


def format_data_frame(dataframe, format_message_string):
    """Add a message field to a data frame using a format message string.

    Args:
        dataframe (pandas.DataFrame): the data frame containing the data.
        format_message_String (str): the format string used to generate
            a message column.
    """
    dataframe['message'] = ''

    formatter = string.Formatter()
    for literal_text, field, _, _ in formatter.parse(format_message_string):
        dataframe['message'] = dataframe['message'] + literal_text

        if field:
            dataframe['message'] = dataframe[
                'message'] + dataframe[field].astype(str)


def get_combined_message_string(dataframe=None, mydict=None):
    """Returns a message string by combining all columns from a DataFrame/dict.

    Args:
        dataframe (pandas.DataFrame): the data frame containing the data. Used
            to get column names for the message string if supplied.
        mydict (dict): if supplied the dictionary keys will be used to
            construct the message string.

    Raises:
        ValueError if neither dataframe nor a dictionary is supplied.

    Returns:
        A string that can be used as a default message string.
    """
    if dataframe is None and mydict is None:
        raise ValueError('Need to define either a dict or a DataFrame')

    if mydict:
        my_list = list(mydict.keys())
    else:
        my_list = list(dataframe.columns)

    fields_to_delete = list(set(my_list).intersection(
        FIELDS_TO_SKIP_IN_FORMAT_STRING))
    for field in fields_to_delete:
        index = my_list.index(field)
        _ = my_list.pop(index)

    for del_field in FIELDS_TO_SKIP_STARTSWITH:
        for index, field in enumerate(my_list):
            if field.startswith(del_field):
                _ = my_list.pop(index)

    string_values = [
        '[{0:s}] = {{{0:s}}}'.format(x) for x in my_list]
    return ', '.join(string_values)


def get_datestring_from_value(value):
    """Returns an empty string or a date value.

    Args:
        value (any): A string or an int/float that contains a timestamp
            value that can be parsed into a datetime.

    Returns:
        A string with the timestamp in ISO 8601 or an empty string if not
        able to parse the timestamp.
    """
    if isinstance(value, six.string_types):
        try:
            date = dateutil.parser.parse(value)
            return date.isoformat()
        except ValueError:
            pass

    if isinstance(value, (int, float)):
        try:
            date = datetime.datetime.utcfromtimestamp(value / 1e6)
            return date.isoformat()
        except ValueError:
            pass
    return ''
