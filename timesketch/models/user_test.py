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
"""Tests for the user model."""

from __future__ import unicode_literals

from timesketch.lib.testlib import ModelBaseTest
from timesketch.models.user import Group
from timesketch.models.user import User


class UserModelTest(ModelBaseTest):
    """Tests the user model."""

    def test_user_model(self):
        """
        Test that the test user has the expected data stored in the
        database.
        """
        expected_result = frozenset([("name", "test1"), ("username", "test1")])
        self._test_db_object(expected_result=expected_result, model_cls=User)

    def test_set_password(self):
        """Test setting a password for the user."""
        self.assertIsNone(self.user1.set_password("test", rounds=4))

    def test_valid_password(self):
        """Test checking a valid password."""
        self.assertTrue(self.user1.check_password("test"))

    def test_invalid_password(self):
        """Test checking a invalid password."""
        self.assertFalse(self.user1.check_password("invalid password"))


class GroupModelTest(ModelBaseTest):
    """Tests the user model."""

    def test_group_model(self):
        """
        Test that the test group has the expected data stored in the
        database.
        """
        expected_result = frozenset(
            [
                ("name", "test_group1"),
                ("display_name", "test_group1"),
                ("description", "test_group1"),
            ]
        )
        self._test_db_object(expected_result=expected_result, model_cls=Group)

    def test_group_membership(self):
        """Test that user1 is member of the group."""
        self.assertTrue(self.user1 in self.group1.users)
