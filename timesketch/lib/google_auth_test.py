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

import time
import mock
import jwt

from cryptography.hazmat.primitives.asymmetric import rsa

from timesketch.lib.testlib import BaseTest
from timesketch.lib.google_auth import decode_jwt
from timesketch.lib.google_auth import validate_jwt
from timesketch.lib.google_auth import get_public_key_for_jwt
from timesketch.lib.google_auth import JwtValidationError
from timesketch.lib.google_auth import JwtKeyError


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

# pylint: disable=line-too-long
# Created with https://mkjwk.org/
MOCK_RSA_PRIVATE_PUBLIC_KEY_JWK = {
    "kty": "RSA",
    "d": "DlJPaEHlCOtPg2qIQ3sFYDJRG-JnHVaz4jJoICLP-BDyo6oVBqGuiia2TdZ1OM_1Df1PCk0sfFyacQw0i1Cno-b2ypZZrAgU5zH8tXiBoFSTu6xp2eeLLPeVKueigbR9Uf0NU3BZ2WcxHojq3T6pil1Au7bMzff0JIPXWcECcO4eLOAqPupYswKO8ebT-sl-wT_AtKqCCxAWKbbSpkgHXLNB7k5A-R7m-hiIK5rSQWoqJu-5SROYzCCADCiwRH5tXbaWLWvFFtiF5rl8VnHHRAPFSEG0iIe6-KlsOFdPA2qdiXgJ-Qb39vxOZ5g8qlCRTU7eshvMKs5dtyBtSTo4eQ",
    "e": "AQAB",
    "use": "sig",
    "kid": "oidc_1234",
    "alg": "RS256",
    "n": "jVUkmrTXhFmaahZExVcdJqb3BqZp2A6Kk-IFkmeLimK2DJg3OpUSxEJ5mlaymu7XQJUlG2qKI7zhL7WV-S9CNYdLCVWMhg_XQ9dKB9VoYf92eAufkGrl2GbGd0y6KdMrTuxGfESC-l-exTcQAPvn1Md95difnruob6K1KXQTqEqQEFhKLiciFtssyiC90r8ia7-082MSJUXpXNhHyyuehuV5Xs5GCVqZfP65MMiDiKidUxq40UNTodqJCzhum7iSK42SF9la7ao0FTizF1uFl7oU7fIbN2qzNBgn5U3CTfaZaII54Xn6pzoIwinYXCZzeTy7x-8ZIN41VDNGulTK_w",
}

# pylint: disable=line-too-long
MOCK_RSA_PUBLIC_KEY_JWK = {
    "kty": "RSA",
    "e": "AQAB",
    "use": "sig",
    "kid": "oidc_1234",
    "alg": "RS256",
    "n": "jVUkmrTXhFmaahZExVcdJqb3BqZp2A6Kk-IFkmeLimK2DJg3OpUSxEJ5mlaymu7XQJUlG2qKI7zhL7WV-S9CNYdLCVWMhg_XQ9dKB9VoYf92eAufkGrl2GbGd0y6KdMrTuxGfESC-l-exTcQAPvn1Md95difnruob6K1KXQTqEqQEFhKLiciFtssyiC90r8ia7-082MSJUXpXNhHyyuehuV5Xs5GCVqZfP65MMiDiKidUxq40UNTodqJCzhum7iSK42SF9la7ao0FTizF1uFl7oU7fIbN2qzNBgn5U3CTfaZaII54Xn6pzoIwinYXCZzeTy7x-8ZIN41VDNGulTK_w",
}

# pylint: disable=line-too-long
MOCK_INVALID_RSA_PUBLIC_KEY_JWK = {
    "kty": "RSA",
    "e": "AQAB",
    "use": "sig",
    "kid": "invalid_oidc_1234",
    "alg": "RS256",
    "n": "tQjrbztEuU3GFrNzgxCyb2lAeMXBQPsMctyaQAx05JLiqIxWYE__oSgMXyGz9SR7F_cCZ-x0FVQO1UjIyHU1BUPQxlO88NwEXlIrP5Eo_dnKzn972Cl4AjmoISApp2dTlwhSkHRqycOxJApzsqsg2HQxbrtM6oZrOyFU3uc2u0PHJqVAO6W7fplZXRHRGMd7KaT2a4GJ8zfNHD157Mv7ttjCeQ7rmqkB6OLVpNzO8idKo33gz5gDID2f7IGIPlqpAOAZaaKkRlGqUoaG0EZHns3fPcl27AvNOvmvOl9Blb43UnbBIBFGm6MY9aJUEJzmqcX-td9mch5HtGG14v3sUQ",
}

