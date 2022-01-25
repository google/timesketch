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

import datetime

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


COUNT_RULE_1 = """
detection:
  selection:
    action: failure
  timeframe: 10s
  condition: selection | count(category) by foo > 30
fields:
  - foo
  - bar
  - user
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

MOCK_SIGMA_RULE_DOTS = """
title: Two dots
id: 67b9a11a-03ae-490a-9156-9be9900aaaaa
description: Similar to a mimikatz rule
references:
    - https://github.com/google/timesketch/issues/2007
author: Alexander Jaeger
date: 2022-01-25
modified: 2022-01-25
detection:
    keywords:
        - 'aaa:bbb'
        - 'ccc::ddd'
    condition: keywords
"""


class TestSigmaUtilLib(BaseTest):
    """Tests for the sigma support library."""

    def test_sanitize_rule_string(self):
        """Testing the string sanitization"""

        # pylint: disable=protected-access
        test_1 = sigma_util._sanitize_query("(* lorem * OR * lorema *)")
        self.assertIsNotNone(test_1)

        self.assertEqual(
            sigma_util._sanitize_query("test.keyword:foobar"),
            "test:foobar",
        )
        self.assertEqual(
            sigma_util._sanitize_query("(* foobar *)"),
            '(" foobar ")',
        )
        self.assertEqual(sigma_util._sanitize_query("*foo bar*"), '"foo bar"')

        # test that the function does not break regular queries
        self.assertEqual(
            sigma_util._sanitize_query(
                "*mimikatz* OR *mimikatz.exe* OR *mimilib.dll*"
            ),
            '*mimikatz* OR *mimikatz.exe* OR *mimilib.dll*',
        )

        test_2 = sigma_util._sanitize_query("(*a:b* OR *c::d*)")
        self.assertEqual(test_2, r'("a:b" OR "c\:\:d")')
        # pylint: enable=protected-access

    def test_get_rule_by_text(self):
        """Test getting sigma rule by text."""

        rule = sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE)

        self.assertIsNotNone(MOCK_SIGMA_RULE)
        self.assertIsNotNone(rule)
        self.assertIn("zmap", rule.get("es_query"))
        self.assertEqual(
            '(data_type:("shell:zsh:history" OR "bash:history:command" OR "apt:history:line" OR "selinux:line") AND "apt-get install zmap")',  # pylint: disable=line-too-long
            rule.get("es_query"),
        )
        self.assertIn("b793", rule.get('id'))

        with self.assertRaises(sigma_exceptions.SigmaParseError):
            sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE_ERROR1)

        self.assertIn("2020/06/26", rule.get("date"))
        self.assertIsInstance(rule.get("date"), str)

        rule = sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE_2)

        self.assertIsNotNone(rule)
        self.assertEqual(
            '("Whitespace at" OR " beginning " OR " and extra text ")',
            rule.get("es_query"),
        )

        rule = sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE_3)

        self.assertIsNotNone(rule)
        self.assertEqual(
            '(data_type:"windows:evtx:record" AND " lorem ")',
            rule.get("es_query"),
        )

        with self.assertRaises(NotImplementedError):
            sigma_util.get_sigma_rule_by_text(COUNT_RULE_1)

        rule = sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE_DATE_ERROR1)
        self.assertIsNotNone(MOCK_SIGMA_RULE_DATE_ERROR1)
        # it is actually: 'date': datetime.date(2022, 1, 10)
        self.assertIsInstance(rule.get("date"), datetime.date)
        self.assertIsNot("2022-01-10", rule.get("date"))
        self.assertIn("dd23d2323432", rule.get("modified"))

        rule = sigma_util.get_sigma_rule_by_text(MOCK_SIGMA_RULE_DOTS)
        self.assertIsNotNone(MOCK_SIGMA_RULE_DOTS)
        self.assertIsNotNone(rule)
        self.assertEqual(
            '67b9a11a-03ae-490a-9156-9be9900aaaaa', rule.get('id')
        )
        self.assertEqual(
            r'("aaa:bbb" OR "ccc\:\:ddd")',
            rule.get("es_query"),
        )

    def test_get_sigma_config_file(self):
        """Test getting sigma config file"""
        with self.assertRaises(ValueError):
            sigma_util.get_sigma_config_file("/foo")
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
