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
"""Test for the ACL model."""

from __future__ import unicode_literals

from timesketch.lib.testlib import BaseTest


class AclModelTest(BaseTest):
    """Test the ACL model."""

    def test_change_permission(self):
        """Test changing permissions on a sketch with ACL."""
        for permission in ("read", "write", "delete"):
            self.sketch1.grant_permission(permission=permission, user=self.user1)
            self.assertTrue(
                self.sketch1.has_permission(permission=permission, user=self.user1)
            )
            self.sketch1.revoke_permission(permission=permission, user=self.user1)
            self.assertFalse(
                self.sketch1.has_permission(permission=permission, user=self.user1)
            )

            # Test group permissions
            self.sketch1.grant_permission(permission=permission, group=self.group1)
            self.assertTrue(
                self.sketch1.has_permission(permission=permission, user=self.user1)
            )
            self.sketch1.revoke_permission(permission=permission, group=self.group1)
            self.assertFalse(
                self.sketch1.has_permission(permission=permission, user=self.user1)
            )

    def test_change_public(self):
        """Test toggle the public permission on a sketch."""
        self.sketch1.grant_permission(permission="read")
        self.assertTrue(self.sketch1.is_public)
        self.sketch1.revoke_permission(permission="read")
        self.assertFalse(self.sketch1.is_public)
