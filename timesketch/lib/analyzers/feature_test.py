# Copyright 2023 Google Inc. All rights reserved.
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
"""Unit tests for feature extraction."""

import os
import textwrap
from typing import List, Dict

import yaml
import mock

from timesketch.lib.analyzers.feature import FeatureSketchPlugin
from timesketch.lib.analyzers.sequence_sessionizer_test import _create_eventObj
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestFeatureSketchPlugin(BaseTest):
    """A class to test FeatureSketchPlugin class methods."""

    EXPECTED_RESULT = textwrap.dedent(
        """1 features extracted using feature security_4624_v2"""
    )

    def test_winevt_config(self):
        """Tests Windows event log feature extraction config."""
        config_file = os.path.join("data", "winevt_features.yaml")
        self.assertTrue(os.path.isfile(config_file))

        with open(config_file, "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh)

        self.assertIsInstance(config, dict)

        for key, value in config.items():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, dict)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_run(self) -> None:
        """Tests run method."""
        plugin_object = FeatureSketchPlugin(
            index_name="test", sketch_id=1, timeline_id=1
        )

        plugin_object.datastore.client = mock.Mock()
        datastore = plugin_object.datastore

        self._create_mock_events(datastore)

        plugin_object.plugin_name = "winevt_feature_extraction"
        plugin_object.feature_name = "security_4624_v2"
        plugin_object.feature_config = self._get_feature_config(
            "winevt_features.yaml", plugin_object.feature_name
        )

        result = plugin_object.run()
        self.assertEqual(self.EXPECTED_RESULT, result)

    def _get_feature_config(self, file_name: str, feature_name: str) -> Dict:
        """Returns the feature configuration.

        Args:
            file_name (str): Feature configuration file name.
            feature_name (str): Feature name in the configuration file.

        Returns:
            Dict: Configuration parameter for the feature.
        """
        path = os.path.join("data", file_name)

        with open(path, "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh)

        for name, config in config.items():
            if name == feature_name:
                return config

        return None  # Return None if no match.

    def _create_mock_events(self, datastore) -> None:
        """Creates mock events."""
        events: List[Dict] = []
        events.extend(self._create_mock_winevt_events())

        # Adding new events
        # Use the following example to extend the events add add mock events.
        # Example: events.extend(self._create_mock_xyz_events())

        event_id = 0
        timestamp = 1672097149681987

        for event in events:
            _create_eventObj(datastore, event_id, timestamp, event)
            event_id += 1
            timestamp += 1000000

    def _create_mock_winevt_events(self) -> List[Dict]:
        """Creates mock Windows event log events.

        Returns:
            List[Dict]: A list of dictionary containing Windows event logs.
        """
        events = []

        security_4624_v2_event = {
            "source_name": "Microsoft-Windows-Security-Auditing",
            "event_identifier": 4624,
            "event_version": 2,
            "strings": [
                "S-1-5-18",
                "WIN-MDLVGLNGOM0$",
                "WORKGROUP",
                "0x00000000000003e7",
                "S-1-5-18",
                "SYSTEM",
                "NT AUTHORITY",
                "0x00000000000003e7",
                "5",
                "Advapi ",
                "Negotiate",
                "-",
                "{00000000-0000-0000-0000-000000000000}",
                "-",
                "-",
                "0",
                "0x000000000000026c",
                "C:\\Windows\\System32\\services.exe",
                "-",
                "-",
                "%%1833",
                "-",
                "-",
                "-",
                "%%1843",
                "0x0000000000000000",
                "%%1842",
            ],
        }
        events.append(security_4624_v2_event)

        return events
