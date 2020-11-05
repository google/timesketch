"""Tests for IOCExtractionPlugin."""
from __future__ import unicode_literals

import os
import re
import yaml

from timesketch.lib.testlib import BaseTest


class TestIOCExtractionPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def _config_validation(self, config):
        """Validate that all items of a config are valid."""
        query = config.get('path_file_ioc')
        self.assertIsNotNone(path_file_ioc)
        self.assertIsInstance(path_file_ioc, str)

        attributes = config.get('attributes')
        if tags:
            self.assertIsInstance(attributes, (list, tuple))

        attributes_contains = config.get('attributes_contains')
        if attributes_contains:
            self.assertIsInstance(attributes, (list, tuple))
    
        store_as = config.get('store_as')
        self.assertIsNotNone(store_as)

        expression = config.get('match_re')
        self.assertIsNotNone(expression)
        try:
            _ = re.compile(expression)
        except re.error as exception:
            self.assertIsNone(exception)

        tags = config.get('tags')
        if tags:
            self.assertIsInstance(tags, (list, tuple))

    # TODO: Add tests for the ioc extraction.
    def test_config(self):
        """Tests that the config file is valid."""
        config_file = os.path.join('data', 'ioc_extract.yaml')
        self.assertTrue(os.path.isfile(config_file))

        with open(config_file) as fh:
            config = yaml.safe_load(fh)

        self.assertIsInstance(config, dict)

        for key, value in iter(config.items()):
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, dict)
            self._config_validation(value)
