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

    NAME = "MockAnalyzer"

    DEPENDENCIES = frozenset()


class MockAnalyzer2(object):
    """Mock analyzer class,"""

    NAME = "MockAnalyzer2"

    DEPENDENCIES = frozenset(["MockAnalyzer"])


class MockAnalyzer3(object):
    """Mock analyzer class,"""

    NAME = "MockAnalyzer3"

    DEPENDENCIES = frozenset()


class MockAnalyzer4(object):
    """Mock analyzer class,"""

    NAME = "MockAnalyzer4"

    DEPENDENCIES = frozenset(["MockAnalyzer2", "MockAnalyzer3"])


class MockAnalyzerFail1(object):
    """Mock analyzer class,"""

    NAME = "MockAnalyzerFail1"

    DEPENDENCIES = frozenset(["MockAnalyzerFail2"])


class MockAnalyzerFail2(object):
    """Mock analyzer class,"""

    NAME = "MockAnalyzerFail2"

    DEPENDENCIES = frozenset(["MockAnalyzerFail1"])


class TestAnalysisManager(BaseTest):
    """Tests for the functionality of the manager module."""

    def setUp(self):
        """Set up the tests."""
        super().setUp()
        manager.AnalysisManager.clear_registration()
        manager.AnalysisManager.register_analyzer(MockAnalyzer)

    def test_get_analyzers(self):
        """Test to get analyzer class objects."""
        analyzers = manager.AnalysisManager.get_analyzers()
        analyzer_list = list(analyzers)

        analyzer_dict = {}
        for name, analyzer_class in analyzer_list:
            analyzer_dict[name] = analyzer_class
        self.assertIn("mockanalyzer", analyzer_dict)
        analyzer_class = analyzer_dict.get("mockanalyzer")
        self.assertEqual(analyzer_class, MockAnalyzer)

        manager.AnalysisManager.clear_registration()
        analyzers = manager.AnalysisManager.get_analyzers()
        analyzer_list = list(analyzers)
        self.assertEqual(analyzer_list, [])

        manager.AnalysisManager.register_analyzer(MockAnalyzer)
        manager.AnalysisManager.register_analyzer(MockAnalyzer2)
        manager.AnalysisManager.register_analyzer(MockAnalyzer3)
        manager.AnalysisManager.register_analyzer(MockAnalyzer4)

        analyzers = manager.AnalysisManager.get_analyzers()
        analyzer_names_list = [x for x, _ in analyzers]
        self.assertEqual(len(analyzer_names_list), 4)
        self.assertIn("mockanalyzer", analyzer_names_list)

        # pylint: disable=protected-access
        analyzers_to_run = [
            "mockanalyzer",
            "mockanalyzer2",
            "mockanalyzer3",
            "mockanalyzer4",
        ]
        dependency_tree = manager.AnalysisManager._build_dependencies(analyzers_to_run)
        self.assertEqual(len(dependency_tree), 3)
        self.assertIn("mockanalyzer", dependency_tree[0])
        self.assertIn("mockanalyzer3", dependency_tree[0])
        self.assertIn("mockanalyzer2", dependency_tree[1])
        self.assertIn("mockanalyzer4", dependency_tree[2])

        manager.AnalysisManager.clear_registration()
        manager.AnalysisManager.register_analyzer(MockAnalyzerFail1)
        manager.AnalysisManager.register_analyzer(MockAnalyzerFail2)
        with self.assertRaises(KeyError):
            analyzers = manager.AnalysisManager.get_analyzers()
            _ = list(analyzers)

    def test_get_analyzer(self):
        """Test to get analyzer class from registry."""
        analyzer_class = manager.AnalysisManager.get_analyzer("mockanalyzer")
        self.assertEqual(analyzer_class, MockAnalyzer)

    def test_register_analyzer(self):
        """Test so we raise KeyError when analyzer is already registered."""
        self.assertRaises(
            KeyError, manager.AnalysisManager.register_analyzer, MockAnalyzer
        )
