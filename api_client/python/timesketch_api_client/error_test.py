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
"""Tests for the Timesketch API client error handling."""

from __future__ import unicode_literals

import unittest
import mock

from . import error


class ErrorTest(unittest.TestCase):
    """Test error handling functions."""

    # pylint: disable=protected-access

    def test_get_message_with_none(self):
        """Test _get_message with None response."""
        self.assertEqual(error._get_message(None), "n/a")

    def test_get_message_no_text(self):
        """Test _get_message with response lacking text attribute."""
        mock_response = mock.Mock(spec=[])
        self.assertEqual(error._get_message(mock_response), "n/a")

    def test_get_message_html(self):
        """Test _get_message with HTML response."""
        mock_response = mock.Mock()
        mock_response.text = "<html><body><p>Error message</p></body></html>"
        self.assertEqual(error._get_message(mock_response), "Error message")

    def test_get_message_json(self):
        """Test _get_message with JSON response."""
        mock_response = mock.Mock()
        mock_response.text = '{"message": "JSON error"}'
        self.assertEqual(error._get_message(mock_response), "JSON error")

    def test_get_message_plain_text(self):
        """Test _get_message with plain text response."""
        mock_response = mock.Mock()
        mock_response.text = "Plain text error"
        self.assertEqual(error._get_message(mock_response), "Plain text error")

    def test_get_reason_with_none(self):
        """Test _get_reason with None response."""
        self.assertEqual(error._get_reason(None), "n/a")

    def test_get_reason_no_reason(self):
        """Test _get_reason with response lacking reason attribute."""
        mock_response = mock.Mock(spec=[])
        self.assertEqual(error._get_reason(mock_response), "n/a")

    def test_get_reason_with_reason(self):
        """Test _get_reason with reason attribute."""
        mock_response = mock.Mock()
        mock_response.reason = "Not Found"
        self.assertEqual(error._get_reason(mock_response), "Not Found")

    def test_error_message_robustness(self):
        """Test error_message with incomplete response objects."""
        # Test with None response
        with self.assertRaises(RuntimeError) as cm:
            error.error_message(None, message="Failed")
        self.assertIn("Failed, with error [n/a] n/a n/a (n/a)", str(cm.exception))

        # Test with response lacking attributes
        mock_response = mock.Mock(spec=[])
        with self.assertRaises(RuntimeError) as cm:
            error.error_message(mock_response, message="Failed")
        self.assertIn("Failed, with error [n/a] n/a n/a (n/a)", str(cm.exception))

        # Test with partial attributes
        mock_response = mock.Mock()
        mock_response.status_code = 500
        mock_response.reason = "Internal Server Error"
        mock_response.text = "Something went wrong"
        mock_response.url = "http://localhost/api"
        # Remove request attribute if mock added it automatically
        if hasattr(mock_response, "request"):
            del mock_response.request

        with self.assertRaises(RuntimeError) as cm:
            error.error_message(mock_response, message="Failed")
        self.assertIn(
            "Failed, with error [500] Internal Server Error Something went wrong "
            "(http://localhost/api)",
            str(cm.exception),
        )
