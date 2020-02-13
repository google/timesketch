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

import json
import math
import logging
import os
import tempfile
import uuid

import pandas
from . import timeline
from . import definitions


def format_data_frame_row(row, format_message_string):
    """Return a formatted data frame using a format string."""
    return format_message_string.format(**row)


class ImportStreamer(object):
    """Upload object used to stream results to Timesketch."""

    # The number of entries before automatically flushing
    # the streamer.
    ENTRY_THRESHOLD = 100000

    def __init__(self, entry_threshold=None):
        """Initialize the upload streamer."""
        self._count = 0
        self._data_lines = []
        self._format_string = None
        self._index = uuid.uuid4().hex
        self._last_response = None
        self._resource_url = ''
        self._sketch = None
        self._timeline_id = None
        self._timeline_name = None
        self._timestamp_desc = None

        self._threshold = entry_threshold or self.ENTRY_THRESHOLD

    def _fix_data_frame(self, data_frame):
        """Returns a data frame with added columns for Timesketch upload.

        Args:
            data_frame: a pandas data frame.

        Returns:
            A pandas data frame with added columns needed for Timesketch.
        """
        if 'message' not in data_frame:
            data_frame['message'] = data_frame.apply(
                lambda row: format_data_frame_row(
                    row, self._format_string), axis=1)

        if 'timestamp_desc' not in data_frame:
            data_frame['timestamp_desc'] = self._timestamp_desc

        if 'datetime' not in data_frame:
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
                    logging.info(
                        'Unable to convert timestamp in column: %s, error %s',
                        column, e)

            if 'timestamp' in data_frame:
                data_frame['datetime'] = data_frame['timestamp'].dt.strftime(
                    '%Y-%m-%dT%H:%M:%S%z')

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

    def _upload_data(self, file_name, end_stream):
        """Upload data to Timesketch.

        Args:
            file_name: a full path to the file that is about to be uploaded.
            end_stream: boolean indicating whether this is the last chunk of
                the stream.
        """
        files = {
            'file': open(file_name, 'rb')
        }
        data = {
            'name': self._timeline_name,
            'sketch_id': self._sketch.id,
            'enable_stream': not end_stream,
            'index_name': self._index,
        }

        response = self._sketch.api.session.post(
            self._resource_url, files=files, data=data)

        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            raise RuntimeError(
                'Error uploading data: [{0:d}] {1:s} {2:s}, file: {3:s}, '
                'index {4:s}'.format(
                    response.status_code, response.reason, response.text,
                    file_name, self._index))

        response_dict = response.json()
        self._timeline_id = response_dict.get('objects', [{}])[0].get('id')
        self._last_response = response_dict

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

        if size <= self._threshold:
            csv_file = tempfile.NamedTemporaryFile(suffix='.csv')
            data_frame_use.to_csv(csv_file.name, index=False, encoding='utf-8')
            end_stream = not part_of_iter
            self._upload_data(csv_file.name, end_stream=end_stream)
            return

        chunks = int(math.ceil(float(size) / self._threshold))
        for index in range(0, chunks):
            chunk_start = index * self._threshold
            data_chunk = data_frame_use[
                chunk_start:chunk_start + self._threshold]

            csv_file = tempfile.NamedTemporaryFile(suffix='.csv')
            data_chunk.to_csv(csv_file.name, index=False, encoding='utf-8')

            end_stream = bool(index == chunks - 1)
            self._upload_data(csv_file.name, end_stream=end_stream)

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

        if self._count >= self._threshold:
            self.flush(end_stream=False)
            self._reset()

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

        file_ending = filepath.lower().split('.')[-1]
        if file_ending == 'csv':
            for chunk_frame in pandas.read_csv(
                    filepath, delimiter=delimiter, chunksize=self._threshold):
                self.add_data_frame(chunk_frame, part_of_iter=True)
        elif file_ending == 'plaso':
            self._sketch.upload(self._timeline_name, filepath, self._index)
        elif file_ending == 'jsonl':
            with open(filepath, 'r') as fh:
                for line in fh:
                    try:
                        self.add_json(line.strip())
                    except TypeError as e:
                        logging.error('Unable to decode line: {0!s}'.format(e))
        else:
            raise TypeError(
                'File needs to have a file extension of: .csv, .jsonl or '
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
            raise TypeError('Data not as JSON, error: {0!s}'.format(e))

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

        data_frame = pandas.DataFrame(self._data_lines)
        data_frame_use = self._fix_data_frame(data_frame)

        csv_file = tempfile.NamedTemporaryFile(suffix='.csv')
        data_frame_use.to_csv(csv_file.name, index=False, encoding='utf-8')

        self._upload_data(csv_file.name, end_stream=end_stream)

    @property
    def response(self):
        """Returns the last response from an upload."""
        return self._last_response

    def set_sketch(self, sketch):
        """Set a client for the streamer.

        Args:
            sketch: an instance of Sketch that is used to communicate
                with the API to upload data.
        """
        self._sketch = sketch
        self._resource_url = '{0:s}/upload/'.format(sketch.api.api_root)

    def set_message_format_string(self, format_string):
        """Set the message format string."""
        self._format_string = format_string

    def set_timeline_name(self, name):
        """Set the timeline name."""
        self._timeline_name = name

    def set_index_name(self, index):
        """Set the index name."""
        self._index = index

    def set_timestamp_description(self, description):
        """Set the timestamp description field."""
        self._timestamp_desc = description

    @property
    def timeline(self):
        """Returns a timeline object."""
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
