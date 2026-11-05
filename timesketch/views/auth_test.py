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
"""Tests for the auth views."""

from unittest import mock
from flask import current_app
from flask_login import current_user
from werkzeug.exceptions import InternalServerError

from timesketch.lib.definitions import HTTP_STATUS_CODE_REDIRECT
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR
from timesketch.lib.definitions import HTTP_STATUS_CODE_UNAUTHORIZED
from timesketch.lib.google_auth import CSRF_KEY
from timesketch.lib.testlib import BaseTest
from timesketch.models import db_session
from timesketch.models.user import Group
from timesketch.models.user import User


class AuthViewTest(BaseTest):
    """Test the auth view."""

    def test_login_view_unauthenticated(self):
        """Test the login view handler with an unauthenticated session."""
        response = self.client.get("/login/")
        self.assert200(response)

    def test_login_view_form_authenticated(self):
        """Test the login view handler with an authenticated session."""
        self.login()
        response = self.client.get("/login/")
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)

    def test_login_view_sso_authenticated(self):
        """Test the login view handler with an SSO authenticated session."""
        current_app.config["SSO_ENABLED"] = True
        current_app.config["SSO_GROUP_ENV_VARIABLE"] = "SSO_GROUP"
        current_app.config["SSO_GROUP_SEPARATOR"] = ";"
        current_app.config["SSO_GROUP_NOT_MEMBER_SIGN"] = "-"
        with self.client:
            response = self.client.get(
                "/login/",
                environ_base={
                    "REMOTE_USER": "test1",
                    "SSO_GROUP": "test_group1;-test_group2",
                },
            )
            self.assertEqual(current_user.username, "test1")
            self.assertIn(self.group1, current_user.groups)
            self.assertNotIn(self.group2, current_user.groups)
            self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)

    def test_logout_view(self):
        """Test the logout view handler."""
        self.login()
        response = self.client.get("/logout/")
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)

    @mock.patch("flask.current_app.logger")
    def test_login_invalid_next_url(self, mock_logger):
        """Test the login view handler with an invalid next_url."""
        invalid_next_urls = [
            "//example.com",
            "/\\example.com",
            "http://example.com",
            "///example.com",
            "/\t/example.com",
            "/\n/example.com",
            "/\r/example.com",
            "/\x0b/example.com",
            "/\x0c/example.com",
            "javascript:alert(1)",
            "file:///etc/passwd",
        ]
        for url in invalid_next_urls:
            response = self.client.get(f"/login/?next={url}")
            self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
            mock_logger.warning.assert_called()
            mock_logger.warning.reset_mock()

    def test_login_authenticated_invalid_next_url(self):
        """Test authenticated user redirect to '/' if 'next' is unsafe."""
        self.login()
        response = self.client.get("/login/?next=//example.com")
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        self.assertTrue(response.headers.get("Location").endswith("/"))

    def test_login_authenticated_valid_next_url(self):
        """Test authenticated user redirect to safe 'next' URL."""
        self.login()
        response = self.client.get("/login/?next=/sketch/1/")
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        self.assertTrue(response.headers.get("Location").endswith("/sketch/1/"))


class AuthApiViewTest(BaseTest):
    """Test the auth API view."""

    @mock.patch("timesketch.views.auth.requests.post")
    @mock.patch("timesketch.views.auth.get_oauth2_discovery_document")
    @mock.patch("timesketch.views.auth.validate_jwt")
    def test_validate_api_token_scope_superset(self, _, mock_discovery, mock_post):
        """Test validate_api_token with superset of scopes."""
        # Setup config
        self.app.config["GOOGLE_OIDC_CLIENT_ID"] = "test_client_id"
        self.app.config["GOOGLE_OIDC_API_CLIENT_ID"] = "test_api_client_id"

        # Mock responses
        mock_discovery.return_value = {"issuer": "https://accounts.google.com"}

        # Mock requests.post
        def side_effect(*_, **kwargs):
            data = kwargs.get("data", {})
            if "access_token" in data:
                return mock.Mock(
                    status_code=200,
                    json=lambda: {
                        # This includes extra scopes (short forms) that caused
                        # the failure previously.
                        "scope": (
                            "email profile openid "
                            "https://www.googleapis.com/auth/userinfo.profile "
                            "https://www.googleapis.com/auth/userinfo.email"
                        ),
                        "azp": "test_client_id",
                        "email": "test@example.com",
                    },
                )
            if "id_token" in data:
                return mock.Mock(
                    status_code=200,
                    json=lambda: {
                        "email_verified": True,
                        "azp": "test_client_id",
                        "email": "test@example.com",
                        "aud": "test_client_id",
                    },
                )
            return mock.Mock(status_code=400)

        mock_post.side_effect = side_effect

        # Headers and Args
        headers = {"Authorization": "Bearer test_access_token"}

        with mock.patch.object(self.app.logger, "warning") as mock_warning:
            response = self.client.get(
                "/login/api_callback/?id_token=test_id_token", headers=headers
            )
            mock_warning.assert_called()
        # We expect 200 because scope mismatch is now relaxed
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_OK)
        self.assertIn(b"Authenticated", response.data)


