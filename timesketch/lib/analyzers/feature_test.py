"""Unit tests for FeatureSketchPlugin."""

import os
import yaml

import mock

from timesketch.lib.analyzers.feature import FeatureSketchPlugin
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestFeatureSketchPlugin(BaseTest):
    """Class to test FeatureSketchPlugin class methods."""

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
        result = plugin_object.run()
        self.assertTrue(result)
