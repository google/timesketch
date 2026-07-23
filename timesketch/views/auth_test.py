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

from timesketch.lib.definitions import HTTP_STATUS_CODE_REDIRECT
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_UNAUTHORIZED
from timesketch.lib.google_auth import CSRF_KEY
from timesketch.lib.testlib import BaseTest
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
        """Call the OIDC callback route with the OIDC dependencies mocked.

        Args:
            decoded_jwt: The decoded JWT dict to return from decode_jwt().
            csrf_token: The CSRF token to use for both session and request.

        Returns:
            The Flask test client response.
        """
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
