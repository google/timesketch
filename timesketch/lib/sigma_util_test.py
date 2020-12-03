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


class TestSigmaUtilLib(BaseTest):
    """Tests for the sigma support library."""


    def test_get_rule_by_text(self):
        """Test getting sigma rule by text."""

        rule_text = "title: Suspicious Installation of Zenmap\n" \
        "id: 5266a592-b793-11ea-b3de-0242ac130004\n" \
        "description: Detects suspicious installation of Zenmap\n" \
        "references:\n" \
        "    - https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html\n" \
        "author: Alexander Jaeger\n" \
        "date: 2020/06/26\n" \
        "modified: 2020/06/26\n" \
        "logsource:\n" \
        "    product: linux\n" \
        "    service: shell\n" \
        "detection:\n" \
        "    keywords:\n" \
        "        # Generic suspicious commands\n" \
        "        - '*apt-get install zmap*'\n" \
        "    condition: keywords\n" \
        "falsepositives:\n" \
        "    - Unknown\n" \
        "level: high\n"

        config_file = './data/sigma_config.yaml'

        with open(config_file, 'r') as config_file:
            sigma_config_file = config_file.read()

            sigma_config = sigma_configuration.SigmaConfiguration(
                sigma_config_file)

        rule = sigma_util.get_sigma_rule_by_text(rule_text, sigma_config)

        self.assertIsNotNone(rule_text)
        self.assertIsNotNone(rule)
        self.assertIn('zmap', rule.get('es_query'))
        self.assertIn('b793', rule.get('id'))

    def test_get_sigma_config_file(self):
        """Test getting sigma config file"""
        self.assertIsNotNone('aaa')
        # TODO: use that:
        #self.assertRaises(ValueError, sigma_util.get_sigma_config_file())

    def test_get_sigma_rule(self):
        """Test getting sigma rule from file"""

        filepath = './data/sigma/rules/lnx_susp_zenmap.yml'

        self.assertIsNone(sigma_util.get_sigma_rule(filepath))

        #self.assertRaises(ValueError, )
