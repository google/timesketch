# Copyright 2018 Google Inc. All rights reserved.
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
"""Tests for analysis interface."""

import json
from unittest import mock

from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.lib.analyzers import interface
from timesketch.models.sketch import Analysis
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Story
from timesketch.models.sketch import View


class TestAnalysisEvent(BaseTest):
    """Tests for the functionality of the Event class."""

    SKETCH_ID = 1

    def test_event(self):
        """Tests creating an Event object."""
        sketch = interface.Sketch(sketch_id=self.SKETCH_ID)
        datastore = MockDataStore("127.0.0.1", 4711)
        valid_event = {
            "_id": "1",
            "_type": "test",
            "_index": "test",
            "_source": {"__ts_timeline_id": 1, "test": True},
        }
        invalid_event = {"_id": "1"}
        event = interface.Event(valid_event, datastore, sketch=None)
        sketch_event = interface.Event(valid_event, datastore, sketch=sketch)
        self.assertIsInstance(event.datastore, MockDataStore)
        self.assertIsNone(event.sketch)
        self.assertIsInstance(sketch_event.sketch, interface.Sketch)
        self.assertRaises(KeyError, interface.Event, invalid_event, datastore)


class TestAnalysisSketch(BaseTest):
    """Tests for the functionality of the Sketch class."""

    SKETCH_ID = 1

    def test_sketch(self):
        """Test creating a sketch object."""
        sketch = interface.Sketch(sketch_id=self.SKETCH_ID)
        self.assertEqual(sketch.id, self.SKETCH_ID)
        self.assertIsInstance(sketch.sql_sketch, Sketch)

    def test_add_view(self):
        """Test adding a view to a sketch."""
        sketch = interface.Sketch(sketch_id=self.SKETCH_ID)
        view = sketch.add_view(
            view_name="MockView", analyzer_name="Test", query_string="test"
        )
        self.assertIsInstance(view, View)

    def test_add_story(self):
        """Test adding a story to a sketch."""
        sketch = interface.Sketch(sketch_id=self.SKETCH_ID)
        story = sketch.add_story(title="test")
        view = sketch.add_view(
            view_name="MockView", analyzer_name="Test", query_string="test"
        )
        sql_story = story.story
        story.add_text("test")
        story.add_view(view)
        content_json = sql_story.content
        content_list = json.loads(sql_story.content)
        self.assertIsInstance(sql_story, Story)
        self.assertIsInstance(content_json, str)
        self.assertIsInstance(content_list, list)
        self.assertIsInstance(content_list[0], dict)
        self.assertIsInstance(content_list[1], dict)

    def test_get_all_instances(self):
        """Test get all indices from a sketch."""
        sketch = interface.Sketch(sketch_id=self.SKETCH_ID)
        indices = sketch.get_all_indices()
        self.assertIsInstance(indices, list)
        self.assertEqual(len(indices), 1)
        self.assertEqual(indices[0], "test")


class _DummyAnalyzer(interface.BaseAnalyzer):
    """Minimal analyzer subclass for testing BaseAnalyzer.run_wrapper."""

    NAME = "dummy_analyzer"
    DISPLAY_NAME = "Dummy Analyzer"
    DESCRIPTION = "Minimal analyzer for unit testing."

    def run(self):
        """Return a dummy summary."""
        return "ok"


class TestBaseAnalyzerRunWrapper(BaseTest):
    """Tests for BaseAnalyzer.run_wrapper edge cases."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_run_wrapper_aborts_when_timeline_deleted(self):
        """run_wrapper marks analysis ERROR instead of crashing if timeline is gone."""
        analysis = Analysis(
            name="dummy_analyzer",
            description="desc",
            analyzer_name="dummy_analyzer",
            parameters="{}",
            user=self.user1,
            sketch=self.sketch1,
            timeline=None,
        )
        analysis.set_status("PENDING")
        analysis_id = analysis.id

        analyzer = _DummyAnalyzer(index_name="test", sketch_id=self.sketch1.id)
        result = analyzer.run_wrapper(analysis_id)

        self.assertEqual(result, "Failed")
        refreshed = Analysis.get_by_id(analysis_id)
        self.assertEqual(refreshed.get_status.status, "ERROR")
        self.assertEqual(
            refreshed.result, "Timeline was deleted before analyzer started."
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_run_wrapper_aborts_when_analysis_missing(self):
        """run_wrapper returns Failed cleanly when analysis ID does not exist."""
        analyzer = _DummyAnalyzer(index_name="test", sketch_id=self.sketch1.id)
        result = analyzer.run_wrapper(999999)
        self.assertEqual(result, "Failed")