# Converted to PEM format with pem-jwk (npm install -g pem-jwk)
MOCK_RSA_PRIVATE_KEY_PEM = """
-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAjVUkmrTXhFmaahZExVcdJqb3BqZp2A6Kk+IFkmeLimK2DJg3
OpUSxEJ5mlaymu7XQJUlG2qKI7zhL7WV+S9CNYdLCVWMhg/XQ9dKB9VoYf92eAuf
kGrl2GbGd0y6KdMrTuxGfESC+l+exTcQAPvn1Md95difnruob6K1KXQTqEqQEFhK
LiciFtssyiC90r8ia7+082MSJUXpXNhHyyuehuV5Xs5GCVqZfP65MMiDiKidUxq4
0UNTodqJCzhum7iSK42SF9la7ao0FTizF1uFl7oU7fIbN2qzNBgn5U3CTfaZaII5
4Xn6pzoIwinYXCZzeTy7x+8ZIN41VDNGulTK/wIDAQABAoIBAA5ST2hB5QjrT4Nq
iEN7BWAyURviZx1Ws+IyaCAiz/gQ8qOqFQahroomtk3WdTjP9Q39TwpNLHxcmnEM
NItQp6Pm9sqWWawIFOcx/LV4gaBUk7usadnniyz3lSrnooG0fVH9DVNwWdlnMR6I
6t0+qYpdQLu2zM339CSD11nBAnDuHizgKj7qWLMCjvHm0/rJfsE/wLSqggsQFim2
0qZIB1yzQe5OQPke5voYiCua0kFqKibvuUkTmMwggAwosER+bV22li1rxRbYhea5
fFZxx0QDxUhBtIiHuvipbDhXTwNqnYl4CfkG9/b8TmeYPKpQkU1O3rIbzCrOXbcg
bUk6OHkCgYEA4xl4WfVqFEfrvmD+KSU3KTZxRSCof8AFOfmrmJPYqocxDw9JaFPH
7fxFEP/8BnxDBcnW+ikGB8VfWNrm40LAme7TD1Ogva9ddWlE/nnOacPWX4ep00e9
ErwIYLlvOjreH5J3PBGqNDVjavO+kREKKUqXDXY7m55OY5dEPckMLhsCgYEAn1GH
CoIwXfms7+CHPDld0bS6VecJGy6MJ3kvrVyc3Toopygnafj12epKKiusExu5EOH4
JIxfm/m6XMOLixIXAa0ZWBfVrek9Bt0CWf2l3jJeyD+oRk7h9Mw8dc4FpP8acZVg
AyD/MKW2zIfjp7hi4v4vagz9JUm4i3vbyIqcFO0CgYEA1BWxQ7Hhg1c3XfAO7DYJ
Mb/aQIijU8rsFpyIGFHagkcHFd1c3MWBbUuu5JVrtFLP9NPupGkzbIZy6PRls89f
N2LGUQX0k7D2QvQwrsbqcfOmfEih3OKePKTF3i7PJT5cund6SurkXSWO1w8S5T9Y
kf9K2hOUz1wkMPXPkTP04AkCgYAnPGDRibZ3rmGUwesMPeSJHMU3Gqr3csM5hXLk
cwZ+xS/12sG6K4IApN6W/CJook81hTEjbx6svxfSeKYJHe9kjkjLlTMenW5WHl/R
4dHTovwMvQCoMA0dyJ6rNI3XUKwmhO8cVigCxwz52g2K5LIVzRvINmKxqDI2x84c
2WYPEQKBgAU26m/CfLEANjrN2gHVXaBA6uKnUnyQBl99PXH/HOJ7g8o8OXJVJIDe
taxXqti9HRcj+oSgKNlL4A4W7pUmDh5sv6tHIx16MVoJO++2CjQN8V+m9DjPlgEx
+UVmw9npr/ilfWf3MnrUdl/MefdPUDZQ9rMIaDvX3VFA9H1KsJqv
-----END RSA PRIVATE KEY-----
"""

IAP_VALID_AUDIENCE = "/projects/1234/global/backendServices/1234"
IAP_INVALID_AUDIENCE = "/projects/foo/global/backendServices/bar"

OIDC_CLIENT_ID = "123456"
OIDC_VALID_AUDIENCE = OIDC_CLIENT_ID

