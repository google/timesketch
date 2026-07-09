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

    def test_change_permission_by_username(self):
        """Test changing permissions on a sketch using username resolution."""
        # 1. Grant permission newly
        success = self.sketch1.grant_permission_by_username(
            permission="read", username="test2"
        )
        self.assertTrue(success)
        self.assertTrue(self.sketch1.has_permission(permission="read", user=self.user2))

        # 2. Grant permission again (should return False because already present)
        success = self.sketch1.grant_permission_by_username(
            permission="read", username="test2"
        )
        self.assertFalse(success)

        # 3. Revoke permission
        success = self.sketch1.revoke_permission_by_username(
            permission="read", username="test2"
        )
        self.assertTrue(success)
        self.assertFalse(
            self.sketch1.has_permission(permission="read", user=self.user2)
        )

        # 4. Fallback: domain stripping in grant
        # (Should resolve "test2@example.com" to database user "test2")
        success = self.sketch1.grant_permission_by_username(
            permission="read", username="test2@example.com"
        )
        self.assertTrue(success)
        self.assertTrue(self.sketch1.has_permission(permission="read", user=self.user2))

        # 5. Fallback: domain stripping in revoke
        success = self.sketch1.revoke_permission_by_username(
            permission="read", username="test2@example.com"
        )
        self.assertTrue(success)
        self.assertFalse(
            self.sketch1.has_permission(permission="read", user=self.user2)
        )

        # 6. Raise ValueError on non-existent user (grant)
        with self.assertRaises(ValueError):
            self.sketch1.grant_permission_by_username(
                permission="read", username="nonexistent_user"
            )

        # 7. Raise ValueError on non-existent user (revoke)
        with self.assertRaises(ValueError):
            self.sketch1.revoke_permission_by_username(
                permission="read", username="nonexistent_user"
            )

    def test_revoke_user_with_group_permission(self):
        """Test revoking user permission doesn't affect group permission."""
        # 1. Grant read permission to a group that self.user1 belongs to
        self.sketch1.grant_permission(permission="read", group=self.group1)
        self.assertTrue(self.sketch1.has_permission(permission="read", user=self.user1))

        # 2. Revoke the user's read permission directly (this should be a no-op
        # because the user doesn't have a direct ACE, only group permission)
        self.sketch1.revoke_permission(permission="read", user=self.user1)

        # 3. Assert the user still has permission (inherited from the group)
        self.assertTrue(self.sketch1.has_permission(permission="read", user=self.user1))

        # Cleanup: revoke group permission
        self.sketch1.revoke_permission(permission="read", group=self.group1)
        self.assertFalse(
            self.sketch1.has_permission(permission="read", user=self.user1)
        )
