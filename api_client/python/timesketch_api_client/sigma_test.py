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
modified: 2021/01/01
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

        rule = self.api_client.get_sigma_rule(
            rule_uuid='5266a592-b793-11ea-b3de-0242ac130004')
        rule.from_rule_uuid('5266a592-b793-11ea-b3de-0242ac130004')
        self.assertGreater(len(rule.attributes),5)
        self.assertIsNotNone(rule)
        self.assertIn('Alexander', rule.author)
        self.assertIn('Alexander', rule.get_attribute('author'))
        self.assertEqual(rule.id, '5266a592-b793-11ea-b3de-0242ac130004')
        self.assertEqual(rule.title, 'Suspicious Installation of Zenmap')
        self.assertIn('zmap', rule.es_query, 'ES_Query does not match')
        self.assertIn('b793', rule.id)
        self.assertIn('/syslog/foobar/', rule.file_relpath)
        self.assertIn('sigma/rule/5266a592', rule.resource_uri)
        self.assertIn('suspicious installation of Zenmap', rule.description)
        self.assertIn('high', rule.level)
        self.assertEqual(len(rule.falsepositives), 1)
        self.assertIn('Unknown', rule.falsepositives[0])
        self.assertIn('susp_zenmap', rule.file_name)
        self.assertIn('2020/06/26', rule.date)
        self.assertIn('2021/01/01', rule.modified)
        self.assertIn('high', rule.level)
        self.assertIn('foobar.com', rule.references[0])
        self.assertEqual(len(rule.detection), 2)
        self.assertEqual(len(rule.logsource), 2)


    def test_sigma_rules(self):
        '''Testing the Sigma rules list'''

        rules = self.api_client.list_sigma_rules()
        self.assertIsNotNone(rules)
        self.assertEqual(len(rules), 2)
        rule = rules[0]
        self.assertEqual(rule.title, 'Suspicious Installation of Zenmap')
        self.assertIn('zmap', rule.es_query, 'ES_Query does not match')
        self.assertIn('b793', rule.id)
        self.assertIn('Alexander', rule.author)
        self.assertIn('2020/06/26',rule.date)
        self.assertIn('installation of Zenmap', rule.description)
        self.assertEqual(len(rule.detection), 2)
        self.assertIn('zmap*', rule.es_query)
        self.assertIn('Unknown', rule.falsepositives[0])
        self.assertEqual(len(rule.detection), 2)
        self.assertEqual(len(rule.logsource), 2)
        self.assertIn('2020/06/26', rule.modified)
        self.assertIn('/linux/syslog/foobar', rule.file_relpath)
        self.assertIn('lnx_susp_zenmap', rule.file_name)
        self.assertIn('high', rule.level)
        self.assertIn('foobar.com', rule.references[0])


    def test_get_sigma_rule_by_text(self):

        rule = self.api_client.get_sigma_rule_by_text(MOCK_SIGMA_RULE)

        self.assertIsNotNone(rule)
        self.assertGreater(len(rule.attributes),5)
        self.assertIn('zsh', rule.es_query)
        self.assertIn('Installation of foobar', rule.title)
        self.assertIn('', rule.id)
        self.assertIn('', rule.file_relpath)
        self.assertIn('http://127.0.0.1/api/v1/sigma/text/', rule.resource_uri)
        self.assertIn('suspicious installation of foobar', rule.description)
        self.assertIn('high', rule.level)
        self.assertEqual(len(rule.falsepositives), 1)
        self.assertIn('Unknown', rule.falsepositives[0])
        self.assertIn('N/A', rule.file_name)
        self.assertIn('Alexander', rule.author)
        self.assertIn('2020/12/10', rule.date)
        self.assertIn('2021/01/01', rule.modified)
        self.assertEqual(len(rule.detection), 2)
        self.assertEqual(len(rule.logsource), 2)
