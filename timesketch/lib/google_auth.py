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
"""
Based on the example code from the public Google IAP documentation:
https://cloud.google.com/iap/docs/signed-headers-howto
"""

from __future__ import unicode_literals

import time
import json
import hashlib
import os
import six

# six.moves is a dynamically-created namespace that doesn't actually
# exist and therefore pylint can't statically analyze it.
# pylint: disable-msg=import-error
from six.moves.urllib import parse as urlparse

import jwt
import requests

from flask import url_for
from flask import current_app
from flask import session

from timesketch.lib.definitions import HTTP_STATUS_CODE_OK

CSRF_KEY = "google_oauth2_csrf_token"
AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"


class JwtValidationError(Exception):
    """Raised when a JSON Web Token cannot be validated."""


class JwtKeyError(Exception):
    """Raised when there is a problem with the public key used for signing."""


class JwtFetchError(Exception):
    """Raised when there is a problem with the public key used for signing."""


class DiscoveryDocumentError(Exception):
    """Raised when there is a problem with the discovery document."""


def _fetch_public_keys(url):
    """Fetch public keys used for verifying signatures.

    Args:
        url: URL where keys can be fetched.

    Raises:
        JwTKeyError if keys cannot be fetched.

    Returns:
        HTTP response.
    """
    try:
        resp = requests.get(url)
    except requests.exceptions.RequestException as e:
        raise JwtKeyError("Cannot fetch public keys: {}".format(e)) from e
    if resp.status_code != HTTP_STATUS_CODE_OK:
        raise JwtKeyError("Cannot fetch public keys: {}".format(resp.status_code))
    return resp.json()


def _fetch_oauth2_discovery_document():
    """Fetch Google OAuth2 discovery document.

    Raises:
        DiscoveryDocumentError if document cannot be fetched.

    Returns:
        HTTP response.
    """
    discovery_url = current_app.config.get("GOOGLE_OIDC_DISCOVERY_URL", DISCOVERY_URL)
    try:
        resp = requests.get(discovery_url)
    except requests.exceptions.RequestException as e:
        raise DiscoveryDocumentError(
            "Cannot fetch discovery document: {}".format(e)
        ) from e
    if resp.status_code != HTTP_STATUS_CODE_OK:
        raise DiscoveryDocumentError(
            "Cannot fetch discovery_document: {}".format(resp.status_code)
        )
    return resp.json()


def _generate_random_token():
    """Generate random string to use as CSRF and nonce tokens.

    Returns:
        Random string.
    """
    return hashlib.sha256(os.urandom(1024)).hexdigest()


def get_oauth2_authorize_url(hosted_domain=None):
    """Generate an authorization URL for Google's OAuth2 service.

    Args:
        hosted_domain: Optional GSuite domain to limit access to.

    Returns:
        Authorization URL.
    """
    auth_uri = current_app.config.get("GOOGLE_OIDC_AUTH_URL", AUTH_URI)
    csrf_token = _generate_random_token()
    nonce = _generate_random_token()
    redirect_uri = url_for(
        "user_views.google_openid_connect", _scheme="https", _external=True
    )
    scopes = ("openid", "email", "profile")

    # Add the generated CSRF token to the client session for later validation.
    session[CSRF_KEY] = csrf_token

    # Generate authorization URL
    params = dict(
        client_id=current_app.config.get("GOOGLE_OIDC_CLIENT_ID"),
        scope=" ".join(scopes),
        response_type="code",
        access_type="online",  # Because we don't need a refresh token.
        state=csrf_token,
        nonce=nonce,  # Enable replay attack protection attack.
        redirect_uri=redirect_uri,
    )
    if hosted_domain:
        params["hd"] = hosted_domain

    urlencoded_params = urlparse.urlencode(params)
    google_authorization_url = "{}?{}".format(auth_uri, urlencoded_params)
    return google_authorization_url


