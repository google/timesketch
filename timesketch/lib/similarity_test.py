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
"""Tests for similar score."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import mock
from datasketch import MinHash

from timesketch.lib import similarity
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestSimilarityLibScorer(BaseTest):
    """Tests for the functionality of the scorer object."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_data_type = "test:test"
        self.test_index = "test_index"
        self.test_text = "This is a test text-with tests/test"
        self.delimiters = [" ", "-", "/"]

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_shingles_from_text(self):
        """Test splitting up a text string to words."""
        # pylint: disable=protected-access
        shingles = similarity._shingles_from_text(self.test_text, self.delimiters)
        self.assertIsInstance(shingles, list)
        self.assertEqual(len(shingles), 8)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_minhash_from_text(self):
        """Test create minhash from text."""
        minhash = similarity.minhash_from_text(
            self.test_text, similarity.DEFAULT_PERMUTATIONS, self.delimiters
        )
        self.assertIsInstance(minhash, MinHash)
