# Copyright 2017 Google Inc. All rights reserved.
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

from . import client
from . import sketch as sketch_lib
from . import test_lib
from timesketch_api_client import sigma

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


class TimesketchApiTest(unittest.TestCase):
    """Test TimesketchApi"""

    @mock.patch("requests.Session", test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")

    def test_fetch_resource_data(self):
        """Test fetch resource."""
        response = self.api_client.fetch_resource_data("sketches/")
        self.assertIsInstance(response, dict)

    # TODO: Add test for create_sketch()

    def test_get_sketch(self):
        """Test to get a sketch."""
        sketch = self.api_client.get_sketch(1)
        self.assertIsInstance(sketch, sketch_lib.Sketch)
        self.assertEqual(sketch.id, 1)
        self.assertEqual(sketch.name, "test")
        self.assertEqual(sketch.description, "test")

    def test_get_sketches(self):
        """Test to get a list of sketches."""
        sketches = list(self.api_client.list_sketches())
        self.assertIsInstance(sketches, list)
        self.assertEqual(len(sketches), 1)
        self.assertIsInstance(sketches[0], sketch_lib.Sketch)

    def test_get_sigma_rule_by_text(self):
        rule = self.api_client.get_sigma_rule_by_text("asdasd")
        self.assertIn("Alexander", rule.author)

    def test_create_sigma_rule(self):
        rule = self.api_client.create_sigma_rule(
            rule_text=MOCK_SIGMA_RULE)
        self.assertIsInstance(rule,sigma.Sigma)
        self.assertIn("5266a592-b793-11ea-b3de-0242ac", rule.id)
        self.assertIn("5266a592-b793-11ea-b3de-0242ac", rule.rule_uuid)
        self.assertIn("suspicious installation of ZMap", rule.description)
        self.assertIn('"*apt\\-get\\ install\\ zmap*"', rule.es_query)

