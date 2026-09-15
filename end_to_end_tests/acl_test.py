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
from timesketch_api_client import client as api_client

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

        # (Deleted: The teardown will clean up the sketch)



    def test_json_parsing_and_types(self):
        """Tests the input validation for payload fields."""
        sketch_id = self.sketch.id
        collaborator_url = f"{self.api.api_root}/sketches/{sketch_id}/collaborators/"

        # 1. Native JSON Array for permissions
        res_native = self.api.session.post(
            collaborator_url,
            json={
                "users": [USER2_USERNAME],
                "permissions": ["read", "write"]
            },
        )
        self.assertions.assertEqual(res_native.status_code, 200)

        # 2. String-encoded JSON for permissions (legacy format)
        res_legacy = self.api.session.post(
            collaborator_url,
            json={
                "users": [USER2_USERNAME],
                "permissions": '["read", "write"]'
            },
        )
        self.assertions.assertEqual(res_legacy.status_code, 200)

        # 3. Malformed invalid types that used to crash (500 Internal Server Error)
        res_malformed = self.api.session.post(
            collaborator_url,
            json={
                "users": None,
                "groups": 123,
                "remove_users": True,
                "remove_groups": "string",
                "permissions": 123
            },
        )
        # Should gracefully ignore invalid fields and return 200 (since owner has write)
        self.assertions.assertEqual(res_malformed.status_code, 200)

    def test_atomicity_of_mutations(self):
        """Tests that the API rolls back entirely if a 403 occurs mid-payload."""
        sketch_id = self.sketch.id
        collaborator_url = f"{self.api.api_root}/sketches/{sketch_id}/collaborators/"
        sketch_url = f"{self.api.api_root}/sketches/{sketch_id}/"

        # Ensure user2 is added
        self.api.session.post(collaborator_url, json={"users": [USER2_USERNAME]})

        # User2 attempts to remove themselves AND the sketch owner (which will 403)
        res_attack = self.user2_api.session.post(
            collaborator_url,
            json={"remove_users": [USER2_USERNAME, interface.USERNAME]}
        )
        self.assertions.assertEqual(res_attack.status_code, 403)

        # Because of the two-pass fix, the valid operation (removing themselves)
        # should have been rolled back because the owner removal triggered an abort.
        res_verify = self.user2_api.session.get(sketch_url)
        self.assertions.assertEqual(
            res_verify.status_code, 
            200, 
            "Atomicity bug! User2 was successfully removed despite the 403."
        )

    def test_public_flag_preservation(self):
        """Tests that omitting the public flag does not silently revoke public access."""
        sketch_id = self.sketch.id
        collaborator_url = f"{self.api.api_root}/sketches/{sketch_id}/collaborators/"

        # 1. Explicitly make sketch public
        res_public = self.api.session.post(
            collaborator_url,
            json={"public": True}
        )
        self.assertions.assertEqual(res_public.status_code, 200)
        
        sketch_url = f"{self.api.api_root}/sketches/{sketch_id}/"
        # Verify it's public
        res_get_public = self.api.session.get(sketch_url)
        self.assertions.assertEqual(res_get_public.status_code, 200)
        self.assertions.assertTrue(res_get_public.json()["meta"]["permissions"]["public"])

        # 2. Add a user but OMIT the public flag
        res_update = self.api.session.post(
            collaborator_url,
            json={"users": [USER2_USERNAME]}
        )
        self.assertions.assertEqual(res_update.status_code, 200)

        # Verify it is STILL public (the bug would have made it private)
        res_get_after = self.api.session.get(sketch_url)
        self.assertions.assertTrue(
            res_get_after.json()["meta"]["permissions"]["public"], 
            "Silent public revocation bug! Sketch was made private."
        )


manager.EndToEndTestManager.register_test(AclTest)
