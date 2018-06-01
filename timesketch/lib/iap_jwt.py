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

import jwt
import requests
from flask import current_app

from timesketch.lib.definitions import HTTP_STATUS_CODE_OK

GOOGLE_IAP_PUBLIC_KEY_URL = 'https://www.gstatic.com/iap/verify/public_key'


class IapKeyException(Exception):
    pass


def validate_iap_jwt(iap_jwt, cloud_project_number, backend_service_id):
    """Validate a Google Identity-Aware Proxy (IAP) JSON Web token (JWT).

    Args:
        iap_jwt: The contents of the X-Goog-IAP-JWT-Assertion header.
        cloud_project_number: The project number for your Google Cloud project.
        backend_service_id: The ID of the Google Cloud backend service.

    Returns:
        Decoded JWT on successful validation, None otherwise.
    """

    audience = '/projects/{}/global/backendServices/{}'.format(
        cloud_project_number, backend_service_id)

    key_id = jwt.get_unverified_header(iap_jwt).get('kid')
    if not key_id:
        current_app.logger.error('No Key ID found in JWT')
        return None

    try:
        iap_public_key = get_iap_public_key(key_id)
    except IapKeyException as e:
        current_app.logger.error('Error with IAP public key: {}'.format(e))
        return None

    try:
        decoded_jwt = jwt.decode(
            iap_jwt, iap_public_key, algorithms=['ES256'], audience=audience)
        return decoded_jwt
    except jwt.exceptions.InvalidTokenError as e:
        current_app.logger.error('JWT validation error: {}'.format(e))
        return None


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
        resp = requests.get(GOOGLE_IAP_PUBLIC_KEY_URL)
        if resp.status_code != HTTP_STATUS_CODE_OK:
            raise IapKeyException(
                'Unable to fetch IAP public key: {} / {} / {}'.format(
                    resp.status_code, resp.headers, resp.text))
        key_cache = resp.json()
        get_iap_public_key.key_cache = key_cache
        key = key_cache.get(key_id)
        if not key:
            raise IapKeyException(
                'IAP public key {!r} not found'.format(key_id))
    return key


# Used to cache the Identity-Aware Proxy public keys.
get_iap_public_key.key_cache = {}
