"""Tests for FeatureExtractionPlugin."""
from __future__ import unicode_literals

import os
import re
import yaml

from timesketch.lib import emojis
from timesketch.lib.testlib import BaseTest


class TestFeatureExtractionPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def _config_validation(self, config):
        """Validate that all items of a config are valid."""
        query = config.get('query_string', config.get('query_dsl'))
        self.assertIsNotNone(query)
        self.assertIsInstance(query, str)

        attribute = config.get('attribute')
        self.assertIsNotNone(attribute)

        store_as = config.get('store_as')
        self.assertIsNotNone(store_as)

        expression = config.get('re')
        self.assertIsNotNone(expression)
        try:
            _ = re.compile(expression)
        except re.error as exception:
            self.assertIsNone(exception)

        emojis_to_add = config.get('emojis')
        if emojis_to_add:
            self.assertIsInstance(emojis_to_add, (list, tuple))
            for emoji_name in emojis_to_add:
                emoji_code = emojis.get_emoji(emoji_name)
                self.assertNotEqual(emoji_code, '')

        tags = config.get('tags')
        if tags:
            self.assertIsInstance(tags, (list, tuple))

        create_view = config.get('create_view')
        if create_view:
            self.assertIsInstance(create_view, bool)

        aggregate = config.get('aggregate')
        if aggregate:
            self.assertIsInstance(aggregate, bool)

    # TODO: Add tests for the feature extraction.
    def test_config(self):
        """Tests that the config file is valid."""
        config_file = os.path.join('config', 'features.yaml')
        self.assertTrue(os.path.isfile(config_file))

        with open(config_file) as fh:
            config = yaml.safe_load(fh)

        self.assertIsInstance(config, dict)

        for key, value in config.iteritems():
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, dict)
            self._config_validation(value)
