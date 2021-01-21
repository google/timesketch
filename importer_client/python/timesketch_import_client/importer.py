# Copyright 2019 Google Inc. All rights reserved.
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
"""Timesketch data importer."""
from __future__ import unicode_literals

import codecs
import io
import json
import logging
import math
import os
import time
import uuid

import numpy
import pandas

from timesketch_api_client import timeline
from timesketch_api_client import definitions
from timesketch_import_client import utils

logger = logging.getLogger('timesketch_importer.importer')


class ImportStreamer(object):
    """Upload object used to stream results to Timesketch."""

    # The number of entries before automatically flushing
    # the streamer.
    DEFAULT_ENTRY_THRESHOLD = 50000

    # Number of bytes in a binary file before automatically
    # chunking it up into smaller pieces.
    DEFAULT_FILESIZE_THRESHOLD = 104857600  # 100 Mb.

    # Define default values.
    DEFAULT_TEXT_ENCODING = 'utf-8'
    DEFAULT_TIMESTAMP_DESC = 'Time Logged'

    def __init__(self):
        """Initialize the upload streamer."""
        self._count = 0
        self._config_helper = None
        self._dict_config_loaded = False
        self._csv_delimiter = None
        self._data_lines = []
        self._data_type = None
        self._datetime_field = None
        self._format_string = None
        self._index = uuid.uuid4().hex
        self._last_response = None
        self._resource_url = ''
        self._sketch = None
        self._timeline_id = None
        self._timeline_name = None

        self._chunk = 1

        self._text_encoding = self.DEFAULT_TEXT_ENCODING
        self._timestamp_desc = self.DEFAULT_TIMESTAMP_DESC
        self._threshold_entry = self.DEFAULT_ENTRY_THRESHOLD
        self._threshold_filesize = self.DEFAULT_FILESIZE_THRESHOLD

    def _fix_dict(self, my_dict):
        """Adjusts a dict with so that it can be uploaded to Timesketch.

        This function will take a dictionary and modify it. Summary of the
        changes are:
          * If "message" is not a key and a format message string has been
              defined, a message field is constructed.
          * If "datetime" is not a key, an attempt to generate it is made.
          * If "timestamp_desc" is not set but defined by the importer it
              is added.
          * All keys that start with an underscore ("_") are removed.

        Args:
            my_dict: a dictionary that may be missing few fields needed
                    for Timesketch.
        """
        if 'message' not in my_dict:
            format_string = (
                self._format_string or utils.get_combined_message_string(
                    mydict=my_dict))
            my_dict['message'] = format_string.format(**my_dict)

        _ = my_dict.setdefault('timestamp_desc', self._timestamp_desc)
        if self._data_type:
            _ = my_dict.setdefault('data_type', self._data_type)

        if 'datetime' not in my_dict:
            date = ''
            if self._datetime_field:
                value = my_dict.get(self._datetime_field)
                if value:
                    date = utils.get_datestring_from_value(value)
            if not date:
                for key in my_dict:
                    key_string = key.lower()
                    if 'time' not in key_string:
                        continue

                    if key_string == 'timestamp_desc':
                        continue

                    value = my_dict[key]
                    date = utils.get_datestring_from_value(value)
                    if date:
                        break

            if date:
                my_dict['datetime'] = date
        else:
            my_dict['datetime'] = utils.get_datestring_from_value(
                my_dict['datetime'])

        # We don't want to include any columns that start with an underscore.
        underscore_columns = [x for x in my_dict if x.startswith('_')]
        if underscore_columns:
            for column in underscore_columns:
                del my_dict[column]

    def _fix_data_frame(self, data_frame):
        """Returns a data frame with added columns for Timesketch upload.

        Args:
            data_frame: a pandas data frame.

        Returns:
            A pandas data frame with added columns needed for Timesketch.
        """
        if 'message' not in data_frame:
            format_string = (
                self._format_string or utils.get_combined_message_string(
                    dataframe=data_frame))
            utils.format_data_frame(data_frame, format_string)

        if 'timestamp_desc' not in data_frame:
            data_frame['timestamp_desc'] = self._timestamp_desc

        if self._data_type and 'data_type' not in data_frame:
            data_frame['data_type'] = self._data_type

        if 'datetime' not in data_frame:
            if self._datetime_field and self._datetime_field in data_frame:
                try:
                    data_frame['timestamp'] = pandas.to_datetime(
                        data_frame[self._datetime_field], utc=True)
                except ValueError as e:
                    logger.info(
                        'Unable to convert timestamp in column: %s, error %s',
                        self._datetime_field, e)
            else:
                for column in data_frame.columns[
                        data_frame.columns.str.contains('time', case=False)]:
                    if column.lower() == 'timestamp_desc':
                        continue
                    try:
                        data_frame['timestamp'] = pandas.to_datetime(
                            data_frame[column], utc=True)
                        # We want the first successful timestamp value.
                        break
                    except ValueError as e:
                        logger.info(
                            'Unable to convert timestamp in column: '
                            '%s, error %s', column, e)

            if 'timestamp' in data_frame:
                data_frame['datetime'] = data_frame['timestamp'].dt.strftime(
                    '%Y-%m-%dT%H:%M:%S%z')
                data_frame['timestamp'] = data_frame[
                    'timestamp'].astype(numpy.int64) / 1e9
        else:
            try:
                date = pandas.to_datetime(data_frame['datetime'], utc=True)
                data_frame['datetime'] = date.dt.strftime('%Y-%m-%dT%H:%M:%S%z')
            except Exception:  # pylint: disable=broad-except
                logger.error(
                    'Unable to change datetime, is it badly formed?',
                    exc_info=True)

        # TODO: Support labels in uploads/imports.
        if 'label' in data_frame:
            del data_frame['label']
            logger.warning(
                'Labels cannot be imported at this time. Therefore the '
                'label column was dropped from the dataset.')

        # We don't want to include any columns that start with an underscore.
        columns = list(
            data_frame.columns[~data_frame.columns.str.contains('^_')])
        return data_frame[columns]

    def _ready(self):
        """Check whether all variables have been set.

        Raises:
            ValueError: if the streamer has not yet been fully configured.
        """
        if self._sketch is None:
            raise ValueError('Sketch has not yet been set.')

    def _reset(self):
        """Reset the buffer."""
        self._count = 0
        self._data_lines = []

    def _upload_data_buffer(self, end_stream):
        """Upload data to Timesketch.

        Args:
            end_stream: boolean indicating whether this is the last chunk of
                the stream.
        """
        if not self._data_lines:
            return

        start_time = time.time()
        data = {
            'name': self._timeline_name,
            'sketch_id': self._sketch.id,
            'enable_stream': not end_stream,
            'index_name': self._index,
            'events': '\n'.join([json.dumps(x) for x in self._data_lines]),
        }
        logger.debug(
            'Data buffer ready for upload, took {0:.2f} seconds to '
            'prepare.'.format(time.time() - start_time))

        response = self._sketch.api.session.post(self._resource_url, data=data)
        # TODO: Investigate why the sleep is needed, fix the underlying issue
        # and get rid of it here.
        # To prevent unexpected errors with connection refusal adding a quick
        # sleep.
        time.sleep(2)
        # TODO: Add in the ability to re-upload failed file.
        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            raise RuntimeError(
                'Error uploading data: [{0:d}] {1!s} {2!s}, '
                'index {3:s}'.format(
                    response.status_code, response.reason, response.text,
                    self._index))

        logger.debug(
            'Data buffer nr. {0:d} uploaded, total time: {1:.2f}s'.format(
                self._chunk, time.time() - start_time))
        self._chunk += 1
        response_dict = response.json()
        self._timeline_id = response_dict.get('objects', [{}])[0].get('id')
        self._last_response = response_dict

    def _upload_data_frame(self, data_frame, end_stream):
        """Upload data to Timesketch.

        Args:
            data_frame: a pandas DataFrame with the content to upload.
            end_stream: boolean indicating whether this is the last chunk of
                the stream.
        """
        data = {
            'name': self._timeline_name,
            'sketch_id': self._sketch.id,
            'enable_stream': not end_stream,
            'index_name': self._index,
            'events': data_frame.to_json(orient='records', lines=True),
        }

        response = self._sketch.api.session.post(self._resource_url, data=data)
        self._chunk += 1
        # TODO: Add in the ability to re-upload failed file.
        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            raise RuntimeError(
                'Error uploading data: [{0:d}] {1!s} {2!s}, '
                'index {3:s}'.format(
                    response.status_code, response.reason, response.text,
                    self._index))

        response_dict = response.json()
        self._timeline_id = response_dict.get('objects', [{}])[0].get('id')
        self._last_response = response_dict

    def _upload_binary_file(self, file_path):
        """Upload binary data to Timesketch, potentially chunking it up.

        Args:
            file_path: a full path to the file that is about to be uploaded.
        """
        file_size = os.path.getsize(file_path)

        if self._timeline_name:
            timeline_name = self._timeline_name
        else:
            file_name = os.path.basename(file_path)
            file_name_no_ext, _, _ = file_name.rpartition('.')
            timeline_name = file_name_no_ext

        data = {
            'name': timeline_name,
            'sketch_id': self._sketch.id,
            'total_file_size': file_size,
            'index_name': self._index,
        }
        if file_size <= self._threshold_filesize:
            file_dict = {
                'file': open(file_path, 'rb')}
            response = self._sketch.api.session.post(
                self._resource_url, files=file_dict, data=data)
        else:
            chunks = int(
                math.ceil(float(file_size) / self._threshold_filesize))
            data['chunk_total_chunks'] = chunks
            for index in range(0, chunks):
                data['chunk_index'] = index
                start = self._threshold_filesize * index
                data['chunk_byte_offset'] = start
                fh = open(file_path, 'rb')
                fh.seek(start)
                binary_data = fh.read(self._threshold_filesize)
                file_stream = io.BytesIO(binary_data)
                file_stream.name = file_path
                file_dict = {'file': file_stream}
                response = self._sketch.api.session.post(
                    self._resource_url, files=file_dict, data=data)

                if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
                    # TODO (kiddi): Re-do this chunk.
                    raise RuntimeError(
                        'Error uploading data chunk: {0:d}/{1:d}. Status code: '
                        '{2:d} - {3!s} {4!s}'.format(
                            index, chunks, response.status_code,
                            response.reason, response.text))

        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            raise RuntimeError(
                'Error uploading data: [{0:d}] {1!s} {2!s}, file: {3:s}, '
                'index {4:s}'.format(
                    response.status_code, response.reason, response.text,
                    file_path, self._index))

        response_dict = response.json()
        self._last_response = response_dict
        self._timeline_id = response_dict.get('objects', [{}])[0].get('id')

    def add_data_frame(self, data_frame, part_of_iter=False):
        """Add a data frame into the buffer.

        Args:
              data_frame: a pandas data frame object to add to the buffer.
              part_of_iter: if it is expected that this function is called
                  as part of an iterator, or that many data frames may be
                  added to the importer set to True, defaults to False.

        Raises:
              ValueError: if the data frame does not contain the correct
                  columns for Timesketch upload.
        """
        self._ready()

        if not isinstance(data_frame, pandas.DataFrame):
            raise TypeError('Entry object needs to be a DataFrame')

        size = data_frame.shape[0]

        if self._config_helper:
            data_type = ''
            if 'data_type' in data_frame:
                data_types = data_frame.data_type.unique()
                if len(data_types) == 1:
                    data_type = data_types[0]

            df_columns = list(data_frame.columns)
            self._config_helper.configure_streamer(
                self, data_type=data_type, columns=df_columns)

        data_frame_use = self._fix_data_frame(data_frame)

        if 'datetime' not in data_frame_use:
            raise ValueError(
                'Need a field called datetime in the data frame that is '
                'formatted according using this format string: '
                '%Y-%m-%dT%H:%M:%S%z. If that is not provided the data frame '
                'needs to have a column that has the word "time" in it, '
                'that can be used to conver to a datetime field.')

        if 'message' not in data_frame_use:
            raise ValueError(
                'Need a field called message in the data frame, use the '
                'formatting string to generate one automatically.')

        if 'timestamp_desc' not in data_frame_use:
            raise ValueError(
                'Need a field called timestamp_desc in the data frame.')

        if size <= self._threshold_entry:
            end_stream = not part_of_iter
            self._upload_data_frame(data_frame_use, end_stream=end_stream)
            return

        chunks = int(math.ceil(float(size) / self._threshold_entry))
        for index in range(0, chunks):
            chunk_start = index * self._threshold_entry
            data_chunk = data_frame_use[
                chunk_start:chunk_start + self._threshold_entry]
            end_stream = bool(index == chunks - 1)
            self._upload_data_frame(data_chunk, end_stream=end_stream)

    def add_dict(self, entry):
        """Add an entry into the buffer.

        Args:
            entry: a dict object to add to the buffer.

        Raises:
            TypeError: if the entry is not a dict.
        """
        self._ready()
        if not isinstance(entry, dict):
            raise TypeError('Entry object needs to be a dict.')

        if self._count >= self._threshold_entry:
            self.flush(end_stream=False)
            self._reset()

        if self._config_helper and not self._dict_config_loaded:
            data_type = entry.get('data_type', '')
            columns = entry.keys()
            self._config_helper.configure_streamer(
                self, data_type=data_type, columns=columns)
            self._dict_config_loaded = True

        # Changing the dictionary to add fields, such as timestamp description,
        # message field, etc. See function docstring for further details.
        self._fix_dict(entry)
        self._data_lines.append(entry)
        self._count += 1

    def add_excel_file(self, filepath, **kwargs):
        """Add a Microsoft Excel sheet to importer.

        Args:
            filepath: full file path to a XLS or XLSX file to add to the
                importer.
            kwargs:
                Other parameters can be passed in that match the
                pandas.read_excel parameters. Including:

                sheet_name: str, int, list, or None, default 0. Strings are
                    used for sheet names. Integers are used in zero-indexed
                    sheet positions. Lists of strings/integers are used to
                    request multiple sheets. Specify None to get all sheets.
                header : int, list of int, default 0
                    Row (0-indexed) to use for the column labels of the
                    parsed DataFrame. If a list of integers is passed those
                    row positions wil be combined into a ``MultiIndex``. Use
                    None if there is no header.
                names : array-like, default None
                    List of column names to use. If file contains no header
                    row then you should explicitly pass header=None.
                index_col : int, list of int, default None
                    Column (0-indexed) to use as the row labels of the
                    DataFrame. Pass None if there is no such column. If a list
                    is passed, those columns will be combined into a
                    ``MultiIndex``. If a subset of data is selected with
                    ``usecols``, index_col is based on the subset.

        Raises:
            TypeError: if the entry is not an Excel sheet.
        """
        self._ready()
        if not os.path.isfile(filepath):
            raise TypeError('File path is not a real file.')

        file_ending = filepath.lower().split('.')[-1]
        if file_ending not in ['xls', 'xlsx']:
            raise TypeError('File name needs to end with xls or xlsx')

        data_frame = pandas.read_excel(filepath, **kwargs)
        if data_frame.empty:
            raise TypeError('Not able to read any rows from sheet.')

        self.add_data_frame(data_frame)

    def add_file(self, filepath, delimiter=','):
        """Add a CSV, JSONL or a PLASO file to the buffer.

        Args:
            filepath: the path to the file to add.
            delimiter: if this is a CSV file then a delimiter can be defined.

        Raises:
            TypeError: if the entry does not fulfill requirements.
        """
        self._ready()

        if not os.path.isfile(filepath):
            raise TypeError('Entry object needs to be a file that exists.')

        if not self._timeline_name:
            base_path = os.path.basename(filepath)
            default_timeline_name, _, _ = base_path.rpartition('.')
            self.set_timeline_name(default_timeline_name)

        file_ending = filepath.lower().split('.')[-1]
        if file_ending == 'csv':
            if self._csv_delimiter:
                delimiter = self._csv_delimiter

            with codecs.open(
                    filepath, 'r', encoding=self._text_encoding,
                    errors='replace') as fh:
                for chunk_frame in pandas.read_csv(
                        fh, delimiter=delimiter,
                        chunksize=self._threshold_entry):
                    self.add_data_frame(chunk_frame, part_of_iter=True)
        elif file_ending == 'plaso':
            self._upload_binary_file(filepath)

        elif file_ending == 'jsonl':
            with codecs.open(
                    filepath, 'r', encoding=self._text_encoding,
                    errors='replace') as fh:
                for line in fh:
                    try:
                        self.add_json(line.strip())
                    except TypeError as e:
                        logger.error('Unable to decode line: {0!s}'.format(e))

        else:
            raise TypeError(
                'File needs to have a file extension of: .csv, .jsonl, mans or '
                '.plaso')

    def add_json(self, json_entry, column_names=None):
        """Add an entry that is in a JSON format.

        Args:
            json_entry: a single entry encoded in JSON.
            column_names: a list of column names if the JSON object
                is a list as an opposed to a dict.

        Raises:
            TypeError: if the entry is not JSON or in the wrong JSON format.
        """
        try:
            json_obj = json.loads(json_entry)
        except json.JSONDecodeError as e:
            raise TypeError('Data not as JSON, error: {0!s}'.format(e)) from e

        json_dict = {}
        if isinstance(json_obj, (list, tuple)):
            if not column_names:
                raise TypeError(
                    'Data is a list, but there are no defined column names.')
            if not len(json_obj) != len(column_names):
                raise TypeError(
                    'The number of columns ({0:d}) does not match the number '
                    'of columns in the JSON list ({1:d})'.format(
                        len(column_names), len(json_obj)))
            json_dict = dict(zip(column_names, json_obj))
        elif isinstance(json_obj, dict):
            json_dict = json_obj
        else:
            raise TypeError(
                'The JSON object needs to be either a dict or a list with '
                'defined column names.')

        self.add_dict(json_dict)

    def close(self):
        """Close the streamer."""
        try:
            self._ready()
        except ValueError:
            return

        if self._data_lines:
            self.flush(end_stream=True)

        # Trigger auto analyzer pipeline to kick in.
        pipe_resource = '{0:s}/sketches/{1:d}/analyzer/'.format(
            self._sketch.api.api_root, self._sketch.id)
        data = {
            'index_name': self._index
        }
        _ = self._sketch.api.session.post(pipe_resource, json=data)

    def flush(self, end_stream=True):
        """Flushes the buffer and uploads to timesketch.

        Args:
            end_stream: boolean that determines whether this is the final
                data to be flushed or whether there is more to come.

        Raises:
            ValueError: if the stream object is not fully configured.
            RuntimeError: if the stream was not uploaded.
        """
        if not self._data_lines:
            return

        self._ready()
        self._upload_data_buffer(end_stream=end_stream)

    @property
    def response(self):
        """Returns the last response from an upload."""
        return self._last_response

    def set_csv_delimiter(self, delimiter):
        """Set the CSV delimiter for CSV file parsing."""
        self._csv_delimiter = delimiter

    def set_data_type(self, data_type):
        """Sets the column where the data_type is defined in."""
        self._data_type = data_type

    def set_datetime_column(self, column):
        """Sets the column where the timestamp is defined in."""
        self._datetime_field = column

    def set_entry_threshold(self, threshold):
        """Set the threshold for number of entries per chunk."""
        self._threshold_entry = threshold

    def set_filesize_threshold(self, threshold):
        """Set the threshold for file size per chunk."""
        self._threshold_filesize = threshold

    def set_config_helper(self, helper):
        """Set the config helper object."""
        self._config_helper = helper

    def set_index_name(self, index):
        """Set the index name."""
        self._index = index

    def set_message_format_string(self, format_string):
        """Set the message format string."""
        self._format_string = format_string

    def set_sketch(self, sketch):
        """Set a client for the streamer.

        Args:
            sketch: an instance of Sketch that is used to communicate
                with the API to upload data.
        """
        self._sketch = sketch
        self._resource_url = '{0:s}/upload/'.format(sketch.api.api_root)

    def set_text_encoding(self, encoding):
        """Set the default encoding for reading text files."""
        self._text_encoding = encoding

    def set_timeline_name(self, name):
        """Set the timeline name."""
        self._timeline_name = name

    def set_timestamp_description(self, description):
        """Set the timestamp description field."""
        self._timestamp_desc = description

    @property
    def timeline(self):
        """Returns a timeline object."""
        if not self._timeline_id:
            logger.warning('No timeline ID has been stored as of yet.')
            return None

        timeline_obj = timeline.Timeline(
            timeline_id=self._timeline_id,
            sketch_id=self._sketch.id,
            api=self._sketch.api,
            name=self._timeline_name,
            searchindex=self._index)
        return timeline_obj

    def __enter__(self):
        """Make it possible to use "with" statement."""
        self._reset()
        return self

    # pylint: disable=unused-argument
    def __exit__(self, exception_type, exception_value, traceback):
        """Make it possible to use "with" statement."""
        self.close()
