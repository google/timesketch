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
from datasketch import MinHash

from timesketch.lib.experimental.similarity import SimilarityScorer
from timesketch.lib.experimental.similarity import SimilarityScorerConfig
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestSimilarityScorerConfig(BaseTest):
    """Tests for the functionality of the config object."""

    def test_config(self):
        """Test config object."""
        data_type = 'test:test'
        index = 'test_index'
        config = SimilarityScorerConfig(data_type=data_type, index=index)

        compare_config = {
            'index': '{0}'.format(index),
            'data_type': '{0}'.format(data_type),
            'query': 'data_type:"{0}"'.format(data_type),
            'field': 'message',
            'delimiters': [' ', '-', '/'],
            'threshold': config.DEFAULT_THRESHOLD,
            'num_perm': config.DEFAULT_PERMUTATIONS
        }
        self.assertIsInstance(config, SimilarityScorerConfig)
        for k, v in compare_config.items():
            self.assertEqual(v, getattr(config, k))


class TestSimilarityScorer(BaseTest):
    """Tests for the functionality of the scorer object."""

    def __init__(self, *args, **kwargs):
        super(TestSimilarityScorer, self).__init__(*args, **kwargs)
        self.test_data_type = 'test:test'
        self.test_index = 'test_index'
        self.test_text = 'This is a test text-with tests/test'

    @mock.patch(
        u'timesketch.lib.experimental.similarity.ElasticsearchDataStore',
        MockDataStore)
    def test_scorer(self):
        """Test scorer object."""
        scorer = SimilarityScorer(
            index=self.test_index, data_type=self.test_data_type)
        self.assertIsInstance(scorer, SimilarityScorer)

    @mock.patch(
        u'timesketch.lib.experimental.similarity.ElasticsearchDataStore',
        MockDataStore)
    def test_shingles_from_text(self):
        """Test splitting up a text string to words."""
        scorer = SimilarityScorer(
            index=self.test_index, data_type=self.test_data_type)
        # pylint: disable=protected-access
        shingles = scorer._shingles_from_text(self.test_text)
        self.assertIsInstance(shingles, list)
        self.assertEqual(len(shingles), 8)

    @mock.patch(
        u'timesketch.lib.experimental.similarity.ElasticsearchDataStore',
        MockDataStore)
    def test_minhash_from_text(self):
        """Test create minhash from text."""
        scorer = SimilarityScorer(
            index=self.test_index, data_type=self.test_data_type)
        # pylint: disable=protected-access
        minhash = scorer._minhash_from_text(self.test_text)
        self.assertIsInstance(minhash, MinHash)
