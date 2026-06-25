# Copyright 2017 Google Inc. All rights reserved.
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
"""Tests for the Timesketch API client"""

from __future__ import unicode_literals

import unittest
from unittest import mock

from . import client
from . import sketch as sketch_lib
from . import test_lib


class TimesketchApiTest(unittest.TestCase):
    """Test TimesketchApi"""

    @mock.patch("requests.Session", test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")

    def test_fetch_resource_data(self):
        """Test fetch resource."""
        response = self.api_client.fetch_resource_data("sketches/")
        self.assertIsInstance(response, dict)

    @mock.patch("timesketch_api_client.error.get_response_json")
    def test_create_sketch(self, mock_get_json):
        """Test create sketch."""
        # Test successful creation
        mock_get_json.return_value = {
            "objects": [{"id": 1, "name": "test", "description": "test"}]
        }
        sketch = self.api_client.create_sketch("test", "test")
        self.assertIsInstance(sketch, sketch_lib.Sketch)
        self.assertEqual(sketch.id, 1)

        # Test missing 'objects' key
        mock_get_json.return_value = {"meta": {}}
        with self.assertRaises(ValueError):
            self.api_client.create_sketch("test", "test")

        # Test empty 'objects' list
        mock_get_json.return_value = {"objects": []}
        with self.assertRaises(ValueError):
            self.api_client.create_sketch("test", "test")

        # Test malformed 'objects' (not a list of dicts with 'id')
        mock_get_json.return_value = {"objects": "invalid"}
        with self.assertRaises(ValueError):
            self.api_client.create_sketch("test", "test")

    def test_get_sketch(self):
        """Test to get a sketch."""
        sketch = self.api_client.get_sketch(1)
        self.assertIsInstance(sketch, sketch_lib.Sketch)
        self.assertEqual(sketch.id, 1)
        self.assertEqual(sketch.name, "test")
        self.assertEqual(sketch.description, "test")

    def test_get_sketches(self):
        """Test to get a list of sketches."""
        sketches = list(self.api_client.list_sketches())
        self.assertIsInstance(sketches, list)
        self.assertEqual(len(sketches), 1)
        self.assertIsInstance(sketches[0], sketch_lib.Sketch)

    def test_get_sketches_by_name(self):
        """Test to get sketches by name."""
        sketches = self.api_client.get_sketches_by_name("test")
        self.assertIsInstance(sketches, list)
        self.assertEqual(len(sketches), 1)
        self.assertIsInstance(sketches[0], sketch_lib.Sketch)
        self.assertEqual(sketches[0].name, "test")

    def test_get_sketches_by_name_not_found(self):
        """Test that get_sketches_by_name raises KeyError for unknown name."""
        with self.assertRaises(KeyError):
            self.api_client.get_sketches_by_name("nonexistent_sketch")

    @mock.patch("requests.Session", test_lib.mock_session)
    def test_get_sketches_by_name_duplicates(self):
        """Test get_sketches_by_name returns multiple sketches with same name."""
        with mock.patch.object(self.api_client, "list_sketches") as mock_list:
            sketch_1 = sketch_lib.Sketch(sketch_id=1, api=self.api_client,
                                         sketch_name="duplicate")
            sketch_2 = sketch_lib.Sketch(sketch_id=2, api=self.api_client,
                                         sketch_name="duplicate")
            mock_list.return_value = iter([sketch_1, sketch_2])

            sketches = self.api_client.get_sketches_by_name("duplicate")
            self.assertIsInstance(sketches, list)
            self.assertEqual(len(sketches), 2)
            self.assertEqual(sketches[0].id, 1)
            self.assertEqual(sketches[1].id, 2)

    @mock.patch("requests.Session", test_lib.mock_session)
    def test_get_sketches_by_name_case_sensitive(self):
        """Test that get_sketches_by_name matching is case-sensitive."""
        with mock.patch.object(self.api_client, "list_sketches") as mock_list:
            sketch_1 = sketch_lib.Sketch(sketch_id=1, api=self.api_client,
                                         sketch_name="My Sketch")
            mock_list.return_value = iter([sketch_1])

            with self.assertRaises(KeyError):
                self.api_client.get_sketches_by_name("my sketch")


class TimesketchApiRetryTest(unittest.TestCase):
    """Test TimesketchApi client retry logic."""

    @mock.patch("requests.Session")
    def test_session_retry_configuration(self, mock_session):
        """Test that the session is configured with retry logic."""
        # Mock the response from the server.
        mock_response = mock.Mock()
        mock_response.text = '<input id="csrf_token" name="csrf_token" value="test">'
        mock_session.return_value.get.return_value = mock_response

        # Mock the POST response for authentication
        mock_post_response = mock.Mock()
        mock_post_response.status_code = 200
        mock_post_response.url = "http://testhost/"
        mock_session.return_value.post.return_value = mock_post_response

        mock_adapter = mock.MagicMock()
        with mock.patch(
            "timesketch_api_client.client.HTTPAdapter", return_value=mock_adapter
        ) as mock_http_adapter:
            client.TimesketchApi(
                host_uri="http://testhost", username="testuser", password="testpassword"
            )

            # Check that a Retry object was created with the correct params
            mock_http_adapter.assert_called_once()
            retry_arg = mock_http_adapter.call_args[1]["max_retries"]
            self.assertEqual(retry_arg.total, client.TimesketchApi.DEFAULT_RETRY_COUNT)
            self.assertEqual(retry_arg.status_forcelist, [500, 502, 503, 504])

            # Check that the adapter was mounted for http and https
            mock_session_instance = mock_session.return_value
            mock_session_instance.mount.assert_any_call("http://", mock_adapter)
            mock_session_instance.mount.assert_any_call("https://", mock_adapter)

    @mock.patch("requests.Session")
    def test_authenticate_session_fail(self, mock_session):
        """Test that _authenticate_session raises RuntimeError on login failure."""
        # Mock the GET response for CSRF token
        mock_get_response = mock.Mock()
        mock_get_response.text = (
            '<input id="csrf_token" name="csrf_token" value="test">'
        )
        mock_session.return_value.get.return_value = mock_get_response

        # Mock the POST response for authentication to simulate failure
        # (redirect back to /login).
        mock_post_response = mock.Mock()
        mock_post_response.status_code = 200
        mock_post_response.url = "http://testhost/login"
        mock_session.return_value.post.return_value = mock_post_response

        with self.assertRaises(RuntimeError) as context:
            client.TimesketchApi(
                host_uri="http://testhost", username="testuser", password="testpassword"
            )

        self.assertEqual(
            str(context.exception),
            "Unable to connect to server, error: Authentication failed: "
            "Invalid username or password.",
        )

    @mock.patch("timesketch_api_client.client.googleauth_flow.InstalledAppFlow")
    def test_oauth_timeout_error(self, mock_flow_class):
        """Test reproduction of b/446157404 where AttributeError is raised."""
        mock_flow = mock.MagicMock()
        mock_flow_class.from_client_config.return_value = mock_flow

        # Simulate the bug in google_auth_oauthlib where run_local_server
        # raises AttributeError when wsgi_app.last_request_uri is None
        def mock_run_local_server(**unused_kwargs):
            # This is what happens in google_auth_oauthlib/flow.py
            last_request_uri = None
            last_request_uri.replace("http", "https")

        mock_flow.run_local_server.side_effect = mock_run_local_server

        api = client.TimesketchApi(
            "http://localhost", "user", auth_mode="oauth", create_session=False
        )

        with self.assertRaises(RuntimeError) as cm:
            # pylint: disable=protected-access
            api._create_oauth_session(client_id="abc", client_secret="def")

        self.assertIn(
            "Authentication failed: No authorization response received",
            str(cm.exception),
        )

    @mock.patch("timesketch_api_client.client.googleauth_flow.InstalledAppFlow")
    def test_oauth_timeout_parameter(self, mock_flow_class):
        """Test that timeout_seconds is passed to run_local_server."""
        mock_flow = mock.MagicMock()
        mock_flow_class.from_client_config.return_value = mock_flow

        api = client.TimesketchApi(
            "http://localhost", "user", auth_mode="oauth", create_session=False
        )

        with mock.patch.object(api, "authenticate_oauth_session") as mock_auth:
            # pylint: disable=protected-access
            api._create_oauth_session(
                client_id="abc", client_secret="def", timeout_seconds=42
            )
            mock_auth.assert_called_once()

        mock_flow.run_local_server.assert_called_once_with(
            host="localhost",
            port=8080,
            open_browser=False,
            timeout_seconds=42,
        )

    @mock.patch("timesketch_api_client.client.googleauth_flow.InstalledAppFlow")
    def test_constructor_auth_timeout(self, mock_flow_class):
        """Test that auth_timeout in constructor is passed down."""
        mock_flow = mock.MagicMock()
        mock_flow_class.from_client_config.return_value = mock_flow

        with mock.patch.object(client.TimesketchApi, "authenticate_oauth_session"):
            client.TimesketchApi(
                "http://localhost", "user", auth_mode="oauth", auth_timeout=123
            )

        mock_flow.run_local_server.assert_called_once_with(
            host="localhost",
            port=8080,
            open_browser=False,
            timeout_seconds=123,
        )
