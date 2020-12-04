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

import sigma.configuration as sigma_configuration

from timesketch.lib.testlib import BaseTest
import timesketch.lib.sigma_util as sigma_util


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


class TestSigmaUtilLib(BaseTest):
    """Tests for the sigma support library."""


    def test_get_rule_by_text(self):
        """Test getting sigma rule by text."""

        config_file = './data/sigma_config.yaml'

        with open(config_file, 'r') as config_file:
            sigma_config_file = config_file.read()

            sigma_config = sigma_configuration.SigmaConfiguration(
                sigma_config_file)

        rule = sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE, sigma_config)

        self.assertIsNotNone(MOCK_SIGMA_RULE)
        self.assertIsNotNone(rule)
        self.assertIn('zmap', rule.get('es_query'))
        self.assertIn('b793', rule.get('id'))

        self.assertIsNone(sigma_util.get_sigma_rule_by_text(
                          MOCK_SIGMA_RULE_ERROR1, sigma_config))


    def test_get_sigma_config_file(self):
        """Test getting sigma config file"""
        # TODO write tests

    def test_get_sigma_rule(self):
        """Test getting sigma rule from file"""

        filepath = './data/sigma/rules/lnx_susp_zenmap.yml'
        self.assertRaises(ValueError, sigma_util.get_sigma_rule(filepath))
