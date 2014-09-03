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
        _user = User.objects.create(username="testuser")
        self.sketch1 = Sketch.objects.create(owner=_user, title="testsketch1")
        self.sketch2 = Sketch.objects.create(owner=_user, title="testsketch2")
        SavedView.objects.create(user=_user, sketch=self.sketch2, query="",
                                 filter="")

    def test_get_named_views(self):
        self.assertIsInstance(self.sketch1.get_named_views(), QuerySet)
        self.assertIsInstance(self.sketch2.get_named_views(), QuerySet)
        self.assertEqual(self.sketch1.get_named_views().count(), 0)
        self.assertEqual(self.sketch2.get_named_views().count(), 1)


class ModelSketchTimelineTest(TestCase):
    def setUp(self):
        _user = User.objects.create(username="testuser")
        _timeline = Timeline.objects.create(owner=_user, title="test",
                                            datastore_index="123456")
        self.timeline = SketchTimeline.objects.create(timeline=_timeline)

    def test_generate_color(self):
        self.assertIsInstance(self.timeline.generate_color(), str)
        self.assertEqual(len(self.timeline.generate_color()), 6)