class GoogleOpenIdConnectViewTest(BaseTest):
    """Tests for the google_openid_connect view."""

    def _login_via_oidc(self, decoded_jwt, csrf_token="test-csrf-token"):
        """Call the OIDC callback route with the OIDC dependencies mocked."""
        with self.client.session_transaction() as sess:
            sess[CSRF_KEY] = csrf_token

        discovery_document = {
            "id_token_signing_alg_values_supported": ["RS256"],
            "issuer": "https://example-issuer.example.com",
            "jwks_uri": "https://example-issuer.example.com/certs",
        }
        with mock.patch(
            "timesketch.views.auth.get_encoded_jwt_over_https",
            return_value="encoded-jwt",
        ), mock.patch(
            "timesketch.views.auth.get_oauth2_discovery_document",
            return_value=discovery_document,
        ), mock.patch(
            "timesketch.views.auth.get_public_key_for_jwt",
            return_value="public-key",
        ), mock.patch(
            "timesketch.views.auth.decode_jwt", return_value=decoded_jwt
        ), mock.patch(
            "timesketch.views.auth.validate_jwt"
        ):
            return self.client.get(
                f"/login/google_openid_connect/?code=test-code&state={csrf_token}"
            )

    def test_login_allowed_users(self):
        """Test GOOGLE_OIDC_ALLOWED_USERS restricts who can log in."""
        cases = [
            ("no allowlist configured allows any user", [], HTTP_STATUS_CODE_REDIRECT),
            (
                "user present in the allowlist is allowed",
                ["allowed@example.com"],
                HTTP_STATUS_CODE_REDIRECT,
            ),
            (
                "user missing from the allowlist is rejected",
                ["other@example.com"],
                HTTP_STATUS_CODE_UNAUTHORIZED,
            ),
        ]
        for description, allowed_users, expected_status in cases:
            with self.subTest(description):
                self.app.config["GOOGLE_OIDC_ALLOWED_USERS"] = allowed_users
                response = self._login_via_oidc({"email": "allowed@example.com"})
                self.assertEqual(response.status_code, expected_status)

    def test_login_rejects_user_not_in_allowed_group(self):
        """Test login is rejected for a user without an allowed group."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_ALLOWED_GROUPS"] = ["Admins"]

        response = self._login_via_oidc(
            {"email": "newuser@example.com", "groups": ["Users"]}
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_UNAUTHORIZED)
        self.assertIsNone(User.query.filter_by(username="newuser@example.com").first())

    def test_login_allows_user_in_allowed_group(self):
        """Test login succeeds for a user who is a member of an allowed group."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_ALLOWED_GROUPS"] = ["Admins", "Users"]

        response = self._login_via_oidc(
            {"email": "newuser@example.com", "groups": ["Users"]}
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        self.assertIsNotNone(
            User.query.filter_by(username="newuser@example.com").first()
        )

    def test_login_syncs_groups_and_grants_admin(self):
        """Test a successful login syncs groups and grants admin rights."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True
        self.app.config["GOOGLE_OIDC_ADMIN_GROUP"] = "Admins"

        response = self._login_via_oidc(
            {"email": "newuser@example.com", "groups": ["Admins", "Analysts"]}
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        user = User.query.filter_by(username="newuser@example.com").first()
        self.assertIsNotNone(user)
        self.assertTrue(user.admin)
        self.assertCountEqual(
            [group.name for group in user.groups], ["Admins", "Analysts"]
        )

    def test_login_does_not_sync_groups_when_sync_disabled(self):
        """Test groups/admin are untouched when GROUPS_SYNC_ENABLED is off."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_ADMIN_GROUP"] = "Admins"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = False

        response = self._login_via_oidc(
            {"email": "newuser@example.com", "groups": ["Admins"]}
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        user = User.query.filter_by(username="newuser@example.com").first()
        self.assertIsNotNone(user)
        self.assertFalse(user.admin)
        self.assertEqual(list(user.groups), [])

    def test_login_removes_stale_groups_and_admin_on_subsequent_login(self):
        """Test groups/admin no longer present in the token get revoked."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True
        self.app.config["GOOGLE_OIDC_ADMIN_GROUP"] = "Admins"
        self.app.config["GOOGLE_OIDC_GROUPS_REMOVE_STALE"] = True

        self._login_via_oidc(
            {"email": "newuser@example.com", "groups": ["Admins", "Analysts"]},
            csrf_token="csrf-token-1",
        )
        user = User.query.filter_by(username="newuser@example.com").first()
        self.assertTrue(user.admin)
        self.assertCountEqual(
            [group.name for group in user.groups], ["Admins", "Analysts"]
        )

        response = self._login_via_oidc(
            {"email": "newuser@example.com", "groups": ["Analysts"]},
            csrf_token="csrf-token-2",
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        user = User.query.filter_by(username="newuser@example.com").first()
        self.assertFalse(user.admin)
        self.assertEqual([group.name for group in user.groups], ["Analysts"])

    def test_login_keeps_stale_groups_and_admin_when_remove_stale_disabled(self):
        """Test groups/admin are kept when GROUPS_REMOVE_STALE is off."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True
        self.app.config["GOOGLE_OIDC_ADMIN_GROUP"] = "Admins"
        self.app.config["GOOGLE_OIDC_GROUPS_REMOVE_STALE"] = False

        self._login_via_oidc(
            {"email": "newuser@example.com", "groups": ["Admins", "Analysts"]},
            csrf_token="csrf-token-1",
        )

        response = self._login_via_oidc(
            {"email": "newuser@example.com", "groups": ["Analysts"]},
            csrf_token="csrf-token-2",
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        user = User.query.filter_by(username="newuser@example.com").first()
        self.assertTrue(user.admin)
        self.assertCountEqual(
            [group.name for group in user.groups], ["Admins", "Analysts"]
        )

    def test_login_allowed_users_and_groups_are_combined(self):
        """Test ALLOWED_USERS and ALLOWED_GROUPS add up (OR), not intersect."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_ALLOWED_USERS"] = ["listed@example.com"]
        self.app.config["GOOGLE_OIDC_ALLOWED_GROUPS"] = ["Analysts"]
        cases = [
            ("listed user outside the group", "listed@example.com", ["Other"], True),
            ("group member not listed", "member@example.com", ["Analysts"], True),
            ("neither listed nor member", "other@example.com", ["Other"], False),
        ]
        for description, email, groups, expected_allowed in cases:
            with self.subTest(description):
                response = self._login_via_oidc({"email": email, "groups": groups})
                expected_status = (
                    HTTP_STATUS_CODE_REDIRECT
                    if expected_allowed
                    else HTTP_STATUS_CODE_UNAUTHORIZED
                )
                self.assertEqual(response.status_code, expected_status)

    def test_denied_login_does_not_log_token_groups(self):
        """Test the names of the token groups are not logged on denial."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_ALLOWED_GROUPS"] = ["Analysts"]

        with self.assertLogs(self.app.logger, level="WARNING") as logs:
            response = self._login_via_oidc(
                {"email": "denied@example.com", "groups": ["SecretGroupName"]}
            )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_UNAUTHORIZED)
        self.assertNotIn("SecretGroupName", "\n".join(logs.output))

    def test_remove_stale_without_admin_group_keeps_admin(self):
        """Test REMOVE_STALE doesn't revoke admin when no ADMIN_GROUP is set."""
        self._create_user("existing-admin@example.com", set_admin=True)
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True
        self.app.config["GOOGLE_OIDC_GROUPS_REMOVE_STALE"] = True
        self.app.config["GOOGLE_OIDC_ADMIN_GROUP"] = ""

        response = self._login_via_oidc(
            {"email": "existing-admin@example.com", "groups": ["Analysts"]}
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        user = User.query.filter_by(username="existing-admin@example.com").first()
        self.assertTrue(user.admin)

    def test_sync_failure_does_not_log_the_user_in(self):
        """Test a failing group sync leaves no authenticated session."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True

        # Use an HTTPException: Flask handles it and still saves the session,
        # so the test fails if login_user() ran before the sync. A plain
        # exception would propagate in test mode before the session is saved.
        with mock.patch(
            "timesketch.views.auth._sync_oidc_groups",
            side_effect=InternalServerError("sync failed"),
        ):
            response = self._login_via_oidc(
                {"email": "newuser@example.com", "groups": ["Analysts"]}
            )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR)
        with self.client.session_transaction() as sess:
            self.assertNotIn("_user_id", sess)

    def test_missing_groups_claim_logs_warning(self):
        """Test a warning is logged when the claim is missing and sync is on."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True

        with self.assertLogs(self.app.logger, level="WARNING") as logs:
            response = self._login_via_oidc({"email": "newuser@example.com"})

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        self.assertIn("missing from the token", "\n".join(logs.output))

    def test_missing_groups_claim_no_warning_when_sync_disabled(self):
        """Test no missing-claim warning is logged when sync is disabled."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = False

        with self.assertNoLogs(self.app.logger, level="WARNING"):
            response = self._login_via_oidc({"email": "newuser@example.com"})

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)

    def test_incomplete_groups_claim_rejects_login(self):
        """Test login is rejected when the claim is flagged as incomplete."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True
        self.app.config["GOOGLE_OIDC_GROUPS_REMOVE_STALE"] = True

        response = self._login_via_oidc(
            {
                "email": "newuser@example.com",
                "_claim_names": {"groups": "src1"},
                "_claim_sources": {"src1": {"endpoint": "https://graph.example.com"}},
            }
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_UNAUTHORIZED)
        self.assertIn(b"too many groups", response.data)
        self.assertIsNone(User.query.filter_by(username="newuser@example.com").first())

    def test_invalid_groups_regex_returns_configuration_error(self):
        """Test an invalid GROUPS_REGEX logs an error and returns HTTP 500."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_REGEX"] = "CN=([^,"

        with self.assertLogs(self.app.logger, level="ERROR") as logs:
            response = self._login_via_oidc(
                {"email": "newuser@example.com", "groups": ["CN=Admins,OU=X"]}
            )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR)
        self.assertIn("Invalid GOOGLE_OIDC_GROUPS_REGEX", "\n".join(logs.output))

    def test_sync_skips_group_names_that_are_too_long(self):
        """Test group names exceeding the database column length are skipped."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True

        response = self._login_via_oidc(
            {"email": "newuser@example.com", "groups": ["x" * 300, "Analysts"]}
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        user = User.query.filter_by(username="newuser@example.com").first()
        self.assertEqual([group.name for group in user.groups], ["Analysts"])

    def test_sync_reuses_group_created_with_other_display_name(self):
        """Test a locally created group is reused instead of re-inserted."""
        local_group = Group(name="Analysts", display_name="Local Analysts")
        self._commit_to_database(local_group)
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True

        response = self._login_via_oidc(
            {"email": "newuser@example.com", "groups": ["Analysts"]}
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        user = User.query.filter_by(username="newuser@example.com").first()
        self.assertEqual([group.id for group in user.groups], [local_group.id])

    def test_login_extracts_groups_using_separator_and_regex(self):
        """Test the groups claim is parsed using the separator/regex config."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SEPARATOR"] = ";"
        self.app.config["GOOGLE_OIDC_GROUPS_REGEX"] = "CN=([^,]+)"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True

        response = self._login_via_oidc(
            {
                "email": "newuser@example.com",
                "groups": "CN=Admins,OU=X;CN=Analysts,OU=Y",
            }
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        user = User.query.filter_by(username="newuser@example.com").first()
        self.assertIsNotNone(user)
        self.assertCountEqual(
            [group.name for group in user.groups], ["Admins", "Analysts"]
        )

    def test_admin_group_member_can_log_in_without_allowed_group(self):
        """Test ADMIN_GROUP members may log in when ALLOWED_GROUPS is set."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True
        self.app.config["GOOGLE_OIDC_ALLOWED_GROUPS"] = ["Analysts"]
        self.app.config["GOOGLE_OIDC_ADMIN_GROUP"] = "Admins"

        response = self._login_via_oidc(
            {"email": "newuser@example.com", "groups": ["Admins"]}
        )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        user = User.query.filter_by(username="newuser@example.com").first()
        self.assertTrue(user.admin)
        # The admin group is not synced as a Timesketch group unless allowed.
        self.assertEqual(list(user.groups), [])

    def test_configured_group_names_are_normalized_with_regex(self):
        """Test ALLOWED_GROUPS/ADMIN_GROUP work with raw and extracted names."""
        cases = [
            ("raw names", ["ts-analysts"], "ts-admins"),
            ("extracted names", ["analysts"], "admins"),
        ]
        for index, (description, allowed_groups, admin_group) in enumerate(cases):
            with self.subTest(description):
                self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
                self.app.config["GOOGLE_OIDC_GROUPS_REGEX"] = r"^ts-(.+)$"
                self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True
                self.app.config["GOOGLE_OIDC_ALLOWED_GROUPS"] = allowed_groups
                self.app.config["GOOGLE_OIDC_ADMIN_GROUP"] = admin_group
                email = f"user{index}@example.com"

                response = self._login_via_oidc(
                    {"email": email, "groups": ["ts-analysts", "ts-admins"]},
                    csrf_token=f"csrf-token-{index}",
                )

                self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
                user = User.query.filter_by(username=email).first()
                self.assertTrue(user.admin)
                self.assertEqual([group.name for group in user.groups], ["analysts"])

    def test_sync_ignores_non_string_claim_values(self):
        """Test nested objects, numbers and booleans don't become groups."""
        self.app.config["GOOGLE_OIDC_GROUPS_CLAIM"] = "groups"
        self.app.config["GOOGLE_OIDC_GROUPS_SYNC_ENABLED"] = True

        with self.assertLogs(self.app.logger, level="WARNING") as logs:
            response = self._login_via_oidc(
                {
                    "email": "newuser@example.com",
                    "groups": [{"id": "1", "name": "A"}, True, 42, "Analysts"],
                }
            )

        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)
        user = User.query.filter_by(username="newuser@example.com").first()
        self.assertEqual([group.name for group in user.groups], ["Analysts"])
        self.assertIn("Ignored 3 non-string value(s)", "\n".join(logs.output))


class DisabledUserTest(BaseTest):
    """Test that disabled users cannot log in or use existing sessions."""

    API_URL = "/api/v1/users/me/"

    def _set_active(self, username, active):
        """Enables or disables a user."""
        user = User.query.filter_by(username=username).first()
        user.active = active
        db_session.add(user)
        db_session.commit()

    @staticmethod
    def _get_session_user_id(client):
        """Returns the user ID stored in the session of a test client."""
        with client.session_transaction() as session:
            return session.get("_user_id")

    def _api_callback_login(self, client):
        """Logs in through the API callback with mocked token responses."""
        self.app.config["GOOGLE_OIDC_CLIENT_ID"] = "test_client_id"
        self.app.config["GOOGLE_OIDC_API_CLIENT_ID"] = "test_api_client_id"
        token_info = {
            "scope": (
                "openid https://www.googleapis.com/auth/userinfo.profile "
                "https://www.googleapis.com/auth/userinfo.email"
            ),
            "email_verified": True,
            "azp": "test_client_id",
            "aud": "test_client_id",
            "email": "test1",
        }
        with mock.patch("timesketch.views.auth.requests.post") as mock_post, mock.patch(
            "timesketch.views.auth.get_oauth2_discovery_document"
        ) as mock_discovery, mock.patch("timesketch.views.auth.validate_jwt"):
            mock_discovery.return_value = {"issuer": "https://accounts.google.com"}
            mock_post.return_value = mock.Mock(status_code=200, json=lambda: token_info)
            return client.get(
                "/login/api_callback/?id_token=test_id_token",
                headers={"Authorization": "Bearer test_access_token"},
            )

    def test_active_user_property(self):
        """Test the is_active property of the user model."""
        self.assertTrue(self.user1.is_active)
        self.user1.active = False
        self.assertFalse(self.user1.is_active)
        self.assertFalse(self.user1.is_authenticated)

    def test_existing_session(self):
        """Test that the session of a disabled user is no longer valid."""
        self.login()
        self.assert200(self.client.get(self.API_URL))

        self._set_active("test1", False)
        response = self.client.get(self.API_URL)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)

    def test_password_login(self):
        """Test that a disabled user cannot log in with a password."""
        self._set_active("test1", False)
        self.login()
        self.assertIsNone(self._get_session_user_id(self.client))
        response = self.client.get(self.API_URL)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)

        self._set_active("test1", True)
        self.login()
        self.assert200(self.client.get(self.API_URL))

    def test_remember_cookie(self):
        """Test that the remember cookie of a disabled user is not valid."""
        response = self._api_callback_login(self.client)
        self.assert200(response)
        remember_cookie = self.client.get_cookie("remember_token")
        self.assertIsNotNone(remember_cookie)

        self._set_active("test1", False)
        client = self.app.test_client()
        client.set_cookie("remember_token", remember_cookie.value)
        response = client.get(self.API_URL)
        self.assertEqual(response.status_code, HTTP_STATUS_CODE_REDIRECT)

    def test_api_callback_login(self):
        """Test that a disabled user cannot log in through the API callback."""
        self._set_active("test1", False)
        response = self._api_callback_login(self.client)
        self.assertNotEqual(response.status_code, HTTP_STATUS_CODE_OK)
        self.assertIsNone(self._get_session_user_id(self.client))
        self.assertIsNone(self.client.get_cookie("remember_token"))
