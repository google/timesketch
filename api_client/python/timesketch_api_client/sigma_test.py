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
"""Tests for the Timesketch API client"""
from __future__ import unicode_literals

import unittest
import mock

from . import test_lib
from . import client

MOCK_SIGMA_RULE = """
title: Suspicious Installation of Zenmap
id: 5266a592-b793-11ea-b3de-0242ac130004
description: Detects suspicious installation of Zenmap
references:
    - https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html
author: Alexander Jaeger
date: 2020/06/26
modified: 2020/06/26
logsource:
    product: linux
    service: shell
detection:
    keywords:
        # Generic suspicious commands
        - '*apt-get install zmap*'
    condition: keywords
falsepositives:
    - Unknown
level: high
"""

MOCK_SIGMA_RULE_ERROR1 = """
title: Suspicious Foobar
id: 5266a592-b793-11ea-b3de-0242ac130004
description: Detects suspicious installation of Zenmap
references:
    - https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html
author: Alexander Jaeger
date: 2020/06/26
modified: 2020/06/26
"""

class TimesketchSigmaTest(unittest.TestCase):
    """Test Sigma."""

    @mock.patch('requests.Session', test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi(
            'http://127.0.0.1', 'test', 'test')

    def test_sigma_rule(self):
        """Test single Sigma rule."""

        # not sure which is the better way to do things here.
        rule = self.api_client.get_sigma_rule(
            rule_uuid='5266a592-b793-11ea-b3de-0242ac130004')
        rule.from_rule_uuid('5266a592-b793-11ea-b3de-0242ac130004')
        self.assertIsNotNone(rule)

        self.assertEqual(
            rule.title, 'Suspicious Installation of Zenmap',
            'Title of the rule does not match')
        self.assertEqual(
            rule.id, '5266a592-b793-11ea-b3de-0242ac130004',
            'Id of the rule does not match')
        self.assertIn('zmap', rule.es_query, 'ES_Query does not match')
        self.assertIn('b793', rule.id)

    def test_sigma_rules(self):
        '''Testing the Sigma rules list'''

        rules = self.api_client.list_sigma_rules()
        self.assertIsNotNone(rules)

        rule1 = rules[0]
        print("aaa" +rule1.id)
        self.assertEqual(
            rule1.title, 'Suspicious Installation of Zenmap',
            'Title of the rule does not match: ')
        self.assertIn('zmap', rule1.es_query, 'ES_Query does not match')
        self.assertIn('b793', rule1.id)

    def test_get_sigma_rule_by_text(self):
        rule = self.api_client.get_sigma_rule_by_text(MOCK_SIGMA_RULE)
        self.assertIsNotNone(rule)
        print(rule.__dict__)
        print(f'title: {rule.title} id: {rule.id}')

        self.assertIn('zmap', rule.es_query, 'ES_Query does not match')
        self.assertIn('Zenmap', rule.title, 'Title does not match')
