# Copyright 2022 Google Inc. All rights reserved.
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
"""Tests for the sigma model."""

from __future__ import unicode_literals

from timesketch.lib.testlib import ModelBaseTest
from timesketch.models.sigma import Sigma

SIGMA_RULE = """
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


class SigmaModelTest(ModelBaseTest):
    """Tests the sigma model"""

    def test_sigma_model(self):
        """Test that the test sigma rule has the expected data stored
        in the database.
        """
        expected_result2 = frozenset(
            [
                ('rule_uuid', '5266a592-b793-11ea-b3de-0242ac130004'),
                ('rule_yaml', SIGMA_RULE),
            ]
        )
        self._test_db_object(expected_result=expected_result2, model_cls=Sigma)
