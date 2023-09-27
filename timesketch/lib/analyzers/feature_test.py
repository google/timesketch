"""Unit tests for FeatureSketchPlugin."""

import os
import textwrap

from typing import List

import yaml
import mock

from timesketch.lib.analyzers.feature import FeatureSketchPlugin
from timesketch.lib.analyzers.sequence_sessionizer_test import _create_eventObj
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestFeatureSketchPlugin(BaseTest):
    """Class to test FeatureSketchPlugin class methods."""

    EXPECTED_RESULT = textwrap.dedent(
        """1 events updated by security_4624_v0.
1 events updated by security_4624_v1.
1 events updated by security_4624_v2.
1 events updated by security_4625_v0.
1 events updated by security_4634_v0.
1 events updated by security_4648_v0.
1 events updated by security_4688_v2.
1 events updated by security_4720_v0.
1 events updated by security_4728_v0.
1 events updated by security_4732_v0.
1 events updated by system_7045_v0."""
    )

    def test_winevt_config(self):
        """Tests Windows event log feature extraction config."""

        config_file = os.path.join("data", "winevt.yaml")
        self.assertTrue(os.path.isfile(config_file))

        with open(config_file, "r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh)
        self.assertIsInstance(config, dict)

        for key, value in iter(config.items()):
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

        result = plugin_object.run()
        self.assertEqual(self.EXPECTED_RESULT, result)

    def _create_mock_events(self, datastore) -> None:
        """Creates mock events."""

        events = []
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

    def _create_mock_winevt_events(self) -> List[dict]:
        """Creates mock Windows event log events.

        Returns:
            List[dict]: A list of dictionary containing Windows event logs.
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
