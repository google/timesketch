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
"""Tests for the Timesketch importer."""
from __future__ import unicode_literals

import json
import unittest

import mock
import pandas
from timesketch_api_client.error import UnableToRunAnalyzer

from . import importer


class MockSketch(object):
    """Mock sketch object."""

    def __init__(self):
        self.api = mock.Mock()
        self.api.api_root = "foo_root"
        self.id = 1


class MockStreamer(importer.ImportStreamer):
    """Mock the import streamer."""

    def __init__(self):
        super().__init__()
        self.lines = []

    @property
    def columns(self):
        columns = set()
        for line in self.lines:
            columns.update(line.keys())
        return list(columns)

    def _upload_data_buffer(self, end_stream, retry_count=0):
        self.lines.extend(self._data_lines)

    def _upload_data_frame(self, data_frame, end_stream, retry_count=0):
        self.lines.extend(json.loads(data_frame.to_json(orient="records")))

    def close(self):
        pass


class TimesketchImporterTest(unittest.TestCase):
    """Test Timesketch importer."""

    def setUp(self):
        """Set up the test data frame."""
        self.lines = []

        dict_one = {
            "timestamp": "2019-02-23T12:51:52",
            "stuff": "from bar to foobar",
            "correct": False,
            "random_number": 13245,
            "vital_stats": "gangverk",
        }
        self.lines.append(dict_one)

        dict_two = {
            "timestamp": "2019-06-17T20:11:23",
            "stuff": "fra sjalfstaedi til sjalfstaedis",
            "correct": True,
            "random_number": 52,
            "vital_stats": "stolt",
        }
        self.lines.append(dict_two)

        dict_three = {
            "timestamp": "2019-01-03T02:39:42",
            "stuff": "stordagur",
            "correct": True,
            "random_number": 59913,
            "vital_stats": "elli",
        }
        self.lines.append(dict_three)

        dict_four = {
            "timestamp": "2019-12-23T23:00:03",
            "stuff": "sidasti sens ad kaupa gjof",
            "correct": True,
            "random_number": 5231134324,
            "vital_stats": "stress",
        }
        self.lines.append(dict_four)

        dict_five = {
            "timestamp": "2019-10-31T17:12:44",
            "stuff": "hraeda hraedur",
            "correct": True,
            "random_number": 420,
            "vital_stats": "grasker",
        }
        self.lines.append(dict_five)

        self.frame = pandas.DataFrame(self.lines)

        self._importer = importer.ImportStreamer()

    def test_adding_data_frames(self):
        """Test adding a data frame to the importer."""
        with MockStreamer() as streamer:
            streamer.set_sketch(MockSketch())
            streamer.set_timestamp_description("Log Entries")
            streamer.set_timeline_name("Test Entries")
            streamer.set_message_format_string(
                "{stuff:s} -> {correct!s} [{random_number:d}]"
            )

            streamer.add_data_frame(self.frame)
            self._run_all_tests(streamer.columns, streamer.lines)
            self.assertEqual(len(streamer.lines), 5)

        # Test by splitting up the dataset into chunks.
        lines = None
        columns = None
        with MockStreamer() as streamer:
            streamer.set_sketch(MockSketch())
            streamer.set_timestamp_description("Log Entries")
            streamer.set_timeline_name("Test Entries")
            streamer.set_entry_threshold(2)
            streamer.set_message_format_string(
                "{stuff:s} -> {correct!s} [{random_number:d}]"
            )

            streamer.add_data_frame(self.frame)
            lines = streamer.lines
            columns = streamer.columns
        self._run_all_tests(columns, lines)
        self.assertEqual(len(lines), 5)

    def test_adding_dict(self):
        """Test adding a dict to the importer."""
        with MockStreamer() as streamer:
            streamer.set_sketch(MockSketch())
            streamer.set_timestamp_description("Log Entries")
            streamer.set_timeline_name("Test Entries")
            streamer.set_message_format_string(
                "{stuff:s} -> {correct!s} [{random_number:d}]"
            )

            for entry in self.lines:
                streamer.add_dict(entry)

            streamer.flush()
            self._run_all_tests(streamer.columns, streamer.lines)

    def test_adding_json(self):
        """Test adding a JSON to the importer."""
        with MockStreamer() as streamer:
            streamer.set_sketch(MockSketch())
            streamer.set_timestamp_description("Log Entries")
            streamer.set_timeline_name("Test Entries")
            streamer.set_message_format_string(
                "{stuff:s} -> {correct!s} [{random_number:d}]"
            )

            for entry in self.lines:
                json_string = json.dumps(entry)
                streamer.add_json(json_string)

            streamer.flush()
            self._run_all_tests(streamer.columns, streamer.lines)

    def test_fix_data_frame(self):
        """Test fixing a data frame.
        create a pandas dataframe with timestamp, datetime, message and data_type
        columns and check some basics that the method is actually working.
        """

        data_frame = pandas.DataFrame(
            {
                "timestamp": ["1435789661000000"],
                "stuff": ["foobar"],
                "correct": [True],
                "random_number": [11332],
                "vital_stats": ["ille"],
                "datetime": ["2019-01-03T02:39:42"],
            }
        )
        fixed_frame = self._importer._fix_data_frame(data_frame)
        self.assertIsNotNone(fixed_frame)

        self.assertIs("ille" in fixed_frame["vital_stats"].values, True)
        print(fixed_frame["datetime"].values)
        self.assertIs(
            "2019-01-03T02:39:42+0000" in fixed_frame["datetime"].values, True
        )

    def test_fix_data_frame_precision_datetime(self):
        """Test fixing a data frame with a datetime hat has microsecond precision."""

        data_frame = pandas.DataFrame(
            {
                "timestamp": ["1456"],
                "datetime": ["2024-07-24T10:57:02.877297Z"],
            }
        )
        fixed_frame = self._importer._fix_data_frame(data_frame)
        self.assertIsNotNone(fixed_frame)

        print(fixed_frame["datetime"].values)
        self.assertIs(
            "2024-07-24T10:57:02+0000" in fixed_frame["datetime"].values, True
        )

    def test_fix_data_frame_precision_timestamp(self):
        """Test fixing a data frame with a timestamp hat has microsecond precision."""

        data_frame = pandas.DataFrame(
            {
                "timestamp": ["1331698658276340"],
                "datetime": ["1985-01-21T10:57:02.25Z"],
            }
        )
        fixed_frame = self._importer._fix_data_frame(data_frame)
        self.assertIsNotNone(fixed_frame)

        self.assertIs(
            "1985-01-21T10:57:02+0000" in fixed_frame["datetime"].values, True
        )
        self.assertIs("1331698658276340" in fixed_frame["timestamp"].values, True)

    def _run_all_tests(self, columns, lines):
        """Run all tests on the result set of a streamer."""
        # The first line is the column line.
        self.assertEqual(len(lines), 5)

        column_set = set(columns)
        correct_set = set(
            [
                "message",
                "timestamp_desc",
                "datetime",
                "timestamp",
                "vital_stats",
                "random_number",
                "correct",
                "stuff",
            ]
        )

        self.assertSetEqual(column_set, correct_set)

        messages = [x.get("message", "N/A") for x in lines]
        message_correct = set(
            [
                "fra sjalfstaedi til sjalfstaedis -> True [52]",
                "from bar to foobar -> False [13245]",
                "sidasti sens ad kaupa gjof -> True [5231134324]",
                "stordagur -> True [59913]",
                "hraeda hraedur -> True [420]",
            ]
        )
        self.assertSetEqual(set(messages), message_correct)


