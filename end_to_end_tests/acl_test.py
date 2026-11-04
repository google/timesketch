# Copyright 2026 Google Inc. All rights reserved.
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
"""End to end tests for ACL security and authorization checks."""

import json
import uuid

from timesketch_api_client import client as api_client
from timesketch_api_client import search

from . import interface
from . import manager

USER2_USERNAME = "test2"
USER2_PASSWORD = "test2"


class AclTest(interface.BaseEndToEndTest):
    """End to end tests for ACL authorization checks."""

    NAME = "acl_test"

    def __init__(self):
        """Initialize the end-to-end test object with a second user session."""
        super().__init__()
        self.user2_api = api_client.TimesketchApi(
            host_uri=interface.HOST_URI,
            username=USER2_USERNAME,
            password=USER2_PASSWORD,
        )

    def test_collaborator_cannot_revoke_owner_permissions(self):
        """Test that a write-level collaborator cannot revoke owner permissions.

        Verifies fix for GHSA-vvf4-j4w4-xvgx:
        1. Owner (test) creates a sketch and adds collaborator (test2) with
           default write access (read=True, write=True, delete=False).
        2. Collaborator attempts to remove owner permissions with omitted
           'permissions' field -> must return 403 Forbidden.
        3. Collaborator attempts to remove owner 'read'/'write' explicitly
           -> must return 403 Forbidden.
        4. Collaborator attempts to remove owner 'delete' explicitly
           -> must return 403 Forbidden.
        5. Owner retains full read/write/delete access throughout.
        6. Owner can successfully remove collaborator -> returns 200 OK.
        """
        assert self.api is not None
        assert self.user2_api is not None

        sketch = self.sketch
        sketch_id = sketch.id
        collaborator_url = f"{self.api.api_root}/sketches/{sketch_id}/collaborators/"
        sketch_url = f"{self.api.api_root}/sketches/{sketch_id}/"

        # 1. Owner adds test2 as an ordinary collaborator (read + write)
        res = self.api.session.post(
            collaborator_url,
            json={"users": [USER2_USERNAME]},
        )
        self.assertions.assertEqual(res.status_code, 200)

        # Verify test2 can access the sketch
        res_user2_get = self.user2_api.session.get(sketch_url)
        self.assertions.assertEqual(res_user2_get.status_code, 200)

        # 2. Attack 1 (GHSA headline): Collaborator sends remove_users=[owner]
        # with 'permissions' omitted (defaults to stripping all permissions).
        res_attack1 = self.user2_api.session.post(
            collaborator_url,
            json={"remove_users": [interface.USERNAME]},
        )
        self.assertions.assertEqual(
            res_attack1.status_code,
            403,
            f"Expected 403 Forbidden when collaborator revokes owner with "
            f"omitted permissions, got {res_attack1.status_code}",
        )

        # Verify owner still has full read access
        res_owner_get = self.api.session.get(sketch_url)
        self.assertions.assertEqual(
            res_owner_get.status_code,
            200,
            "Owner was locked out of reading their own sketch!",
        )

        # 3. Attack 2 (Variant): Collaborator explicitly specifies read/write
        # when attempting to revoke from owner.
        res_attack2 = self.user2_api.session.post(
            collaborator_url,
            json={
                "remove_users": [interface.USERNAME],
                "permissions": json.dumps(["read", "write"]),
            },
        )
        self.assertions.assertEqual(
            res_attack2.status_code,
            403,
            f"Expected 403 Forbidden when collaborator revokes owner read/write, "
            f"got {res_attack2.status_code}",
        )

        # Verify owner still has read access
        res_owner_get2 = self.api.session.get(sketch_url)
        self.assertions.assertEqual(res_owner_get2.status_code, 200)

        # 4. Attack 3 (Inverted control): Collaborator explicitly specifies delete
        res_attack3 = self.user2_api.session.post(
            collaborator_url,
            json={
                "remove_users": [interface.USERNAME],
                "permissions": json.dumps(["delete"]),
            },
        )
        self.assertions.assertEqual(res_attack3.status_code, 403)

        # 5. Positive control: Owner removes collaborator
        res_owner_remove = self.api.session.post(
            collaborator_url,
            json={"remove_users": [USER2_USERNAME]},
        )
        self.assertions.assertEqual(res_owner_remove.status_code, 200)

        # Verify collaborator no longer has access
        res_user2_after = self.user2_api.session.get(sketch_url)
        self.assertions.assertEqual(res_user2_after.status_code, 403)

    def test_archive_and_unarchive_permissions(self):
        """Test sketch archive and unarchive permissions across user roles."""
        assert self.api is not None
        assert self.user2_api is not None
        assert self.admin_api is not None

        # 1. Collaborator with write access (read=True, write=True, delete=False)
        write_sketch = self.api.create_sketch(
            name=f"test-archive-perms-write_{uuid.uuid4().hex}"
        )
        self.import_timeline("sigma_events.jsonl", sketch=write_sketch)
        self.assertions.assertTrue(write_sketch.add_to_acl(user_list=[USER2_USERNAME]))

        sketch_url = f"{self.api.api_root}/sketches/{write_sketch.id}/"
        res_perms = self.user2_api.session.get(sketch_url)
        self.assertions.assertEqual(res_perms.status_code, 200)
        perms = res_perms.json()["meta"]["permissions"]
        self.assertions.assertTrue(perms["read"])
        self.assertions.assertTrue(perms["write"])
        self.assertions.assertFalse(perms["delete"])

        # Owner archives; write collaborator unarchives and re-archives
        self.assertions.assertTrue(write_sketch.archive())
        self.assertions.assertEqual(
            self.api.get_sketch(write_sketch.id).status, "archived"
        )

        user2_write_sketch = self.user2_api.get_sketch(write_sketch.id)
        self.assertions.assertTrue(
            user2_write_sketch.unarchive(),
            "Write collaborator failed to unarchive shared sketch.",
        )
        refreshed_write_sketch = self.user2_api.get_sketch(write_sketch.id)
        self.assertions.assertEqual(refreshed_write_sketch.status, "ready")

        search_client = search.Search(refreshed_write_sketch)
        self.assertions.assertEqual(len(search_client.table), 4)

        self.assertions.assertTrue(
            refreshed_write_sketch.archive(),
            "Write collaborator failed to archive shared sketch.",
        )
        self.assertions.assertEqual(
            self.api.get_sketch(write_sketch.id).status, "archived"
        )

        # 2. Collaborator with read-only access (read=True, write=False, delete=False)
        ro_sketch = self.api.create_sketch(
            name=f"test-archive-perms-readonly_{uuid.uuid4().hex}"
        )
        self.import_timeline("sigma_events.jsonl", sketch=ro_sketch)
        self.assertions.assertTrue(
            ro_sketch.add_to_acl(user_list=[USER2_USERNAME], permissions=["read"])
        )
        ro_archive_url = f"{self.api.api_root}/sketches/{ro_sketch.id}/archive/"
        initial_ro_status = self.api.get_sketch(ro_sketch.id).status
        self.assertions.assertNotEqual(initial_ro_status, "archived")

        res_ro_archive = self.user2_api.session.post(
            ro_archive_url, json={"action": "archive"}
        )
        self.assertions.assertEqual(res_ro_archive.status_code, 403)
        self.assertions.assertFalse(self.user2_api.get_sketch(ro_sketch.id).archive())
        self.assertions.assertEqual(
            self.api.get_sketch(ro_sketch.id).status, initial_ro_status
        )

        # Owner archives; read-only collaborator cannot unarchive or export archived
        self.assertions.assertTrue(ro_sketch.archive())
        self.assertions.assertEqual(
            self.api.get_sketch(ro_sketch.id).status, "archived"
        )

        res_ro_unarchive = self.user2_api.session.post(
            ro_archive_url, json={"action": "unarchive"}
        )
        self.assertions.assertEqual(res_ro_unarchive.status_code, 403)
        self.assertions.assertFalse(self.user2_api.get_sketch(ro_sketch.id).unarchive())
        self.assertions.assertEqual(
            self.api.get_sketch(ro_sketch.id).status, "archived"
        )

        res_ro_export = self.user2_api.session.post(
            ro_archive_url, json={"action": "export"}
        )
        self.assertions.assertEqual(res_ro_export.status_code, 403)
        self.assertions.assertEqual(
            self.api.get_sketch(ro_sketch.id).status, "archived"
        )

        # 3. Admin user without explicit ACL on a private sketch
        admin_target = self.api.create_sketch(
            name=f"test-archive-perms-admin_{uuid.uuid4().hex}"
        )
        self.import_timeline("sigma_events.jsonl", sketch=admin_target)

        admin_get_res = self.admin_api.session.get(
            f"{self.admin_api.api_root}/sketches/{admin_target.id}/"
        )
        self.assertions.assertEqual(admin_get_res.status_code, 200)
        self.assertions.assertTrue(admin_get_res.json()["meta"]["permissions"]["admin"])

        self.assertions.assertTrue(self.admin_api.get_sketch(admin_target.id).archive())
        self.assertions.assertEqual(
            self.admin_api.get_sketch(admin_target.id).status, "archived"
        )

        self.assertions.assertTrue(
            self.admin_api.get_sketch(admin_target.id).unarchive()
        )
        self.assertions.assertEqual(
            self.api.get_sketch(admin_target.id).status, "ready"
        )


manager.EndToEndTestManager.register_test(AclTest)