# Defaults for Google Cloud Identity-Aware Proxy
IAP_PUBLIC_KEY_URL = "https://www.gstatic.com/iap/verify/public_key"
IAP_VALID_ISSUER = "https://cloud.google.com/iap"
IAP_JWT_ALGORITHM = "ES256"

# Defaults for Google OAuth/OpenID Connect
OIDC_PUBLIC_KEY_URL = "https://www.googleapis.com/oauth2/v3/certs"
OIDC_VALID_ISSUER = "https://accounts.google.com"
OIDC_JWT_ALGORITHM = "RS256"


# pylint: disable=unused-argument
def mock_fetch_iap_public_keys(unused_argument):
    """Mock getting public keys.

    Returns:
        Mock public key.
    """
    return {"iap_1234": MOCK_EC_PUBLIC_KEY}


# pylint: disable=unused-argument
def mock_fetch_oidc_public_keys(unused_argument):
    """Mock getting public keys.

    Returns:
        Mock public key.
    """
    return {"keys": [MOCK_RSA_PUBLIC_KEY_JWK]}


def create_default_payload(audience, issuer):
    now = int(time.time())
    payload = {
        "sub": "1234567890",
        "email": "test@example.com",
        "hd": "example.com",
        "iat": now - 300,  # issued 5 min ago
        "exp": now + 300,  # expires in 5 min
        "aud": audience,
        "iss": issuer,
    }
    return payload


def create_default_header(algorithm, key_id):
    header = {"alg": algorithm, "kid": key_id}
    return header


def create_mock_jwt(
    key, algorithm, key_id, audience, issuer, header=None, payload=None
):
    """Create test JSON Web Token (JWT).

    Args:
        key: Private key for signing.
        algorithm: Algorithm used for the private key.
        key_id: Key ID for the public key.
        header: Dict with optional header.
        payload: Dict with optional payload.

    Returns:
        Encoded JWT signed with key.
    """
    if not header:
        header = create_default_header(algorithm=algorithm, key_id=key_id)

    if not payload:
        payload = create_default_payload(audience, issuer)

    return jwt.encode(payload, key, algorithm=algorithm, headers=header)


