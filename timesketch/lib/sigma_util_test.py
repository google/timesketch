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
"""Tests for sigma_util score."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from sigma.parser import exceptions as sigma_exceptions

from timesketch.lib.testlib import BaseTest
import timesketch.lib.sigma_util as sigma_util


MOCK_SIGMA_RULE = """
title: Suspicious Installation of ZMap
id: 5266a592-b793-11ea-b3de-0242ac130004
description: Detects suspicious installation of zmap
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

MOCK_SIGMA_RULE_2 = """
title: This rule is full of test edge cases
description: Various edge cases in a rule
references:
    - https://github.com/google/timesketch/issues/2007
author: Alexander Jaeger
date: 2021/12/03
modified: 2021/12/03
detection:
    keywords:
        - 'Whitespace at'
        - ' beginning '
        - ' and extra text '
    condition: keywords
falsepositives:
    - Unknown
level: high
"""

MOCK_SIGMA_RULE_3 = """
logsource:
    product: windows
detection:
    keywords:
        - ' lorem '
    condition: keywords
"""

MOCK_SIGMA_RULE_ERROR1 = """
title: Suspicious Foobar
description: Detects suspicious installation of zmap
references:
    - https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html
author: Alexander Jaeger
date: 2020/06/26
modified: 2020/06/26
"""


class TestSigmaUtilLib(BaseTest):
    """Tests for the sigma support library."""

    def test_get_rule_by_text(self):
        """Test getting sigma rule by text."""

        rule = sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE)

        self.assertIsNotNone(MOCK_SIGMA_RULE)
        self.assertIsNotNone(rule)
        self.assertIn('zmap', rule.get('es_query'))
        self.assertIn('b793', rule.get('id'))
        self.assertRaises(
            sigma_exceptions.SigmaParseError,
            sigma_util.get_sigma_rule_by_text,
            MOCK_SIGMA_RULE_ERROR1)
        rule2 = sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE_2)
        rule3 = sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE_3)

        self.assertIsNotNone(rule2)
        self.assertEqual('("Whitespace at" OR " beginning " OR " and extra text ")', rule2.get('es_query'))

        self.assertIsNotNone(rule3)
        self.assertEqual('(data_type:"windows:evtx:record" AND " lorem ")', rule3.get('es_query'))

    def test_get_sigma_config_file(self):
        """Test getting sigma config file"""
        self.assertRaises(ValueError, sigma_util.get_sigma_config_file, '/foo')
        self.assertIsNotNone(sigma_util.get_sigma_config_file())

    def test_get_blocklist_file(self):
        """Test getting sigma config file"""
        self.assertRaises(ValueError, sigma_util.get_sigma_blocklist, '/foo')
        self.assertIsNotNone(sigma_util.get_sigma_config_file())

    def test_get_sigma_rule(self):
        """Test getting sigma rule from file"""

        filepath = './data/sigma/rules/lnx_susp_zmap.yml'

        rule = sigma_util.get_sigma_rule(filepath)

        self.assertIsNotNone(rule)
        self.assertIn('zmap', rule.get('es_query'))
        self.assertIn('b793', rule.get('id'))
