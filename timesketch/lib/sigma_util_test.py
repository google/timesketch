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


SIGMA_MOCK_RULE_TEST4 = r"""
title: Login with WMI
id: 5af54681-df95-4c26-854f-2565e13cfab0
status: stable
description: Detection of logins performed with WMI
author: Thomas Patzke
date: 2019/12/04
tags:
    - attack.execution
    - attack.t1047
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4624
        ProcessName|endswith: '\WmiPrvSE.exe'
    condition: selection
falsepositives:
    - Monitoring tools
    - Legitimate system administration
level: low
"""

SIGMA_MOCK_RULE_TEST5 = r"""

title: Proxy Execution via Wuauclt
id: af77cf95-c469-471c-b6a0-946c685c4798
related:
    - id: ba1bb0cb-73da-42de-ad3a-de10c643a5d0
      type: obsoletes
    - id: d7825193-b70a-48a4-b992-8b5b3015cc11
      type: obsoletes
status: test
description: Detects the use of the Windows Update Client binary (wuauclt.exe) to proxy execute code.
references:
    - https://dtm.uk/wuauclt/
    - https://blog.malwarebytes.com/threat-intelligence/2022/01/north-koreas-lazarus-apt-leverages-windows-update-client-github-in-latest-campaign/
author: Roberto Rodriguez (Cyb3rWard0g), OTR (Open Threat Research), Florian Roth (Nextron Systems), Sreeman, FPT.EagleEye Team
date: 2020/10/12
modified: 2023/02/13
tags:
    - attack.defense_evasion
    - attack.t1218
    - attack.execution
logsource:
    category: process_creation
    product: windows
detection:
    selection_img:
        - Image|endswith: '\wuauclt.exe'
        - OriginalFileName: 'wuauclt.exe'
    selection_cli:
        CommandLine|contains|all:
            - 'UpdateDeploymentProvider'
            - '.dll'
            - 'RunHandlerComServer'
    filter:
        CommandLine|contains:
            - ' /UpdateDeploymentProvider UpdateDeploymentProvider.dll '
            - ' wuaueng.dll '
    condition: all of selection_* and not filter
falsepositives:
    - Unknown
level: high
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

    def test_sanitize_rule_string_multiple_or(self):
        """test that the function does not break regular queries"""
        # pylint: disable=protected-access
        self.assertEqual(
            sigma_util._sanitize_query("*mimikatz* OR *mimikatz.exe* OR *mimilib.dll*"),
            "*mimikatz* OR *mimikatz.exe* OR *mimilib.dll*",
        )

    def test_sanitize_rule_string_multiple_colon(self):
        """Test sanitization of query with multiple colons and asterisks"""
        # pylint: disable=protected-access
        test_2 = sigma_util._sanitize_query("(*a:b* OR *c::d*)")
        self.assertEqual(test_2, r'("a:b" OR "c\:\:d")')

    def test_sanitize_rule_string_with_dotkeyword(self):
        """Test sanitization of query with .keyword in them"""
        # pylint: disable=protected-access
        test_3 = sigma_util._sanitize_query(
            '(xml_string.keyword:"\\foobar.exe" AND GrantedAccess.keyword:"10")'
        )
        self.assertEqual(test_3, r'(xml_string:"\foobar.exe" AND GrantedAccess:"10")')

    def test_sanitize_rule_string_with_double_quotes(self):
        """Test sanitization of query with double quotes in the query"""
        # pylint: disable=protected-access
        test_4 = sigma_util._sanitize_query(
            '(xml_string:C:\\Program Files\\WindowsApps\\" AND xml_string: "GamingServices.exe)'  # pylint: disable=line-too-long
        )
        self.assertIsNotNone(test_4)
        # pylint: enable=protected-access

    def test_get_rule_by_text(self):
        """Test getting sigma rule by text."""

        rule = sigma_util.parse_sigma_rule_by_text(SIGMA_MOCK_RULE_TEST4)

        self.assertIsNotNone(SIGMA_MOCK_RULE_TEST4)
        self.assertIsNotNone(rule)
        self.assertEqual(
            '(data_type:"windows:evtx:record" AND source_name:("Microsoft-Windows-Security-Auditing" OR "Microsoft-Windows-Eventlog") AND event_identifier:"4624" AND xml_string:"\\\\WmiPrvSE.exe")',  # pylint: disable=line-too-long
            rule.get("search_query"),
        )

    def test_get_rule_by_text_zmap_rule(self):
        """Test getting sigma rule by text with endswith in detection."""

        rule = sigma_util.parse_sigma_rule_by_text(
            """
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
        )

        self.assertIsNotNone(rule)
        self.assertIn("zmap", rule.get("search_query"))
        self.assertEqual(
            '(data_type:("shell:zsh:history" OR "bash:history:command" OR "apt:history:line" OR "selinux:line") AND "apt-get install zmap")',  # pylint: disable=line-too-long
            rule.get("search_query"),
        )
        self.assertIn("b793", rule.get("id"))
        self.assertIn("2020/06/26", rule.get("date"))
        self.assertIsInstance(rule.get("date"), str)

    def test_get_rule_by_text_no_sanitize(self):
        """Test getting sigma rule by text with no sanitization."""
        rule = sigma_util.parse_sigma_rule_by_text(
            r"""
title: TEST
id: BLAH
status: test
description: test
author: test
date: 2020/02/01
modified: 2020/02/01
tags:
    - tag1
logsource:
    category: process_creation
    product: windows
detection:
    selection_img:
        - Image|endswith: '\foo.exe'
        - OriginalFileName: 'origfile.exe'
    selection_cli:
        CommandLine|contains|all:
            - 'bar'
            - '.dll'
            - 'Baz'
    filter:
        CommandLine|contains:
            - ' /foo bar.dll '
            - ' baz.dll '
    condition: all of selection_* and not filter
falsepositives:
    - Unknown
level: high
""",
            sanitize=True,
        )

        self.assertIsNotNone(rule)
        self.assertEqual(
            '(data_type:"windows:evtx:record" AND event_identifier:("1" OR "4688") AND source_name:("Microsoft-Windows-Sysmon" OR "Microsoft-Windows-Security-Auditing" OR "Microsoft-Windows-Eventlog") AND ((message:"\\\\foo.exe" OR xml_string:"origfile.exe") AND (xml_string:*bar* AND xml_string:*.dll* AND xml_string:"Baz")) AND (NOT (xml_string:(" \\/foo bar.dll " OR " baz.dll "))))',  # pylint: disable=line-too-long
            rule.get("search_query"),
        )

    def test_get_rule_by_text_parsing_error(self):
        """Test getting sigma rule by text with a rule causing parsing error."""
        with self.assertRaises(sigma_exceptions.SigmaParseError):
            sigma_util.parse_sigma_rule_by_text(
                """
title: Suspicious Foobar
description: Detects suspicious installation of zmap
references:
    - https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html
author: Alexander Jaeger
date: 2020/06/26
modified: 2020/06/26
"""
            )

    def test_get_rule_by_text_whitespaces_in_detection(self):
        """Test getting sigma rule by text."""
        rule = sigma_util.parse_sigma_rule_by_text(
            """
title: This rule is full of test edge cases
id: aaa-3-34444-45-5-5-555
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
        )
        self.assertIsNotNone(rule)
        self.assertEqual(
            '("Whitespace at" OR " beginning " OR " and extra text ")',
            rule.get("search_query"),
        )

    def test_get_rule_by_text_minimal_rule(self):
        """Test getting sigma rule by text."""
        rule = sigma_util.parse_sigma_rule_by_text(
            """
title: foo
description: bar
id: aaaa-aaa-aaaa-aaaa
logsource:
    product: windows
detection:
    keywords:
        - ' lorem '
    condition: keywords
"""
        )

        self.assertIsNotNone(rule)
        self.assertEqual(
            '(data_type:"windows:evtx:record" AND " lorem ")',
            rule.get("search_query"),
        )

    def test_get_rule_by_text_count_condition_error(self):
        """Test getting sigma rule by text with count in condition which is not
        implemented so it will cause an exception."""
        with self.assertRaises(NotImplementedError):
            sigma_util.parse_sigma_rule_by_text(
                """
title: count in detection
description: rule that has count in the condition to error out
id: aaaaa-aaaa-aaa-aaa-aaa
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
            )

    def test_get_rule_by_text_date_error(self):
        """Test getting sigma rule by text with problematic value in date"""
        rule = sigma_util.parse_sigma_rule_by_text(
            """
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
        )
        # it is actually: 'date': datetime.date(2022, 1, 10)
        self.assertIsInstance(rule.get("date"), datetime.date)
        self.assertIsNot("2022-01-10", rule.get("date"))
        self.assertIn("dd23d2323432", rule.get("modified"))

    def test_get_rule_by_text_dots_in_keywords(self):
        """Test getting sigma rule by text with `:`in detection"""
        rule = sigma_util.parse_sigma_rule_by_text(
            """
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
        )
        self.assertIsNotNone(rule)
        self.assertEqual("67b9a11a-03ae-490a-9156-9be9900aaaaa", rule.get("id"))
        self.assertEqual(
            '("aaa:bbb" OR "ccc\\:\\:ddd")',
            rule.get("search_query"),
        )

    def test_get_rule_by_text_startswith_endswith_mixed(self):
        """Test getting sigma rule by text with startswith and endswith
        in detection"""
        rule = sigma_util.parse_sigma_rule_by_text(
            r"""
title: MIXED LSASS Mock rule to test various combinations
id: 5d2c62fe-3cbb-47c3-88e1-88ef73503a9f
description: rule to make a complex test case
status: experimental
author: Alexander Jaeger
date: 2022/04/26
references:
    - https://github.com/SigmaHQ/sigma/blob/e4c8e62ba6a32f8966ab4216a15dd393af4ef3a3/rules/windows/process_access/proc_access_win_rare_proc_access_lsass.yml # pylint: disable=line-too-long
logsource:
    category: process_access
    product: windows
detection:
    selection:
        TargetImage|endswith: '\foobar.exe'
        GrantedAccess|endswith: '10'
    # Absolute paths to programs that cause false positives
    filter1:
        SourceImage:
            - 'C:\WINDOWS\system32\foo.exe'
            - 'C:\Program Files\Malwarebytes\Anti-Malware\lorem.exe'
            - 'C:\PROGRAMDATA\MALWAREBYTES\MBAMSERVICE\ipsum\gfdsa.exe'
            - 'C:\WINDOWS\system32\taskhostv.exe'
            - 'C:\Users\\*\AppData\Local\Programs\Microsoft VS Code\Microsoft.exe'
            - 'C:\Program Files\Windows Defender\MsMpFoo.exe'
            - 'C:\Windows\SysWOW64\gciexec.exe'
            - 'C:\Windows\System32\gciexec.exe'
            - 'C:\Windows\System32\lsoss.exe'
            - 'C:\WINDOWS\System32\loremmon.exe'
    # Windows Defender
    filter2:
        SourceImage|startswith: 'C:\ProgramData\Microsoft\Windows Avangers\'
        SourceImage|endswith: '\MsMpFoo.exe'
    # Microsoft Eating Services
    filter3:
        SourceImage|startswith: 'C:\Program Files\WindowsApps\'
        SourceImage|endswith: '\EatingServices.exe'
    # Process Drinker
    filter4:
        SourceImage|endswith:
            - '\PROCDRINK64.EXE'
            - '\PROCDRINK.EXE'
    # BMware Tools
    filter5:
        SourceImage|startswith: 'C:\ProgramData\BMware\BMware Tools\'
        SourceImage|endswith: '\bmtoolsd.exe'
    # Provirus and MBR agents
    filter6:
        SourceImage|startswith:
            - 'C:\Program Files\'
            - 'C:\Program Files (x86)\'
        SourceImage|contains:
            - 'Provirus'
    filter7:
        SourceImage: 'C:\WINDOWS\system32\wbem\vgaprvse.exe'
    filter8:
        SourceImage: 'C:\Windows\sysWOW64\wbem\vgaprvse.exe'
    filter_mcbfee:
        SourceImage: 'C:\Program Files\Common Files\McBfee\ABBSHost\ABBSHOST.exe'
    filter_prevtron:
        SourceImage|startswith: 'C:\Windows\Temp\bsgbrd2-agent\'
        SourceImage|endswith:
            - '\hammer64.exe'
            - '\hammer.exe'
    filter_generic:
        SourceImage|startswith:
            - 'C:\Program Files\'
            - 'C:\Program Files (x86)\'
            - 'C:\WINDOWS\system32\'
    filter_localappdata:
        SourceImage|contains|all:
            - 'C:\Users\'
            - '\AppData\Local\'
        SourceImage|endswith:
            - '\Maxisoft AB Cade\Cade.exe'
            - '\software_influencer_tool.exe'
            - '\PickUpdate.exe'
            - '\NBAInstallerService.exe'
    condition: selection and not 1 of filter*
fields:
    - User
    - SourceImage
    - GrantedAccess
falsepositives:
    - Legitimate software accessing LSASS process for legitimate reason
level: medium
"""
        )

        self.assertIsNotNone(rule)
        self.assertEqual("5d2c62fe-3cbb-47c3-88e1-88ef73503a9f", rule.get("id"))
        self.assertIn(
            'event_identifier:"10"',
            rule.get("search_query"),
        )
        self.assertIn(
            'xml_string:"\\\\foobar.exe" AND xml_string:"10"',
            rule.get("search_query"),
        )

    def test_get_sigma_rule_by_text_missing_title(self):
        """Test the Sigma yaml rule parsing with missing title value"""
        rule = r"""
id: 5af54681-df95-4c26-854f-2565e13cfab0
status: stable
description: Detection of logins performed with WMI
detection:
    selection:
        EventID: 4624
        ProcessName|endswith: '\WmiPrvSE.exe'
    condition: selection
"""
        with self.assertRaises(ValueError):
            sigma_util.parse_sigma_rule_by_text(rule)

    def test_get_sigma_config_file(self):
        """Test getting sigma config file"""
        with self.assertRaises(ValueError):
            sigma_util.get_sigma_config_file("/foo")
        self.assertIsNotNone(sigma_util.get_sigma_config_file())

    def test_get_sigmarule_by_text_first_term(self):
        """Test getting sigma rule by text"""
        rule = sigma_util.parse_sigma_rule_by_text(
            r"""
title: WMI Login
id: 5af54681-df95-4c26-854f-2565e13cfab0
status: stable
description: Detection of logins performed with WMI
detection:
    star:
        star:
            - '*stararoundterm*'
    quote:
        quote:
            - 'quote'
    condition:
        (1 of star) and (1 of quote)
"""
        )
        self.assertIsNotNone(rule)

    def test_sigmarule_by_text_three_words(self):
        """
        Testing the different terms in a Sigma rule and how each is treated.
        Reference: https://github.com/google/timesketch/issues/2550
        """
        rule = sigma_util.parse_sigma_rule_by_text(
            r"""
title: test terms
id: 6d8ca9f2-79e2-44bd-957d-b4d810374972
description: Rule to test combination of three words and how they are parsed
author: Alexander Jaeger
date: 2023/02/13
modified: 2023/02/13
falsepositives:
    - Legitimate usage of the terms
tags:
    - testrule
status: experimental
level: medium
detection:
    keywords:
        - '*onlyoneterm*'
        - '*two words*'
        - '*completely new term*'
    condition: keywords"""
        )
        self.assertIsNotNone(rule)
        self.assertEqual(
            '("onlyoneterm" OR "two words" OR "completely new term")',
            rule.get("search_query"),
        )

    def test_get_rule_by_text_specialchar(self):
        """
        Testing rules, that contain special characters (like "'") in their description
        """
        rule = sigma_util.parse_sigma_rule_by_text(
            r"""
title: Vim GTFOBin Abuse - Linux
id: 7ab8f73a-fcff-428b-84aa-6a5ff7877dea
status: test
description: Detects usage of "vim" and it's siblings as a GTFOBin to execute and proxy command and binary execution # pylint: disable=line-too-long
references:
    - https://gtfobins.github.io/gtfobins/vim/
    - https://gtfobins.github.io/gtfobins/rvim/
    - https://gtfobins.github.io/gtfobins/vimdiff/
author: Nasreddine Bencherchali (Nextron Systems)
date: 2022/12/28
tags:
    - attack.discovery
    - attack.t1083
logsource:
    category: process_creation
    product: linux
detection:
    selection_img:
        Image|endswith:
            - '/vim'
            - '/rvim'
            - '/vimdiff'
        CommandLine|contains:
            - ' -c '
            - ' --cmd'
    selection_cli:
        CommandLine|contains:
            - ':!/'
            - ':py '
            - ':lua '
            - '/bin/sh'
            - '/bin/bash'
            - '/bin/dash'
            - '/bin/zsh'
            - '/bin/fish'
    condition: all of selection_*
falsepositives:
    - Unknown
level: high
"""
        )
        self.assertIsNotNone(rule)