def get_encoded_jwt_over_https(code):
    """Fetch a JSON Web Token (JWT) using a authentication code.

    Args:
        code: Authentication code obtained from an OAuth2 flow.

    Raises:
        JwtFetchError if JWT cannot be fetched.

    Returns:
        Encoded JWT.
    """

    discovery_document = get_oauth2_discovery_document()
    redirect_uri = url_for(
        "user_views.google_openid_connect", _scheme="https", _external=True
    )
    post_data = {
        "code": code,
        "client_id": current_app.config.get("GOOGLE_OIDC_CLIENT_ID"),
        "client_secret": current_app.config.get("GOOGLE_OIDC_CLIENT_SECRET"),
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    token_url = discovery_document.get("token_endpoint")
    try:
        response = requests.post(token_url, data=post_data)
        encoded_jwt = response.json().get("id_token")
    except requests.exceptions.RequestException as e:
        raise JwtFetchError("Cannot fetch JWT: {}".format(e)) from e
    if response.status_code != HTTP_STATUS_CODE_OK:
        raise JwtFetchError("Cannot fetch JWT: {}".format(response.status_code))

    if not encoded_jwt:
        raise JwtFetchError("Cannot fetch JWT: Missing id_token in response")

    return encoded_jwt


def decode_jwt(encoded_jwt, public_key, algorithm, expected_audience):
    """Decode a JSON Web Token (JWT).

    Args:
        encoded_jwt: The contents of the X-Goog-IAP-JWT-Assertion header.
        public_key: Key to verify signature of the JWT.
        algorithm: Algorithm used for the key. E.g. ES256, RS256. If the
            GOOGLE_OIDC_ALGORITHM is set in the config, it will overwrite
            the algorithm used here.
        expected_audience: Expected audience in the JWT.

    Returns:
        Decoded JWT as a dict object.

    Raises:
        JwtValidationError: if the JWT token cannot be decoded.
    """
    chosen_algorithm = current_app.config.get("GOOGLE_OIDC_ALGORITHM", algorithm)
    try:
        decoded_jwt = jwt.decode(
            jwt=encoded_jwt,
            key=public_key,
            algorithms=[chosen_algorithm],
            audience=expected_audience,
        )
        return decoded_jwt
    except (jwt.exceptions.InvalidTokenError, jwt.exceptions.InvalidKeyError) as e:
        raise JwtValidationError("JWT validation error: {}".format(e)) from e

    return None


def validate_jwt(decoded_jwt, expected_issuer, expected_domain=None):
    """Decode and validate a JSON Web token (JWT).

    Cloud IAP:
    https://cloud.google.com/iap/docs/signed-headers-howto

    Google OpenID Connect:
    https://developers.google.com/identity/protocols/OpenIDConnect

    Args:
        decoded_jwt: A dict object containing the decoded JWT token.
        expected_issuer: Expected issuer of the JWT.
        expected_domain: Expected GSuite domain in the JWT (optional).

    Raises:
        JwtValidationError: If unable to validate the JWT.
    """
    # Make sure the token is not created in the future or has expired.
    try:
        now = int(time.time())
        issued_at = decoded_jwt["iat"]
        if isinstance(issued_at, six.string_types):
            issued_at = int(issued_at, 10)

        expires_at = decoded_jwt["exp"]
        if isinstance(expires_at, six.string_types):
            expires_at = int(expires_at, 10)

        if issued_at > now:
            raise JwtValidationError("Token was issued in the future")
        if expires_at < now:
            raise JwtValidationError("Token has expired")
    except KeyError as e:
        raise JwtValidationError("Missing timestamp: {}".format(e)) from e

    # Check that the issuer of the token is correct.
    try:
        issuer = decoded_jwt["iss"]
        if issuer != expected_issuer:
            raise JwtValidationError("Wrong issuer: {}".format(issuer))
    except KeyError as e:
        raise JwtValidationError("Missing issuer") from e

    if "email" not in decoded_jwt:
        raise JwtValidationError("Missing email field in token")

    if expected_domain:
        try:
            domain = decoded_jwt["hd"]
            if not domain == expected_domain:
                raise JwtValidationError("Wrong domain: {}".format(domain))
        except KeyError as e:
            raise JwtValidationError("Missing domain: {}".format(e)) from e


def get_public_key_for_jwt(encoded_jwt, url):
    """Get public key for JWT in order to verify the signature.

    The keys get cached in order to limit the amount of network round trips.

    Args:
        encoded_jwt: Base64 encoded JWT.
        url: URL where keys can be fetched.

    Raises:
        JwTKeyError if keys cannot be fetched.

    Returns:
        Key as string.
    """
    # Get the Key ID from the JWT header.
    key_id = jwt.get_unverified_header(encoded_jwt).get("kid")
    if not key_id:
        raise JwtKeyError("Missing key ID field in token header")
    key_cache = get_public_key_for_jwt.key_cache
    key = key_cache.get(key_id)
    if key:
        return key

    # Re-fetch the key file.
    keys_json = _fetch_public_keys(url)
    if "keys" in keys_json:
        _new_keys_dict = {}
        for key_dict in keys_json["keys"]:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(key_dict))
            _new_keys_dict[key_dict["kid"]] = public_key
        key_cache = _new_keys_dict
    else:
        key_cache = keys_json
    get_public_key_for_jwt.key_cache = key_cache
    key = key_cache.get(key_id)
    if not key:
        raise JwtKeyError("IAP public key {!r} not found".format(key_id))

    return key


def get_oauth2_discovery_document():
    """Get Google OAuth2 discovery document.

    The document is cached in order to limit the amount of network round trips
    and is set to expire in 12 hours from when it was fetched.

    Returns:
        Discovery document as a dictionary.
    """
    now = int(time.time())
    cache = get_oauth2_discovery_document.cache
    discovery_document = cache.get("current")
    if discovery_document:
        # Check if the document has expired.
        created_at = discovery_document["created_at"]
        expires_at = created_at + 12 * 60 * 60  # 12 hours in seconds
        if now < expires_at:
            return discovery_document["document"]

    # Re-fetch the discovery document.
    new_discovery_document = _fetch_oauth2_discovery_document()
    cache = {"current": {"created_at": now, "document": new_discovery_document}}
    get_oauth2_discovery_document.cache = cache
    return new_discovery_document


# Used to cache public keys.
get_public_key_for_jwt.key_cache = {}

# Used to cache discovery documents.
get_oauth2_discovery_document.cache = {}
