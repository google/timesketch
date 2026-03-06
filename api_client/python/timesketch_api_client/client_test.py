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
import mock

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


class TimesketchApiRetryTest(unittest.TestCase):
    """Test TimesketchApi client retry logic."""

    @mock.patch("requests.Session")
    def test_session_retry_configuration(self, mock_session):
        """Test that the session is configured with retry logic."""
        # Mock the response from the server.
        mock_response = mock.Mock()
        mock_response.text = '<input id="csrf_token" name="csrf_token" value="test">'
        mock_session.return_value.get.return_value = mock_response

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
