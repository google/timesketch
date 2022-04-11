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
"""Tests for story export manager."""

from __future__ import unicode_literals

from timesketch.lib.testlib import BaseTest
from timesketch.lib.stories import manager


class MockStoryExporter(object):
    """Mock story exporter class,"""

    EXPORT_FORMAT = "MockFormat"


class MockStoryExporter2(object):
    """Mock story exporter class,"""

    EXPORT_FORMAT = "MockFormat2"


class MockStoryExporter3(object):
    """Mock story exporter class,"""

    EXPORT_FORMAT = "MockFormat3"


class TestStoryExportManager(BaseTest):
    """Tests for the functionality of the manager module."""

    def setUp(self):
        """Set up the tests."""
        super().setUp()
        manager.StoryExportManager.clear_registration()
        manager.StoryExportManager.register_exporter(MockStoryExporter)

    def test_get_exporters(self):
        """Test to get exporter class objects."""
        exporters = manager.StoryExportManager.get_exporters()
        exporter_list = list(exporters)
        self.assertIsInstance(exporter_list, list)
        exporter_dict = {}
        for name, exporter_class in exporter_list:
            exporter_dict[name] = exporter_class
        self.assertIn("mockformat", exporter_dict)
        exporter_class = exporter_dict.get("mockformat")
        self.assertEqual(exporter_class, MockStoryExporter)

        manager.StoryExportManager.clear_registration()
        exporters = manager.StoryExportManager.get_exporters()
        exporter_list = [x for x, _ in exporters]
        self.assertEqual(exporter_list, [])

        manager.StoryExportManager.clear_registration()
        manager.StoryExportManager.register_exporter(MockStoryExporter)
        manager.StoryExportManager.register_exporter(MockStoryExporter2)
        manager.StoryExportManager.register_exporter(MockStoryExporter3)

        exporters = manager.StoryExportManager.get_exporters()
        exporter_list = [x for x, _ in exporters]
        self.assertEqual(len(exporter_list), 3)
        self.assertIn("mockformat", exporter_list)

    def test_get_exporter(self):
        """Test to get exporter class from registry."""
        exporter_class = manager.StoryExportManager.get_exporter("mockformat")
        self.assertEqual(exporter_class, MockStoryExporter)

    def test_register_exporter(self):
        """Test so we raise KeyError when exporter is already registered."""
        self.assertRaises(
            KeyError, manager.StoryExportManager.register_exporter, MockStoryExporter
        )
