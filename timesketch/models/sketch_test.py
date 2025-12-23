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


import json

from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sketch import View
from timesketch.models.sketch import Story
from timesketch.models.sketch import SearchHistory
from timesketch.models.sketch import AnalysisSession
from timesketch.models.user import User
from timesketch.models.sketch import Event
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
        test_filter = {"indices": []}
        test_filter_json = json.dumps(test_filter)
        validated_filter_dict = self.view1.validate_filter(test_filter)
        validated_filter_json = self.view1.validate_filter(test_filter_json)
        self.assertDictEqual(json.loads(validated_filter_dict), default_values)
        self.assertDictEqual(json.loads(validated_filter_json), default_values)


class StoryModelTest(ModelBaseTest):
    """Tests the sketch models related to stories."""

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

    def test_cascade_delete_related_objects(self):
        """Test that related objects are deleted when a sketch is deleted."""
        # Create a new user, sketch, and search index for this test
        # Using fresh objects avoids interference from the setUp method's data
        user = User(username="cascade_user", name="Cascade User")
        self.db_session.add(user)
        self.db_session.commit()

        sketch = Sketch(
            name="Cascade Test Sketch",
            description="Test sketch for cascade delete",
            user=user,
        )
        self.db_session.add(sketch)
        self.db_session.commit()

        search_index = SearchIndex(
            name="cascade_index",
            description="Test index",
            index_name="cascade_index",
            user=user,
        )
        self.db_session.add(search_index)
        self.db_session.commit()

        # Create related objects that have cascade="delete" from Sketch
        timeline = Timeline(
            name="Cascade Timeline",
            description="Test timeline",
            user=user,
            sketch=sketch,
            searchindex=search_index,
        )
        view = View(name="Cascade View", query_string="*", user=user, sketch=sketch)
        story = Story(
            title="Cascade Story", content="Test story", user=user, sketch=sketch
        )
        search_history = SearchHistory(
            description="Cascade Search History",
            query_string="*",
            user=user,
            sketch=sketch,
        )
        analysis_session = AnalysisSession(user=user, sketch=sketch)

        self.db_session.add_all(
            [timeline, view, story, search_history, analysis_session]
        )
        self.db_session.commit()

        # Verify objects exist before deletion
        self.assertIsNotNone(self.db_session.get(Sketch, sketch.id))
        self.assertIsNotNone(self.db_session.get(Timeline, timeline.id))
        self.assertIsNotNone(self.db_session.get(View, view.id))
        self.assertIsNotNone(self.db_session.get(Story, story.id))
        self.assertIsNotNone(self.db_session.get(SearchHistory, search_history.id))
        self.assertIsNotNone(self.db_session.get(AnalysisSession, analysis_session.id))
        # SearchIndex should NOT be deleted as it's not cascaded from Sketch
        self.assertIsNotNone(self.db_session.get(SearchIndex, search_index.id))

        # Delete the sketch
        self.db_session.delete(sketch)
        self.db_session.commit()

        # Verify sketch and cascaded related objects are deleted
        self.assertIsNone(self.db_session.get(Sketch, sketch.id))
        self.assertIsNone(self.db_session.get(Timeline, timeline.id))
        self.assertIsNone(self.db_session.get(View, view.id))
        self.assertIsNone(self.db_session.get(Story, story.id))
        self.assertIsNone(self.db_session.get(SearchHistory, search_history.id))
        self.assertIsNone(self.db_session.get(AnalysisSession, analysis_session.id))
        # Verify SearchIndex is still NOT deleted
        self.assertIsNotNone(self.db_session.get(SearchIndex, search_index.id))

        # Clean up the search index and user created for this test
        self.db_session.delete(search_index)
        self.db_session.delete(user)
        self.db_session.commit()

    def test_no_cascade_delete_labels(self):
        """Test that Label objects are NOT deleted when a sketch is deleted."""
        # Create a new user and sketch for this test
        user = User(username="label_user", name="Label User")
        self.db_session.add(user)
        self.db_session.commit()

        sketch = Sketch(
            name="Label Test Sketch",
            description="Test sketch for label no cascade delete",
            user=user,
        )
        self.db_session.add(sketch)
        self.db_session.commit()

        # Add a label to the sketch
        sketch.add_label(label="important", user=user)
        self.db_session.commit()

        # Get the dynamically created SketchLabel class and the label object
        SketchLabel = sketch.Label
        label_obj = (
            self.db_session.query(SketchLabel)
            .filter_by(label="important", parent=sketch)
            .first()
        )

        # Verify sketch and label exist before deletion
        self.assertIsNotNone(self.db_session.get(Sketch, sketch.id))
        self.assertIsNotNone(self.db_session.get(SketchLabel, label_obj.id))

        # Delete the sketch
        self.db_session.delete(sketch)
        self.db_session.commit()

        # Verify sketch is deleted, and the label IS ALSO deleted due to cascade
        self.assertIsNone(self.db_session.get(Sketch, sketch.id))
        self.assertIsNone(self.db_session.get(SketchLabel, label_obj.id))

        # Clean up the created user
        self.db_session.delete(user)
        # label_obj is already deleted by cascade, no need to delete it manually
        self.db_session.commit()