@mock.patch("timesketch.lib.google_auth._fetch_public_keys", mock_fetch_iap_public_keys)
class TestGoogleCloudIAP(BaseTest):
    """Tests for the functionality of the google_auth module."""

    def _test_payload_raises_jwt_validation_error(self, payload, domain=None):
        """Test JWT with supplied payload."""
        test_jwt = create_mock_jwt(
            MOCK_EC_PRIVATE_KEY,
            algorithm=IAP_JWT_ALGORITHM,
            key_id="iap_1234",
            audience=IAP_VALID_AUDIENCE,
            issuer=IAP_VALID_ISSUER,
            payload=payload,
        )
        public_key = get_public_key_for_jwt(test_jwt, IAP_PUBLIC_KEY_URL)
        with self.assertRaises(JwtValidationError):
            test_decoded_jwt = decode_jwt(
                test_jwt, public_key, IAP_JWT_ALGORITHM, IAP_VALID_AUDIENCE
            )
            validate_jwt(test_decoded_jwt, IAP_VALID_ISSUER, domain)

    def _test_header_raises_jwt_validation_error(self, header):
        """Test JWT with supplied header."""
        test_jwt = create_mock_jwt(
            MOCK_EC_PRIVATE_KEY,
            algorithm=IAP_JWT_ALGORITHM,
            key_id="iap_1234",
            audience=IAP_VALID_AUDIENCE,
            issuer=IAP_VALID_ISSUER,
            header=header,
        )
        public_key = get_public_key_for_jwt(test_jwt, IAP_PUBLIC_KEY_URL)

        with self.assertRaises(JwtValidationError):
            test_decoded_jwt = decode_jwt(
                test_jwt, public_key, IAP_JWT_ALGORITHM, IAP_VALID_AUDIENCE
            )
            validate_jwt(test_decoded_jwt, IAP_VALID_ISSUER)

    def test_valid_jwt(self):
        """Test to validate a valid JWT."""
        test_jwt = create_mock_jwt(
            MOCK_EC_PRIVATE_KEY,
            algorithm=IAP_JWT_ALGORITHM,
            key_id="iap_1234",
            audience=IAP_VALID_AUDIENCE,
            issuer=IAP_VALID_ISSUER,
        )
        public_key = get_public_key_for_jwt(test_jwt, IAP_PUBLIC_KEY_URL)
        test_decoded_jwt = decode_jwt(
            test_jwt, public_key, IAP_JWT_ALGORITHM, IAP_VALID_AUDIENCE
        )
        validate_jwt(test_decoded_jwt, IAP_VALID_ISSUER)
        self.assertIsInstance(test_decoded_jwt, dict)
        self.assertEqual(test_decoded_jwt.get("email"), "test@example.com")

    def test_invalid_audience_raises_jwt_validation_error(self):
        """Test to validate a JWT with wrong audience."""
        test_jwt = create_mock_jwt(
            MOCK_EC_PRIVATE_KEY,
            algorithm=IAP_JWT_ALGORITHM,
            key_id="iap_1234",
            audience=IAP_VALID_AUDIENCE,
            issuer=IAP_VALID_ISSUER,
        )
        public_key = get_public_key_for_jwt(test_jwt, IAP_PUBLIC_KEY_URL)
        self.assertRaises(
            JwtValidationError,
            decode_jwt,
            test_jwt,
            public_key,
            IAP_JWT_ALGORITHM,
            IAP_INVALID_AUDIENCE,
        )

    def test_invalid_algorithm_raises_jwt_validation_error(self):
        """Test to validate a JWT with invalid algorithm."""

        # Hard coding a JWT with MOCK_EC_PRIVATE_KEY as key and "HS256" as alg
        # in the header. Newer versions of PyJWT won't encode JWTs with this
        # configuration.
        test_jwt = (
            b"eyJ0eXAiOiJKV1QiLCJhbGciOiJFUzI1NiIsImtpZCI6ImlhcF8xMjM0In0.eyJzd"
            b"WIiOiIxMjM0NTY3ODkwIiwiZW1haWwiOiJ0ZXN0QGV4YW1wbGUuY29tIiwiaGQiOi"
            b"JleGFtcGxlLmNvbSIsImlhdCI6MTY1NzU5NDE4NSwiZXhwIjoxNjU3NTk0Nzg1LCJ"
            b"hdWQiOiIvcHJvamVjdHMvMTIzNC9nbG9iYWwvYmFja2VuZFNlcnZpY2VzLzEyMzQi"
            b"LCJpc3MiOiJodHRwczovL2Nsb3VkLmdvb2dsZS5jb20vaWFwIn0.s49RJ_Fhoaqpo"
            b"GHfXTjEi5Ma373Zr69BU8rG3ZObNq0EJJXGgBq4E48LwaD_WMR4z3dMxv-UkcShmU"
            b"3p6qnv7w"
        )

        public_key = get_public_key_for_jwt(test_jwt, IAP_PUBLIC_KEY_URL)

        with self.assertRaises(JwtValidationError):
            test_decoded_jwt = decode_jwt(
                test_jwt, public_key, IAP_JWT_ALGORITHM, IAP_VALID_AUDIENCE
            )
            validate_jwt(test_decoded_jwt, IAP_VALID_ISSUER)

    def test_missing_key_id_raises_jwt_key_error(self):
        """Test to validate a JWT with key ID missing."""
        header = create_default_header(IAP_JWT_ALGORITHM, "iap_1234")
        del header["kid"]
        test_jwt = create_mock_jwt(
            MOCK_EC_PRIVATE_KEY,
            algorithm=IAP_JWT_ALGORITHM,
            key_id="iap_1234",
            audience=IAP_VALID_AUDIENCE,
            issuer=IAP_VALID_ISSUER,
            header=header,
        )
        self.assertRaises(
            JwtKeyError, get_public_key_for_jwt, test_jwt, IAP_PUBLIC_KEY_URL
        )

    def test_missing_email_raises_jwt_validation_error(self):
        """Test to validate a JWT with email missing."""
        payload = create_default_payload(IAP_VALID_AUDIENCE, IAP_VALID_ISSUER)
        del payload["email"]
        self._test_payload_raises_jwt_validation_error(payload)

    def test_missing_issuer_raises_jwt_validation_error(self):
        """Test to validate a JWT with issuer missing."""
        payload = create_default_payload(IAP_VALID_AUDIENCE, IAP_VALID_ISSUER)
        del payload["iss"]
        self._test_payload_raises_jwt_validation_error(payload)

    def test_invalid_issuer_raises_jwt_validation_error(self):
        """Test to validate a JWT with invalid issuer"""
        payload = create_default_payload(IAP_VALID_AUDIENCE, "invalid_issuer")
        self._test_payload_raises_jwt_validation_error(payload)

    def test_issued_in_the_future_raises_jwt_validation_error(self):
        """Test to validate a JWT created in the future."""
        payload = create_default_payload(IAP_VALID_AUDIENCE, IAP_VALID_ISSUER)
        payload["iat"] = payload["iat"] + 600  # seconds
        self._test_payload_raises_jwt_validation_error(payload)

    def test_expired_jwt_raises_jwt_validation_error(self):
        """Test to validate an expired JWT."""
        payload = create_default_payload(IAP_VALID_AUDIENCE, IAP_VALID_ISSUER)
        payload["exp"] = payload["exp"] - 600  # seconds
        self._test_payload_raises_jwt_validation_error(payload)

    def test_valid_domain(self):
        """Test to validate a JWT with domain."""
        valid_domain = "example.com"
        test_jwt = create_mock_jwt(
            MOCK_EC_PRIVATE_KEY,
            algorithm=IAP_JWT_ALGORITHM,
            key_id="iap_1234",
            audience=IAP_VALID_AUDIENCE,
            issuer=IAP_VALID_ISSUER,
        )
        public_key = get_public_key_for_jwt(test_jwt, IAP_PUBLIC_KEY_URL)
        test_decoded_jwt = decode_jwt(
            test_jwt, public_key, IAP_JWT_ALGORITHM, IAP_VALID_AUDIENCE
        )
        validate_jwt(test_decoded_jwt, IAP_VALID_ISSUER, valid_domain)
        self.assertIsInstance(test_decoded_jwt, dict)
        self.assertEqual(test_decoded_jwt.get("hd"), "example.com")

    def test_invalid_domain_raises_jwt_validation_error(self):
        """Test to validate a JWT with an invalid domain."""
        invalid_domain = "foobar.com"
        payload = create_default_payload(IAP_VALID_AUDIENCE, IAP_VALID_ISSUER)
        self._test_payload_raises_jwt_validation_error(payload, domain=invalid_domain)

    def test_invalid_public_key_raises_jwt_validation_error(self):
        """Test to validate a JWT with wrong public key."""
        test_jwt = create_mock_jwt(
            MOCK_EC_PRIVATE_KEY,
            algorithm=IAP_JWT_ALGORITHM,
            key_id="iap_1234",
            audience=IAP_VALID_AUDIENCE,
            issuer=IAP_VALID_ISSUER,
        )
        self.assertRaises(
            JwtValidationError,
            decode_jwt,
            test_jwt,
            MOCK_INVALID_EC_PUBLIC_KEY,
            IAP_JWT_ALGORITHM,
            IAP_VALID_AUDIENCE,
        )


