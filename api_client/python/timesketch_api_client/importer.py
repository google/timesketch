# Copyright 2017 Google Inc. All rights reserved.
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

import os
import tempfile
import uuid

import pandas
from .definitions import HTTP_STATUS_CODE_20X


def format_data_frame_row(row, format_message_string):
    """Return a formatted data frame using a format string."""
    return format_message_string.format(**row)


class UploadStreamer(object):
    """Upload object used to stream results to Timesketch."""

    # The number of entries before automatically flushing
    # the streamer.
    ENTRY_THRESHOLD = 10000

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

        if entry_threshold:
            self._threshold = entry_threshold
        else:
            self._threshold = self.ENTRY_THRESHOLD

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
                except ValueError:
                    pass
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
        if self._format_string is None:
            raise ValueError('Format string has not yet been set.')

        if self._sketch is None:
            raise ValueError('Sketch has not yet been set.')

        if self._timestamp_desc is None:
            raise ValueError('Timestamp description has not yet been set.')

    def _reset(self):
        """Reset the buffer."""
        self._count = 0
        self._data_lines = []

    def _upload_data(self, file_name, end_stream):
        """Upload data TODO ADD DOCSTRING."""
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

        if response.status_code not in HTTP_STATUS_CODE_20X:
            raise RuntimeError(
                'Error uploading data: [{0:d}] {1:s} {2:s}, file: {3:s}, '
                'index {4:s}'.format(
                    response.status_code, response.reason, response.text,
                    file_name, self._index))

        response_dict = response.json()
        self._timeline_id = response_dict.get('objects', [{}])[0].get('id')
        self._last_response = response_dict

    def add_data_frame(self, data_frame):
        """Add a data frame into the buffer.

        Args:
              data_frame: a pandas data frame object to add to the buffer.

        Raises:
              ValueError: if the data frame does not contain the correct
                  columns for Timesketch upload.
        """
        self._ready()

        if not isinstance(data_frame, pandas.DataFrame):
            raise TypeError('Entry object needs to be a DataFrame')

        size = data_frame.shape[0]
        data_frame_use = self._fix_data_frame(data_frame)

        if not 'datetime' in data_frame_use:
            raise ValueError(
                'Need a field called datetime in the data frame that is '
                'formatted according using this format string: '
                '%Y-%m-%dT%H:%M:%S%z. If that is not provided the data frame '
                'needs to have a column that has the word "time" in it, '
                'that can be used to conver to a datetime field.')

        if not 'message' in data_frame_use:
            raise ValueError(
                'Need a field called message in the data frame, use the '
                'formatting string to generate one automatically.')

        if not 'timestamp_desc' in data_frame_use:
            raise ValueError(
                'Need a field called timestamp_desc in the data frame.')

        if size < self._threshold:
            csv_file = tempfile.NamedTemporaryFile(suffix='.csv')
            data_frame_use.to_csv(csv_file.name, index=False, encoding='utf-8')
            self._upload_data(csv_file.name, end_stream=True)
            return

        chunks = int(size / self._threshold)
        for index in range(0, chunks):
            chunk_start = index * chunks
            data_chunk = data_frame_use[
                chunk_start:chunk_start + self._threshold]

            csv_file = tempfile.NamedTemporaryFile(suffix='.csv')
            data_chunk.to_csv(csv_file.name, index=False, encoding='utf-8')

            end_stream = bool(index == chunks - 1)
            self._upload_data(csv_file.name, end_stream=end_stream)

    def add_file(self, filepath):
        """Add a CSV, JSONL or a PLASO file to the buffer."""
        self._ready()

        if not os.path.isfile(filepath):
            raise TypeError('Entry object needs to be a file that exists.')
        # TODO: implement.

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

    def set_timestamp_description(self, description):
        """Set the timestamp description field."""
        self._timestamp_desc = description

    @property
    def timeline(self):
        """Returns a timeline object."""
        timeline_obj = Timeline(
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
        self.flush(end_stream=True)

        try:
            self._ready()
        except ValueError:
            return

        pipe_resource = '{0:s}/sketches/{1:d}/analyzer/auto_run/'.format(
            self._sketch.api.api_root, self._sketch.id)
        data = {
            'index_name': self._index
        }
        _ = self._sketch.api.session.post(pipe_resource, data=data)
