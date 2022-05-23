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
"""Tests for the sketch models."""

from __future__ import unicode_literals

import json

from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sketch import View
from timesketch.models.sketch import Event
from timesketch.models.sketch import Story
from timesketch.lib.testlib import ModelBaseTest


class SketchModelTest(ModelBaseTest):
    """Tests the sketch models."""

    def test_sketch_model(self):
        """
        Test that the test sketch has the expected data stored in the
        database.
        """
        expected_result = frozenset(
            [("name", "Test 1"), ("description", "Test 1"), ("user", self.user1)]
        )
        self._test_db_object(expected_result=expected_result, model_cls=Sketch)

    def test_searchindex_model(self):
        """
        Test that the test searchindex has the expected data stored in the
        database.
        """
        expected_result = frozenset(
            [
                ("name", "test"),
                ("description", "test"),
                ("index_name", "test"),
                ("user", self.user1),
            ]
        )
        self._test_db_object(expected_result=expected_result, model_cls=SearchIndex)

    def test_timeline_model(self):
        """
        Test that the test timeline has the expected data stored in the
        database.
        """
        expected_result = frozenset(
            [
                ("name", "Timeline 1"),
                ("description", "Timeline 1"),
                ("user", self.user1),
                ("sketch", self.sketch1),
                ("searchindex", self.searchindex),
            ]
        )
        self._test_db_object(expected_result=expected_result, model_cls=Timeline)

    def test_view_model(self):
        """
        Test that the test view has the expected data stored in the database.
        """
        expected_result = frozenset(
            [
                ("name", "View 1"),
                ("query_string", "View 1"),
                ("user", self.user1),
                ("sketch", self.sketch1),
            ]
        )
        self._test_db_object(expected_result=expected_result, model_cls=View)

    def test_searchtemplate_model(self):
        """
        Test that the test search template has the expected data stored in the
        database.
        """
        expected_result = frozenset(
            [
                ("name", "template"),
                ("user", self.user1),
            ]
        )
        self._test_db_object(expected_result=expected_result, model_cls=SearchTemplate)

    def test_event_model(self):
        """
        Test that the test event has the expected data stored in the database.
        """
        expected_result = frozenset(
            [
                ("searchindex", self.searchindex),
                ("sketch", self.sketch1),
                ("document_id", "test"),
            ]
        )
        self._test_db_object(expected_result=expected_result, model_cls=Event)

    def test_validate_filter(self):
        """
        Test the query filter validation.
        """
        DEFAULT_LIMIT = 40
        default_values = {
            "from": 0,
            "size": DEFAULT_LIMIT,
            "terminate_after": DEFAULT_LIMIT,
            "indices": [],
            "exclude": [],
            "order": "asc",
            "chips": [],
        }
        test_filter = dict(indices=[])
        test_filter_json = json.dumps(test_filter)
        validated_filter_dict = self.view1.validate_filter(test_filter)
        validated_filter_json = self.view1.validate_filter(test_filter_json)
        self.assertDictEqual(json.loads(validated_filter_dict), default_values)
        self.assertDictEqual(json.loads(validated_filter_json), default_values)


class StoryModelTest(ModelBaseTest):
    """Tests the user model."""

    def test_story_model(self):
        """
        Test that the test story has the expected data stored in the
        database.
        """
        expected_result = frozenset(
            [
                ("title", "Test"),
                ("content", "Test"),
                ("user", self.user1),
                ("sketch", self.sketch1),
            ]
        )
        self._test_db_object(expected_result=expected_result, model_cls=Story)
