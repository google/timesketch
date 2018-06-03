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
import time
import jwt

from timesketch.lib.testlib import BaseTest
from timesketch.lib.cloud_iap import validate_jwt
from timesketch.lib.cloud_iap import JwtValidationError
from timesketch.lib.cloud_iap import VALID_JWT_ISSUER
from timesketch.lib.cloud_iap import JWT_ALGORITHM


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

MOCK_INVALID_EC_PUBLIC_KEY = """
-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE45WYklVqGutB1h/v0FFOtjeACMA0
62e1qPRxoXqi/vREEDnRdkjAq0SlS+pGFVeZq89NUFYwfMBIySF0ShppPg==
-----END PUBLIC KEY-----
"""


# pylint: disable=unused-argument
def mock_get_iap_public_key(unused_argument):
    """Mock getting key from Google IAP service.

    Returns:
        Mock public key.
    """
    return MOCK_EC_PUBLIC_KEY


# pylint: disable=unused-argument
def mock_get_invalid_iap_public_key(unused_argument):
    """Mock getting key from Google IAP service.

    Returns:
        Mock public key.
    """
    return MOCK_INVALID_EC_PUBLIC_KEY


def create_default_payload():
    now = int(time.time())
    payload = {
        "sub": "1234567890",
        "email": "test@example.com",
        "iat": now - 300,  # issued 5 min ago
        "exp": now + 300,  # expires in 5 min
        "aud": "/projects/1234/global/backendServices/1234",
        "iss": VALID_JWT_ISSUER
    }
    return payload


def create_default_header():
    header = {
        "alg": JWT_ALGORITHM,
        "kid": "test"
    }
    return header


def create_test_iap_jwt(header=None, payload=None):
    """Create test JSON Web Token (JWT).

    Returns:
        Encoded JWT signed with key.
    """
    if not header:
        header = create_default_header()

    if not payload:
        payload = create_default_payload()

    return jwt.encode(
        payload, MOCK_EC_PRIVATE_KEY, algorithm=JWT_ALGORITHM, headers=header)


@mock.patch(
    u'timesketch.lib.cloud_iap.get_iap_public_key', mock_get_iap_public_key)
class TestCloudIap(BaseTest):
    """Tests for the functionality of the cloud_iap module."""

    def _test_payload(self, payload):
        """Test JWT with supplied payload."""
        test_jwt = create_test_iap_jwt(payload=payload)
        self.assertRaises(
            JwtValidationError, validate_jwt, test_jwt, '1234', '1234')

    def _test_header(self, header):
        """Test JWT with supplied header."""
        test_jwt = create_test_iap_jwt(header=header)
        self.assertRaises(
            JwtValidationError, validate_jwt, test_jwt, '1234', '1234')

    def test_valid_jwt(self):
        """Test to validate a valid JWT."""
        test_jwt = create_test_iap_jwt()
        valid_jwt = validate_jwt(test_jwt, '1234', '1234')
        self.assertIsInstance(valid_jwt, dict)
        self.assertEqual(valid_jwt.get('email'), 'test@example.com')

    def test_invalid_cloud_project_number(self):
        """Test to validate a JWT with wrong cloud project number."""
        test_jwt = create_test_iap_jwt()
        self.assertRaises(
            JwtValidationError, validate_jwt, test_jwt, 'invalid', '1234')

    def test_invalid_cloud_backend_id(self):
        """Test to validate JWT with wrong cloud backend ID."""
        test_jwt = create_test_iap_jwt()
        self.assertRaises(
            JwtValidationError, validate_jwt, test_jwt, '1234', 'invalid')

    def test_invalid_algorithm(self):
        """Test to validate a JWT with invalid algorithm."""
        header = create_default_header()
        header['alg'] = 'HS256'
        self._test_header(header)

    def test_missing_key_id(self):
        """Test to validate a JWT with key ID missing."""
        header = create_default_header()
        del header['kid']
        self._test_header(header)

    def test_missing_email(self):
        """Test to validate a JWT with email missing."""
        payload = create_default_payload()
        del payload['email']
        self._test_payload(payload)

    def test_missing_issuer(self):
        """Test to validate a JWT with issuer missing."""
        payload = create_default_payload()
        del payload['iss']
        self._test_payload(payload)

    def test_invalid_issuer(self):
        """Test to validate a JWT with invalid issuer"""
        payload = create_default_payload()
        payload['iss'] = 'invalid'
        self._test_payload(payload)

    def test_issued_in_the_future(self):
        """Test to validate a JWT created in the future."""
        payload = create_default_payload()
        payload['iat'] = payload['iat'] + 600  # seconds
        self._test_payload(payload)

    def test_expired_jwt(self):
        """Test to validate an expired JWT."""
        payload = create_default_payload()
        payload['exp'] = payload['exp'] - 600  # seconds
        self._test_payload(payload)


@mock.patch(
    u'timesketch.lib.cloud_iap.get_iap_public_key',
    mock_get_invalid_iap_public_key)
class TestInvalidKeyCloudIap(BaseTest):
    """Tests for the functionality of the cloud_iap module."""
    def test_valid_jwt_with_wrong_public_key(self):
        """Test to validate a JWT with wrong public key."""
        test_jwt = create_test_iap_jwt()
        self.assertRaises(
            JwtValidationError, validate_jwt, test_jwt, '1234', '1234')
