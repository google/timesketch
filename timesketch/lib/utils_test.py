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

from __future__ import unicode_literals

import re

from timesketch.lib.testlib import BaseTest
from timesketch.lib.utils import get_validated_indices
from timesketch.lib.utils import random_color


class TestUtils(BaseTest):
    """Tests for the functionality on the utils module."""

    def test_random_color(self):
        """Test to generate a random color."""
        color = random_color()
        self.assertTrue(re.match('^[0-9a-fA-F]{6}$', color))

    def test_get_validated_indices(self):
        """Test for validating indices."""
        sketch = self.sketch1
        sketch_indices = [t.searchindex.index_name for t in sketch.timelines]

        sketch_structure = {}
        for timeline in sketch.timelines:
            if timeline.get_status.status.lower() != 'ready':
                continue
            index_ = timeline.searchindex.index_name
            sketch_structure.setdefault(index_, [])
            sketch_structure[index_].append({
                'name': timeline.name,
                'id': timeline.id,
            })


        valid_indices = ['test']
        invalid_indices = ['test', 'fail']

        test_indices, _ = get_validated_indices(valid_indices, sketch_structure)
        self.assertListEqual(sketch_indices, test_indices)

        test_indices, _ = get_validated_indices(
            invalid_indices, sketch_structure)
        self.assertFalse('fail' in test_indices)
