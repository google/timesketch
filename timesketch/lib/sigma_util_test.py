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
from timesketch.lib import sigma_util


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

MOCK_SIGMA_RULE_ERROR1 = """
title: Suspicious Foobar
id: 5266a592-b793-11ea-b3de-0242ac130004
description: Detects suspicious installation of zmap
references:
    - https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html
author: Alexander Jaeger
date: 2020/06/26
modified: 2020/06/26
"""

MOCK_SIGMA_RULE_DATE_ERROR1 = """
title: Wrong dateformat
id: 67b9a11a-03ae-490a-9156-9be9900f86b0
description: Does nothing useful
references:
    - https://github.com/google/timesketch/issues/2033
author: Alexander Jaeger
date: 2022-01-10
modified: dd23d2323432
detection:
    keywords:
        - 'foobar'
    condition: keywords
"""


class TestSigmaUtilLib(BaseTest):
    """Tests for the sigma support library."""

    def test_get_rule_by_text(self):
        """Test getting sigma rule by text."""

        rule = sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE)

        self.assertIsNotNone(MOCK_SIGMA_RULE)
        self.assertIsNotNone(rule)
        self.assertIn("zmap", rule.get("es_query"))
        self.assertIn("b793", rule.get("id"))
        self.assertRaises(
            sigma_exceptions.SigmaParseError,
            sigma_util.get_sigma_rule_by_text,
            MOCK_SIGMA_RULE_ERROR1,
        )
        self.assertIn("2020/06/26", rule.get("date"))

        rule = sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE_DATE_ERROR1)
        self.assertIsNotNone(MOCK_SIGMA_RULE_DATE_ERROR1)
        # it is actually: 'date': datetime.date(2022, 1, 10)
        self.assertIsNot("2022-01-10", rule.get("date"))
        self.assertIn("dd23d2323432", rule.get("modified"))

    def test_get_sigma_config_file(self):
        """Test getting sigma config file"""
        self.assertRaises(ValueError, sigma_util.get_sigma_config_file, "/foo")
        self.assertIsNotNone(sigma_util.get_sigma_config_file())

    def test_get_blocklist_file(self):
        """Test getting sigma config file"""
        self.assertRaises(ValueError, sigma_util.get_sigma_blocklist, "/foo")
        self.assertIsNotNone(sigma_util.get_sigma_config_file())

    def test_get_sigma_rule(self):
        """Test getting sigma rule from file"""

        filepath = "./data/sigma/rules/lnx_susp_zmap.yml"

        rule = sigma_util.get_sigma_rule(filepath)

        self.assertIsNotNone(rule)
        self.assertIn("zmap", rule.get("es_query"))
        self.assertIn("b793", rule.get("id"))
