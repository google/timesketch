# Copyright 2019 Google Inc. All rights reserved.
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
"""Timesketch API client library."""
from __future__ import unicode_literals

import json

import bs4

from . import definitions


def _get_message(response):
    """Return a formatted message string from the response text.

    Args:
        response (requests.Response): a response object from a HTTP
            request.

    Returns:
        str: a string with the message field extracted from the
            response.text.
    """
    soup = bs4.BeautifulSoup(response.text, features='html.parser')
    if soup.p:
        return soup.p.string

    if isinstance(response.text, bytes):
        response_text = response.text.decode('utf-8')
    else:
        response_text = response.text

    try:
        response_dict = json.loads(response_text)
    except json.JSONDecodeError:
        return response_text

    if not isinstance(response_dict, dict):
        return str(response_dict)

    return response_dict.get('message', str(response_dict))


def _get_reason(response):
    """Return the reason from a response.

    Args:
        response (requests.Response): a response object from a HTTP
            request.

    Returns:
        str: a string with the reason field extracted from the
            response.reason.
    """
    reason = response.reason
    if isinstance(reason, bytes):
        return reason.decode('utf-8')

    return reason


def get_response_json(response, logger):
    """Return the JSON object from a response, logging any errors.

    Args:
        response (requests.Response): a response object from a HTTP
            request.
        logger (logging.Logger): a logger object that can be used to
            write log messages.

    Returns:
        dict: a dict with the decoded JSON object within the HTTP
            response object.
    """
    status = response.status_code in definitions.HTTP_STATUS_CODE_20X
    if not status:
        reason = _get_reason(response)
        logger.warning('Failed response: [{0:d}] {2:s} {1:s}'.format(
            response.status_code, reason, _get_message(response)))

    try:
        return response.json()
    except json.JSONDecodeError as e:
        logger.error('Unable to decode response: {0!s}'.format(e))

    return {}


def error_message(response, message=None, error=RuntimeError):
    """Raise an error using error message extracted from response."""
    if not message:
        message = 'Unknown error, with error: '
    text = _get_message(response)

    raise error('{0:s}, with error [{1:d}] {2:s} {3:s}'.format(
        message, response.status_code, _get_reason(response), text))


def check_return_status(response, logger):
    """Check return status and return a boolean.

    Args:
        response (requests.Response): a response object from a HTTP
            request.
        logger (logging.Logger): a logger object that can be used to
            write log messages.

    Returns:
        bool: a boolean indicating whether the return status was in
            the 20X range of HTTP responses.
    """
    status = response.status_code in definitions.HTTP_STATUS_CODE_20X
    if status:
        return status

    logger.warning('Failed response: [{0:d}] {1:s}'.format(
        response.status_code, _get_message(response)))
    return status


class Error(Exception):
    """Base error class."""


class UnableToRunAnalyzer(Error):
    """Raised when unable to run an analyzer."""
