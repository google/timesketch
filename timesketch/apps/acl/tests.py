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
"""Tests for acl models."""

from django.contrib.auth.models import User
from django.test import TestCase

from timesketch.apps.acl.models import AccessControlEntry
from timesketch.apps.sketch.models import Sketch


# pylint: disable=no-member, too-many-public-methods
class ModelAccessControlEntryTest(TestCase):
    """Test for AccessControlEntry model."""
    def setUp(self):
        self.user = User.objects.create(username='user1')
        self.sketch1 = Sketch.objects.create(user=self.user, title='sketch1')
        self.sketch2 = Sketch.objects.create(user=self.user, title='sketch2')
        self.sketch1.make_public(self.user)
        self.sketch2.make_private(self.user)
        self.ace = self.sketch1.acl.create(user=self.user)
        # Make the sketch public again to catch the case where an public ace is
        # already present.
        self.sketch1.make_public(self.user)

    def test_access_control_entry(self):
        """Test AccessControlEntry."""
        self.assertEqual(self.sketch1.is_public(), True)
        self.assertEqual(self.sketch1.can_read(self.user), True)
        self.assertEqual(self.sketch2.is_public(), False)
        self.assertEqual(self.sketch2.can_read(self.user), True)
        self.assertIsInstance(self.sketch1.get_collaborators(), set)
        self.assertIsInstance(self.ace, AccessControlEntry)
