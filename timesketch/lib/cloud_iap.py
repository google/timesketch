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
import requests

from timesketch.lib.definitions import HTTP_STATUS_CODE_OK

IAP_PUBLIC_KEY_URL = 'https://www.gstatic.com/iap/verify/public_key'
VALID_JWT_ISSUER = 'https://cloud.google.com/iap'
JWT_ALGORITHM = 'ES256'


class JwtValidationError(Exception):
    pass


def validate_jwt(iap_jwt, cloud_project_number, cloud_backend_id):
    """Validate a Google Identity-Aware Proxy (IAP) JSON Web token (JWT).

    Documentation: https://cloud.google.com/iap/docs/signed-headers-howto

    Args:
        iap_jwt: The contents of the X-Goog-IAP-JWT-Assertion header.
        cloud_project_number: The project number for your Google Cloud project.
        cloud_backend_id: The ID of the Google Cloud backend service.

    Returns:
        Decoded JWT on successful validation.
    """

    audience = '/projects/{}/global/backendServices/{}'.format(
        cloud_project_number, cloud_backend_id)

    # What key to use for verifying the signature.
    key_id = jwt.get_unverified_header(iap_jwt).get('kid')
    if not key_id:
        raise JwtValidationError('No Key ID found')

    # Get the public key to verify the token signature.
    try:
        iap_public_key = get_iap_public_key(key_id)
    except Exception as e:
        raise JwtValidationError('{}'.format(e))

    # Finally try to decode the token and verify it's payload.
    try:
        decoded_jwt = jwt.decode(
            iap_jwt, iap_public_key, algorithm=JWT_ALGORITHM, audience=audience)

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
            if issuer != VALID_JWT_ISSUER:
                raise JwtValidationError('Wrong issuer: {}'.format(issuer))
        except KeyError:
            raise JwtValidationError('Missing issuer')

        # Bail out if email is missing.
        if 'email' not in decoded_jwt:
            raise JwtValidationError('Missing email field in token')

        # If everything checks out, return the decoded token.
        return decoded_jwt

    except (jwt.exceptions.InvalidTokenError,
            jwt.exceptions.InvalidKeyError) as e:
        raise JwtValidationError('JWT validation error: {}'.format(e))


def get_iap_public_key(key_id):
    """Retrieves a public key published by Identity-Aware Proxy.

    Args:
        key_id: The ID of the public key (part of an JWT).

    Returns:
        The public key used to sign the JWT.

    Raises:
        IapKeyException if key could not be fetched.
    """
    key_cache = get_iap_public_key.key_cache
    key = key_cache.get(key_id)
    if not key:
        # Re-fetch the key file.
        try:
            resp = requests.get(IAP_PUBLIC_KEY_URL)
        except requests.exceptions.RequestException as e:
            raise Exception('Unable to fetch IAP public key: {}'.format(e))

        if resp.status_code != HTTP_STATUS_CODE_OK:
            raise Exception(
                'Unable to fetch IAP public key: {} / {} / {}'.format(
                    resp.status_code, resp.headers, resp.text))

        key_cache = resp.json()
        get_iap_public_key.key_cache = key_cache
        key = key_cache.get(key_id)
        if not key:
            raise Exception('IAP public key {!r} not found'.format(key_id))
    return key


# Used to cache the Identity-Aware Proxy public keys.
get_iap_public_key.key_cache = {}
