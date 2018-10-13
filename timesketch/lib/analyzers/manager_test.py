# Copyright 2018 Google Inc. All rights reserved.
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
"""Tests for analysis manager."""

from __future__ import unicode_literals

from timesketch.lib.testlib import BaseTest
from timesketch.lib.analyzers import manager


class MockAnalyzer(object):
    """Mock analyzer class,"""
    NAME = 'MockAnalyzer'


class TestAnalysisManager(BaseTest):
    """Tests for the functionality of the manager module."""

    manager.AnalysisManager.register_analyzer(MockAnalyzer)

    def test_get_analyzers(self):
        """Test to get analyzer class objects."""
        analyzers = manager.AnalysisManager.get_analyzers()
        analyzer_list = [x for x in analyzers]
        first_analyzer_tuple = analyzer_list[0]
        analyzer_name, analyzer_class = first_analyzer_tuple
        self.assertIsInstance(analyzer_list, list)
        self.assertIsInstance(first_analyzer_tuple, tuple)
        self.assertEqual(analyzer_class, MockAnalyzer)
        self.assertEqual(analyzer_name, 'mockanalyzer')

    def test_get_analyzer(self):
        """Test to get analyzer class from registry."""
        analyzer_class = manager.AnalysisManager.get_analyzer('mockanalyzer')
        self.assertEqual(analyzer_class, MockAnalyzer)

    def test_register_analyzer(self):
        """Test so we raise KeyError when analyzer is already registered."""
        self.assertRaises(
            KeyError, manager.AnalysisManager.register_analyzer, MockAnalyzer)
