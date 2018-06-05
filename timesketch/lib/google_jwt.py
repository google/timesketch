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
import jwt
import json
import requests

from timesketch.lib.definitions import HTTP_STATUS_CODE_OK


class JwtValidationError(Exception):
    pass


class JwtKeyError(Exception):
    pass


def validate_jwt(encoded_jwt, public_key, algorithm, expected_audience,
                 expected_issuer, expected_domain=None):
    """Decode anb validate a JSON Web token (JWT).

    Cloud IAP:
    https://cloud.google.com/iap/docs/signed-headers-howto

    Google OpenID Connect:
    https://developers.google.com/identity/protocols/OpenIDConnect

    Args:
        encoded_jwt: The contents of the X-Goog-IAP-JWT-Assertion header.
        public_key: Key to verify signature of the JWT.
        algorithm: Algorithm used for the key. E.g. ES256, RS256
        expected_audience: Expected audience in the JWT.
        expected_issuer: Expected issuer of the JWT.
        expected_domain: Expected GSuite domain in the JWT (optional).

    Returns:
        Decoded JWT on successful validation.
    """
    # Decode the token and verify it's payload.
    try:
        decoded_jwt = jwt.decode(
            encoded_jwt, public_key, algorithm=algorithm,
            audience=expected_audience)

        # Make sure the token is not created in the future or has expired.
        try:
            now = int(time.time())
            issued_at = decoded_jwt['iat']
            expires_at = decoded_jwt['exp']
            if issued_at > now:
                raise JwtValidationError('Token was issued in the future')
            elif expires_at < now:
                raise JwtValidationError('Token has expired')
        except KeyError as e:
            raise JwtValidationError('Missing timestamp: {}'.format(e))

        # Check that the issuer of the token is correct.
        try:
            issuer = decoded_jwt['iss']
            if issuer != expected_issuer:
                raise JwtValidationError('Wrong issuer: {}'.format(issuer))
        except KeyError:
            raise JwtValidationError('Missing issuer')

        if 'email' not in decoded_jwt:
            raise JwtValidationError('Missing email field in token')

        if expected_domain:
            try:
                domain = decoded_jwt['hd']
                if not domain == expected_domain:
                    raise JwtValidationError('Wrong domain: {}'.format(domain))
            except KeyError as e:
                raise JwtValidationError('Missing domain: {}'.format(e))

        # If everything checks out, return the decoded token.
        return decoded_jwt

    except (jwt.exceptions.InvalidTokenError,
            jwt.exceptions.InvalidKeyError) as e:
        raise JwtValidationError('JWT validation error: {}'.format(e))


def fetch_public_keys(url):
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
        raise JwtKeyError('Cannot fetch public keys: {}'.format(e))
    if resp.status_code != HTTP_STATUS_CODE_OK:
        raise JwtKeyError(
            'Cannot fetch public keys: {}'.format(resp.status_code))
    return resp.json()


def get_public_key_for_jwt(encoded_jwt, url):
    """Get public key for JWT in order to verify the signature.

    The keys get's cached in order to limit the amount of network round trips.

    Args:
        encoded_jwt: Base64 encoded JWT.
        url: URL where keys can be fetched.

    Raises:
        JwTKeyError if keys cannot be fetched.

    Returns:
        Key as string.
    """
    # Get the Key ID from the JWT header.
    key_id = jwt.get_unverified_header(encoded_jwt).get('kid')
    if not key_id:
        raise JwtKeyError('Missing key ID field in token header')
    key_cache = get_public_key_for_jwt.key_cache
    key = key_cache.get(key_id)
    if not key:
        # Re-fetch the key file.
        keys_json = fetch_public_keys(url)
        if 'keys' in keys_json:
            _new_keys_dict = {}
            for key_dict in keys_json['keys']:
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(
                    json.dumps(key_dict))
                _new_keys_dict[key_dict['kid']] = public_key
            key_cache = _new_keys_dict
        else:
            key_cache = keys_json
        get_public_key_for_jwt.key_cache = key_cache
        key = key_cache.get(key_id)
        if not key:
            raise JwtKeyError('IAP public key {!r} not found'.format(key_id))
    return key


# Used to cache public keys.
get_public_key_for_jwt.key_cache = {}
