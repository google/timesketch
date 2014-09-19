# Copyright 2014 Google Inc. All rights reserved.
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
"""Unit tests for timesketch models"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.query import QuerySet

from timesketch.apps.sketch.models import Sketch
from timesketch.apps.sketch.models import SavedView
from timesketch.apps.sketch.models import Timeline
from timesketch.apps.sketch.models import SketchTimeline


class ModelSketchTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(username="testuser1")
        self.user2 = User.objects.create(username="testuser2")
        self.sketch1 = Sketch.objects.create(owner=self.user1, title="testsketch1")
        self.sketch2 = Sketch.objects.create(owner=self.user1, title="testsketch2")
        SavedView.objects.create(user=self.user1, sketch=self.sketch2, query="",
                                 filter="")
        self.sketch1.make_public(self.user1)
        self.sketch2.make_private(self.user1)

    def test_get_named_views(self):
        self.assertIsInstance(self.sketch1.savedview_set.all(), QuerySet)
        self.assertEqual(self.sketch1.savedview_set.all().count(), 0)

        self.assertIsInstance(self.sketch2.savedview_set.all(), QuerySet)
        self.assertEqual(self.sketch2.savedview_set.all().count(), 1)

    def test_ace(self):
        self.assertEqual(self.sketch1.is_public(), True)
        self.assertEqual(self.sketch1.can_read(self.user1), True)
        self.assertEqual(self.sketch2.is_public(), False)
        self.assertEqual(self.sketch2.can_read(self.user1), True)
        self.assertIsInstance(self.sketch1.get_collaborators(), set)


class ModelTimelineTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser1")
        self.timeline1 = Timeline.objects.create(owner=self.user, title="test1",
                                                 datastore_index="1")
        self.timeline2 = Timeline.objects.create(owner=self.user, title="test2",
                                                 datastore_index="2")
        self.timeline1.make_public(self.user)
        self.timeline2.make_private(self.user)

    def test_ace(self):
        self.assertEqual(self.timeline1.is_public(), True)
        self.assertEqual(self.timeline2.is_public(), False)
        self.assertEqual(self.timeline1.can_read(self.user), True)


class ModelSketchTimelineTest(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="testuser")
        self.timeline = Timeline.objects.create(owner=self.user, title="test",
                                                datastore_index="123456")
        self.sketch_timeline = SketchTimeline.objects.create(timeline=self.timeline)

    def test_generate_color(self):
        self.assertIsInstance(self.sketch_timeline.generate_color(), str)
        self.assertEqual(len(self.sketch_timeline.generate_color()), 6)
