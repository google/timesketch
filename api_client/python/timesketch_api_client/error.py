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


def error_message(response, message=None, error=RuntimeError):
    """Raise an error using error message extracted from response."""
    if not message:
        message = 'Unknown error, with error: '
    soup = bs4.BeautifulSoup(response.text, features='html.parser')
    text = ''
    if soup.p:
        text = soup.p.string
    else:
        try:
            response_dict = json.loads(response.text)
            text = response_dict.get('message', 'Unable to get message')
        except (json.JSONDecodeError, AttributeError):
            text = str(response.text)
    raise error('{0:s}, with error [{1:d}] {2!s} {3:s}'.format(
        message, response.status_code, response.reason, text))


class Error(Exception):
    """Base error class."""


class UnableToRunAnalyzer(Error):
    """Raised when unable to run an analyzer."""
