# Copyright 2023 Google Inc. All rights reserved.
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
"""End to end tests of Timesketch upload functionality."""
import json
import os
import random

from timesketch_api_client import search

from . import interface, manager


class UploadTest(interface.BaseEndToEndTest):
    """End to end tests for upload functionality."""

    NAME = "upload_test"

    def test_invalid_index_name(self):
        """Test uploading a timeline with an invalid index name."""
        with self.assertions.assertRaises(RuntimeError):
            self.import_timeline("evtx.plaso", index_name="/invalid/index/name")

    def test_normal_upload_json(self):
        """Test the upload of a json file with a few events."""
        # create a new sketch
        rand = random.randint(0, 10000)
        sketch = self.api.create_sketch(name=f"test_normal_upload_json {rand}")
        self.sketch = sketch

        file_path = (
            "/usr/local/src/timesketch/end_to_end_tests/test_data/sigma_events.jsonl"
        )
        self.import_timeline(file_path, index_name=rand, sketch=sketch)
        timeline = sketch.list_timelines()[0]
        # check that timeline was uploaded correctly
        self.assertions.assertEqual(timeline.name, file_path)
        self.assertions.assertEqual(timeline.index.name, str(rand))
        self.assertions.assertEqual(timeline.index.status, "ready")

        events = sketch.explore("*", as_pandas=True)
        self.assertions.assertEqual(len(events), 4)

    def test_large_upload_jsonl(self):
        """Test uploading a timeline with a lot of events as jsonl. The test
        will create a temporary file with a large number of events and then
        upload the file to Timesketch. The test will then check that the
        number of events in the timeline is correct."""

        # create a new sketch
        rand = random.randint(0, 10000)
        sketch = self.api.create_sketch(name=f"test_large_upload_json {rand}")
        self.sketch = sketch

        file_path = "/tmp/large.jsonl"

        with open(file_path, "w", encoding="utf-8") as file_object:
            for i in range(4123):
                string = f'{{"message":"Count {i} {rand}","timestamp":"123456789","datetime":"2015-07-24T19:01:01+00:00","timestamp_desc":"Write time","data_type":"foobarjson"}}\n'
                file_object.write(string)

        self.import_timeline("/tmp/large.jsonl", index_name=rand, sketch=sketch)
        os.remove(file_path)

        timeline = sketch.list_timelines()[0]
        # check that timeline was uploaded correctly
        self.assertions.assertEqual(timeline.name, file_path)
        self.assertions.assertEqual(timeline.index.name, str(rand))
        self.assertions.assertEqual(timeline.index.status, "ready")

        search_obj = search.Search(sketch)
        search_obj.query_string = "data_type:foobarjson"
        search_obj.commit()
        self.assertions.assertEqual(len(search_obj.table), 4123)

        # check that the number of events is correct with a different method
        events = sketch.explore("data_type:foobarjson", as_pandas=True)
        self.assertions.assertEqual(len(events), 4123)

    def test_upload_jsonl_mapping_exceeds_limit(self):
        """Test uploading a timeline with a jsonl events that exceeds the
        default field mapping limit of 1000. The test will create a temporary
        file with events that have many unique keys and then upload the file to
        Timesketch. The test will then check that the correct error is triggered.
        """

        # create a new sketch
        rand = random.randint(0, 10000)
        sketch = self.api.create_sketch(
            name=f"test_upload_jsonl_mapping_exceeds_limit {rand}"
        )
        self.sketch = sketch

        file_path = "/tmp/mapping_over_1k.jsonl"
        num_lines = 100
        num_keys_per_line = 6
        all_keys = set()

        with open(file_path, "w", encoding="utf-8") as file_object:
            for i in range(num_lines):
                line_data = {
                    "datetime": "2015-07-24T19:01:01+00:00",
                    "message": f"Event {i} of {num_lines}",
                    "timestamp_desc": "test",
                    "data_type": "test:jsonl",
                }
                for j in range(num_keys_per_line):
                    key = f"field_name_{j}_{random.randint(0, 100000)}"
                    while key in all_keys:  # Avoid duplicate keys
                        key = f"field_name_{random.randint(0, 100000)}"
                    all_keys.add(key)
                    line_data[key] = f"value_{j}_{random.randint(0, 10000)}"

                json.dump(line_data, file_object)
                file_object.write("\n")

        try:
            self.import_timeline(file_path, index_name=rand, sketch=sketch)
        except RuntimeError:
            print(
                "Timeline import failing is expected. Checking for the correct "
                "error message..."
            )
        os.remove(file_path)

        timeline = sketch.list_timelines()[0]
        # check that timeline threw the correct error
        self.assertions.assertEqual(timeline.name, file_path)
        self.assertions.assertEqual(timeline.index.name, str(rand))
        self.assertions.assertEqual(timeline.index.status, "fail")
        self.assertions.assertIn(
            "OPENSEARCH_MAPPING_UPPER_LIMIT", timeline.data_sources[0]["error_message"]
        )

    def test_very_large_upload_jsonl(self):
        """Test uploading a timeline with over 50 k events as jsonl. The test
        will create a temporary file and then
        upload the file to Timesketch. The test will check that the
        number of events in the timeline is correct."""

        # create a new sketch
        rand = random.randint(0, 10000)
        sketch = self.api.create_sketch(name=f"test__very_large_upload_json {rand}")
        self.sketch = sketch

        file_path = "/tmp/verylarge.jsonl"

        with open(file_path, "w", encoding="utf-8") as file_object:
            for i in range(74251):
                string = f'{{"message":"Count {i} {rand}","timestamp":"123456789","datetime":"2015-07-24T19:01:01+00:00","timestamp_desc":"Write time","data_type":"foobarjsonverlarge"}}\n'
                file_object.write(string)

        self.import_timeline(file_path, index_name=rand, sketch=sketch)
        os.remove(file_path)

        timeline = sketch.list_timelines()[0]
        # check that timeline was uploaded correctly
        self.assertions.assertEqual(timeline.name, file_path)
        self.assertions.assertEqual(timeline.index.name, str(rand))
        self.assertions.assertEqual(timeline.index.status, "ready")

        search_obj = search.Search(sketch)
        search_obj.query_string = "data_type:foobarjsonverlarge"
        search_obj.commit()

        # normal max query limit
        self.assertions.assertEqual(len(search_obj.table), 10000)
        self.assertions.assertEqual(search_obj.expected_size, 74251)

        # increase max entries returned:
        search_obj.max_entries = 100000
        search_obj.commit()
        self.assertions.assertEqual(len(search_obj.table), 74251)

        # check that the number of events is correct with a different method
        events = sketch.explore(
            "data_type:foobarjsonverlarge", as_pandas=True, max_entries=100000
        )
        self.assertions.assertEqual(len(events), 74251)

    def test_large_upload_csv(self):
        """Test uploading a timeline with an a lot of events.
        The test will create a temporary file with a large number of events
        and then upload the file to Timesketch.
        The test will then check that the number of events in the timeline
        is correct."""

        # create a new sketch
        rand = str(random.randint(0, 10000))
        sketch = self.api.create_sketch(name=rand)
        self.sketch = sketch

        file_path = "/tmp/large.csv"

        with open(file_path, "w", encoding="utf-8") as file_object:
            file_object.write(
                '"message","timestamp","datetime","timestamp_desc","data_type"\n'
            )

            for i in range(3251):
                # write a line with random values for message
                string = (
                    f'"CSV Count: {i} {rand}","123456789",'
                    '"2015-07-24T19:01:01+00:00","Write time","foobarcsv"\n'
                )
                file_object.write(string)

        self.import_timeline("/tmp/large.csv", index_name=rand, sketch=sketch)
        os.remove(file_path)

        timeline = sketch.list_timelines()[0]
        # check that timeline was uploaded correctly
        self.assertions.assertEqual(timeline.name, file_path)
        self.assertions.assertEqual(timeline.index.name, str(rand))
        self.assertions.assertEqual(timeline.index.status, "ready")

        search_obj = search.Search(sketch)
        search_obj.query_string = "data_type:foobarcsv"
        search_obj.commit()
        self.assertions.assertEqual(len(search_obj.table), 3251)

        # check that the number of events is correct with a different method
        events = sketch.explore("data_type:foobarcsv", as_pandas=True)
        self.assertions.assertEqual(len(events), 3251)

    def test_large_upload_csv_over_flush_limit(self):
        """Test uploading a timeline with an a lot of events > 50 k.
        The test will create a temporary file with a large number of events
        and then upload the file to Timesketch.
        The test will then check that the number of events in the timeline
        is correct."""

        # create a new sketch
        rand = str(random.randint(0, 10000))
        sketch = self.api.create_sketch(name=rand)
        self.sketch = sketch

        file_path = "/tmp/verylarge.csv"

        with open(file_path, "w", encoding="utf-8") as file_object:
            file_object.write(
                '"message","timestamp","datetime","timestamp_desc","data_type"\n'
            )

            for i in range(73251):
                # write a line with random values for message
                string = (
                    f'"CSV Count: {i} {rand}","123456789",'
                    '"2015-07-24T19:01:01+00:00","Write time","73kcsv"\n'
                )
                file_object.write(string)

        self.import_timeline("/tmp/verylarge.csv", index_name=rand, sketch=sketch)
        os.remove(file_path)

        timeline = sketch.list_timelines()[0]
        # check that timeline was uploaded correctly
        self.assertions.assertEqual(timeline.name, file_path)
        self.assertions.assertEqual(timeline.index.name, str(rand))
        self.assertions.assertEqual(timeline.index.status, "ready")

        search_obj = search.Search(sketch)
        search_obj.query_string = "data_type:73kcsv"
        search_obj.commit()

        # normal max query limit
        self.assertions.assertEqual(len(search_obj.table), 10000)
        self.assertions.assertEqual(search_obj.expected_size, 73251)

        # increase max entries returned:
        search_obj.max_entries = 100000
        search_obj.commit()
        self.assertions.assertEqual(len(search_obj.table), 73251)

        # check that the number of events is correct with a different method
        events = sketch.explore("data_type:73kcsv", as_pandas=True, max_entries=100000)
        self.assertions.assertEqual(len(events), 73251)

    def test_csv_different_timestamps(self):
        """Test uploading a timeline with different precision of timestamps."""

        # create a new sketch
        rand = str(random.randint(0, 10000))
        sketch = self.api.create_sketch(name=f"csv_different_timestamps_{rand}")
        self.sketch = sketch

        file_path = "/tmp/timestamptest.csv"

        with open(file_path, "w", encoding="utf-8") as file_object:
            file_object.write(
                '"message","timestamp","datetime","timestamp_desc","data_type"\n'
            )
            string = (
                '"total precision","123456789",'
                '"2024-07-24T10:57:02.877297Z","Write time","timestamptest"\n'
            )
            file_object.write(string)
            string = (
                '"ISO8601","1331698658276340",'
                '"2015-07-24T19:01:01+00:00","Write time","timestamptest"\n'
            )
            file_object.write(string)
            string = (
                '"Wrong epoch","123456",'
                '"2015-07-24 19:01:01","Write time","timestamptest fail"\n'
            )
            file_object.write(string)
            string = '"no_datetime","123456","","Write time","no_datetime"\n'
            file_object.write(string)
            string = (
                '"Notimestamp","",'
                '"2015-07-24 19:01:01","Write time","no_timestamp"\n'
            )
            file_object.write(string)
            string = (
                '"Accurate_timestamp","1331712840499027",'
                '"2015-07-24 19:01:01","Write time","Accurate_timestamp"\n'
            )
            file_object.write(string)

        self.import_timeline("/tmp/timestamptest.csv", index_name=rand, sketch=sketch)
        os.remove(file_path)

        timeline = sketch.list_timelines()[0]
        # check that timeline was uploaded correctly
        self.assertions.assertEqual(timeline.name, file_path)
        self.assertions.assertEqual(timeline.index.name, str(rand))
        self.assertions.assertEqual(timeline.index.status, "ready")

        search_obj = search.Search(sketch)
        search_obj.query_string = "data_type:timestamptest"
        search_obj.commit()
        self.assertions.assertEqual(len(search_obj.table), 3)

        # check that the number of events is correct with a different method
        events = sketch.explore("data_type:timestamptest", as_pandas=True)
        self.assertions.assertEqual(len(events), 3)

        # check that events with no timestamp
        events = sketch.explore("data_type:no_timestamp", as_pandas=True)
        self.assertions.assertEqual(len(events), 1)

        # check number of events with no datetime
        events = sketch.explore("data_type:no_datetime", as_pandas=True)
        self.assertions.assertEqual(len(events), 1)


manager.EndToEndTestManager.register_test(UploadTest)
