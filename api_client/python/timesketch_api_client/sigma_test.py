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

# TODO remove config
from . import config
from . import sigma
from . import test_lib
from . import client



class TimesketchSigmaTest(unittest.TestCase):
    """Test Sigma."""

    TEST_Rule_1 = """
title: Suspicious Test rule 1
id: 45408669-b6a3-4c7a-b678-84f62ca914ab
description: Detects nothing
references:
    - https://demo.timesketch.org
author: Alexander Jaeger
date: 2020/11/10
modified: 2020/11/10
logsource:
    product: linux
    service: shell
detection:
    keywords:
        # Generic suspicious commands
        - '*curl timesketch*'
    condition: keywords
falsepositives:
    - Unknown
level: high
    """
    TEST_Rule_1 = """
title: Suspicious Test rule 2
id: 776bdd11-f3aa-436e-9d03-9d6159e9814e
description: Detects nothing more
references:
    - https://demo.timesketch.org
author: Alexander Jaeger
date: 2020/11/10
modified: 2020/11/10
logsource:
    product: linux
    service: shell
detection:
    keywords:
        # Generic suspicious commands
        - '*curl log2timeline*'
    condition: keywords
falsepositives:
    - Unknown
level: low
    """
    TEST_rule_3 = {'title': 'Suspicious Installation of Zenmap',
                    'id': '5266a592-b793-11ea-b3de-0242ac130004',
                    'description': 'Detects suspicious installation of Zenmap',
                    'references': ['https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html'],
                    'author': 'Alexander Jaeger',
                    'date': '2020/06/26',
                    'modified': '2020/06/26',
                    'logsource': {'product': 'linux', 'service': 'shell'},
                    'detection': {'keywords': ['*apt-get install zmap*'],
                    'condition': 'keywords'},
                    'falsepositives': ['Unknown'],
                    'level': 'high',
                    'es_query': '(data_type:("shell\\:zsh\\:history" OR "bash\\:history\\:command" OR "apt\\:history\\:line" OR "selinux\\:line") AND "*apt\\-get\\ install\\ zmap*")',
                    'file_name': 'lnx_susp_zenmap'}

    @mock.patch('requests.Session', test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi(
            'http://127.0.0.1', 'test', 'test')
        self.rule = self.api_client.get_sigma_rule("5266a592-b793-11ea-b3de-0242ac130004")


    def test_sigma_rule(self):
        self.assertIsNotNone(True)
