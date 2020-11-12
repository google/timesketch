# Copyright 2020 Google Inc. All rights reserved.
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
from __future__ import unicode_literals

import unittest
import tempfile
import mock
import json

# TODO remove config
from . import config
from . import sigma
from . import test_lib
from . import client



class TimesketchSigmaTest(unittest.TestCase):
    """Test Sigma."""

    @mock.patch('requests.Session', test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi(
            'http://127.0.0.1', 'test', 'test')
        self.rule = self.api_client.get_sigma_rule("5266a592-b793-11ea-b3de-0242ac130004")
        self.rules = self.api_client.list_sigma_rules()

    def test_sigma_rule(self):
        self.assertIsNotNone(True)
        self.assertIsNotNone(self.rule)

        data = json.loads(self.rule)
        self.assertEqual(data['title'], 'Suspicious Installation of Zenmap', "Title of the rule does not match") 

        