@mock.patch(
    "timesketch.lib.google_auth._fetch_public_keys", mock_fetch_oidc_public_keys
)
class TestGoogleCloudOpenIdConnect(BaseTest):
    """Tests for the functionality of the google_auth module."""

    def test_fetching_oidc_keys(self):
        """Test to fetch OpenID Connect formatted keys."""
        test_jwt = create_mock_jwt(
            MOCK_RSA_PRIVATE_KEY_PEM,
            algorithm=OIDC_JWT_ALGORITHM,
            key_id="oidc_1234",
            audience=OIDC_VALID_AUDIENCE,
            issuer=OIDC_VALID_ISSUER,
        )
        public_key = get_public_key_for_jwt(test_jwt, OIDC_PUBLIC_KEY_URL)
        self.assertIsInstance(public_key, rsa.RSAPublicKey)

    def test_valid_oidc_jwt(self):
        """Test to validate a valid OpenID Connect JWT."""
        test_jwt = create_mock_jwt(
            MOCK_RSA_PRIVATE_KEY_PEM,
            algorithm=OIDC_JWT_ALGORITHM,
            key_id="oidc_1234",
            audience=OIDC_VALID_AUDIENCE,
            issuer=OIDC_VALID_ISSUER,
        )
        public_key = get_public_key_for_jwt(test_jwt, OIDC_PUBLIC_KEY_URL)
        test_decoded_jwt = decode_jwt(
            test_jwt, public_key, OIDC_JWT_ALGORITHM, OIDC_VALID_AUDIENCE
        )
        validate_jwt(test_decoded_jwt, OIDC_VALID_ISSUER)

        self.assertIsInstance(test_decoded_jwt, dict)
        self.assertEqual(test_decoded_jwt.get("email"), "test@example.com")
