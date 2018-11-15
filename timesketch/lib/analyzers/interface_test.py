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

from __future__ import unicode_literals

from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.lib.analyzers import interface
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import View


class TestAnalysisEvent(BaseTest):
    """Tests for the functionality of the Event class."""

    SKETCH_ID = 1

    def test_event(self):
        """Tests creating an Event object."""
        sketch = interface.Sketch(sketch_id=self.SKETCH_ID)
        datastore = MockDataStore('127.0.0.1', 4711)
        valid_event = dict(
            _id='1', _type='test', _index='test', _source='test')
        invalid_event = dict(_id='1')
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
        view = sketch.add_view('MockView', query_string='test')
        self.assertIsInstance(view, View)

    def test_get_all_instances(self):
        """Test get all indices from a sketch."""
        sketch = interface.Sketch(sketch_id=self.SKETCH_ID)
        indices = sketch.get_all_indices()
        self.assertIsInstance(indices, list)
        self.assertEqual(len(indices), 1)
        self.assertEquals(indices[0], 'test')
