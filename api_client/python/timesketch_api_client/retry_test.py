# Copyright 2025 Google Inc. All rights reserved.
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
"""Tests for the VerboseRetry class."""

import unittest
from unittest import mock

from urllib3.exceptions import MaxRetryError

from timesketch_api_client import client


class RetryTest(unittest.TestCase):
    """Tests for the VerboseRetry class."""

    @mock.patch("timesketch_api_client.client.logger")
    def test_warning_log_on_retryable_error(self, mock_logger):
        """Test that a warning is logged on a retryable error."""
        # Arrange
        retry = client.VerboseRetry(total=4, status_forcelist=[500])
        mock_response = mock.Mock()
        mock_response.status = 500
        mock_response.data = b'{"message": "Server is busy"}'

        # Act
        retry.increment(response=mock_response)

        # Assert
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0]
        self.assertEqual(call_args[0], "Error %d received (Attempt %d/%d): %s")
        self.assertEqual(call_args[1], 500)
        self.assertEqual(call_args[2], 1)
        self.assertEqual(call_args[3], 5)
        self.assertEqual(call_args[4], '{"message": "Server is busy"}')

    @mock.patch("urllib3.util.retry.Retry.increment")
    def test_final_exception_format(self, mock_super_increment):
        """Test the format of the final exception after all retries fail."""
        # Arrange
        reason = "Too many errors"
        mock_super_increment.side_effect = MaxRetryError(None, None, reason=reason)
        retry = client.VerboseRetry(total=4)
        retry.history = [mock.Mock()] * 4  # Simulate 4 previous attempts

        mock_response = mock.Mock()
        mock_response.data = b'{"message": "Giving up"}'

        # Act & Assert
        with self.assertRaises(MaxRetryError) as cm:
            retry.increment(response=mock_response)

        final_reason = str(cm.exception.reason)
        self.assertIn(reason, final_reason)
        self.assertIn("Attempts: 4", final_reason)
        self.assertIn('Server Response: {"message": "Giving up"}', final_reason)

    @mock.patch("urllib3.util.retry.Retry.increment")
    def test_final_exception_no_body(self, mock_super_increment):
        """Test the exception format when the final response has no body."""
        # Arrange
        reason = "Connection refused"
        mock_super_increment.side_effect = MaxRetryError(None, None, reason=reason)
        retry = client.VerboseRetry(total=4)
        retry.history = [mock.Mock()] * 4
        mock_response = mock.Mock()
        mock_response.data = None

        # Act & Assert
        with self.assertRaises(MaxRetryError) as cm:
            retry.increment(response=mock_response)

        final_reason = str(cm.exception.reason)
        self.assertIn(reason, final_reason)
        self.assertIn("Attempts: 4", final_reason)
        self.assertNotIn("Server Response:", final_reason)