class RunAnalyzersTest(unittest.TestCase):
    """Tests for the run_analyzers function."""

    @mock.patch("timesketch_import_client.importer.logger")
    def test_run_analyzers_without_timeline(self, mock_logger):
        """Test calling run_analyzers without a timeline object."""
        with self.assertRaises(ValueError):
            importer.run_analyzers(analyzer_names=["test_analyzer"])
        mock_logger.error.assert_called_with(
            "Unable to run analyzers: Timeline object not found."
        )

    @mock.patch("timesketch_import_client.importer.logger")
    def test_run_analyzers_timeline_not_ready(self, mock_logger):
        """Test calling run_analyzers with a timeline that is not ready."""
        timeline_obj = mock.Mock(status="pending", name="test")
        importer.run_analyzers(
            analyzer_names=["test_analyzer"], timeline_obj=timeline_obj
        )
        mock_logger.error.assert_called_with(
            "The provided timeline '%s' is not ready yet!", timeline_obj.name
        )

    @mock.patch("timesketch_import_client.importer.logger")
    def test_run_analyzers_without_analyzers(self, mock_logger):
        """Test calling run_analyzers without analyzers."""
        timeline_obj = mock.Mock(status="ready")
        importer.run_analyzers(timeline_obj=timeline_obj)
        mock_logger.info.assert_called_with(
            "No analyzer names provided, skipping analysis."
        )

    @mock.patch("timesketch_import_client.importer.logger")
    def test_run_analyzers_success(self, mock_logger):
        """Test calling run_analyzers successfully."""
        timeline_obj = mock.Mock(
            status="ready", run_analyzers=mock.Mock(return_value="Success")
        )
        return_value = importer.run_analyzers(
            analyzer_names=["test_analyzer"], timeline_obj=timeline_obj
        )
        self.assertEqual(return_value, "Success")
        mock_logger.debug.assert_called_with("Analyzer results: %s", "Success")

    @mock.patch("timesketch_import_client.importer.logger")
    def test_run_analyzers_failed(self, mock_logger):
        """Test calling run_analyzers with an exception."""
        timeline_obj = mock.Mock(
            status="ready",
            run_analyzers=mock.Mock(
                side_effect=UnableToRunAnalyzer("Analyzer failed.")
            ),
        )
        return_value = importer.run_analyzers(
            analyzer_names=["test_analyzer"], timeline_obj=timeline_obj
        )
        self.assertIsNone(return_value)
        mock_logger.error.assert_called_with(
            "Failed to run requested analyzers '%s'! Error: %s",
            "['test_analyzer']",
            "Analyzer failed.",
        )
