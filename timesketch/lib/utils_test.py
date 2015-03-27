# Copyright 2014 Google Inc. All rights reserved.
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
"""Tests for utils."""

import re

from timesketch.lib.testlib import BaseTest
from timesketch.lib.utils import random_color


class TestUtils(BaseTest):
    """Tests for the functionality on the utils module."""
    def test_random_color(self):
        """Test to generate a random color."""
        color = random_color()
        self.assertTrue(re.match(u'^[0-9a-fA-F]{6}$', color))
