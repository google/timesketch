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
"""Tests for aggregations."""
from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers.similarity_scorer import SimilarityScorer
from timesketch.lib.analyzers.similarity_scorer import SimilarityScorerConfig
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestSimilarityScorerConfig(BaseTest):
    """Tests for the functionality of the config object."""

    def test_config(self):
        """Test config object."""
        data_type = "test:test"
        index = "test_index"
        config = SimilarityScorerConfig(data_type=data_type, index_name=index)

        compare_config = {
            "index_name": "{0}".format(index),
            "data_type": "{0}".format(data_type),
            "query": 'data_type:"{0}"'.format(data_type),
            "field": "message",
            "delimiters": [" ", "-", "/"],
            "threshold": config.DEFAULT_THRESHOLD,
            "num_perm": config.DEFAULT_PERMUTATIONS,
        }
        self.assertIsInstance(config, SimilarityScorerConfig)
        for k, v in compare_config.items():
            self.assertEqual(v, getattr(config, k))


class TestSimilarityScorer(BaseTest):
    """Tests for the functionality of the scorer object."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_data_type = "test:test"
        self.test_index = "test_index"
        self.test_text = "This is a test text-with tests/test"

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_scorer(self):
        """Test scorer object."""
        scorer = SimilarityScorer(
            index_name=self.test_index, sketch_id=1, data_type=self.test_data_type
        )
        self.assertIsInstance(scorer, SimilarityScorer)
