# Copyright 2018 Google Inc. All rights reserved.
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
"""Tests for Cloud IAP."""

from __future__ import unicode_literals

import mock
import jwt

from timesketch.lib.testlib import BaseTest
from timesketch.lib.cloud_iap import validate_jwt


# openssl ecparam -genkey -name prime256v1 -noout -out ec_private.pem
MOCK_EC_PRIVATE_KEY = """
-----BEGIN EC PRIVATE KEY-----
MHcCAQEEINoHHwc7+3FSbIg3UMS8w21G58EprN+OT6zGmP93vdhEoAoGCCqGSM49
AwEHoUQDQgAEkLZi2KNrKBnpRKvol8w+ZyaBdjtVdhXMONj3fbMzQNRt5/NvLbq6
1fWR3kDQQXp0Jq2hT0SrZn9M2gT5uqaUCQ==
-----END EC PRIVATE KEY-----
"""

# openssl ec -in ec_private.pem -pubout -out ec_public.pem
MOCK_EC_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEkLZi2KNrKBnpRKvol8w+ZyaBdjtV
dhXMONj3fbMzQNRt5/NvLbq61fWR3kDQQXp0Jq2hT0SrZn9M2gT5uqaUCQ==
-----END PUBLIC KEY-----
"""


# pylint: disable=unused-argument
def mock_get_iap_public_key(unused_argument):
    """Mock getting key from Google IAP service.

    Returns:
        Mock public key.
    """
    return MOCK_EC_PUBLIC_KEY


def create_test_iap_jwt():
    """Create test JSON Web Token (JWT).

    Returns:
        Encoded JWT signed with key.
    """
    header = {
        "alg": "ES256",
        "typ": "JWT",
        "kid": "test"
    }
    payload = {
        "sub": "1234567890",
        "email": "test@example.com",
        "iat": 1516239022,
        "aud": "/projects/1234/global/backendServices/1234"
    }
    return jwt.encode(
        payload, MOCK_EC_PRIVATE_KEY, algorithm='ES256', headers=header)


@mock.patch(
    u'timesketch.lib.cloud_iap.get_iap_public_key', mock_get_iap_public_key)
class TestCloudIap(BaseTest):
    """Tests for the functionality of the cloud_iap module."""

    def test_valid_jwt(self):
        """Test to validate a valid JWT."""
        test_jwt = create_test_iap_jwt()
        valid_jwt = validate_jwt(test_jwt, '1234', '1234')
        self.assertEqual(valid_jwt.get('email'), 'test@example.com')

    def test_invalid_cloud_project_number(self):
        """Test to validate a valid JWT with wrong arguments."""
        test_jwt = create_test_iap_jwt()
        invalid_jwt = validate_jwt(
            test_jwt, 'invalid', '1234')
        self.assertIsNone(invalid_jwt)
