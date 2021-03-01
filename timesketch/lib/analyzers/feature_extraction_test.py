"""Tests for FeatureExtractionPlugin."""
from __future__ import unicode_literals

import os
import re
import yaml

import mock

from timesketch.lib import emojis
from timesketch.lib.analyzers import feature_extraction
from timesketch.lib.testlib import BaseTest

from timesketch.lib.testlib import MockDataStore

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
        config_file = os.path.join('data', 'features.yaml')
        self.assertTrue(os.path.isfile(config_file))

        with open(config_file) as fh:
            config = yaml.safe_load(fh)

        self.assertIsInstance(config, dict)

        for key, value in iter(config.items()):
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, dict)
            self._config_validation(value)

    # Mock the Elasticsearch datastore.
    @mock.patch(
        'timesketch.lib.analyzers.interface.ElasticsearchDataStore',
        MockDataStore)
    def test_get_attribute_value(self):
        """Test function _get_attribute_value()."""
        analyzer = feature_extraction.FeatureExtractionSketchPlugin(
            'test_index', 1)
        current_val = ['hello']
        extracted_value = ['hello']
        # pylint: disable=protected-access
        new_val = analyzer._get_attribute_value(
            current_val=current_val,
            extracted_value=extracted_value,
            keep_multi=True,
            merge_values=True,
            type_list=True)
        new_val.sort()

        self.assertEqual(new_val, ['hello'])

        current_val = ['hello']
        extracted_value = ['hello2', 'hello3']
        # pylint: disable=protected-access
        new_val = analyzer._get_attribute_value(
            current_val,
            extracted_value,
            True,
            True,
            True)
        new_val.sort()

        self.assertEqual(new_val, ['hello', 'hello2', 'hello3'])

        current_val = ['hello']
        extracted_value = ['hello2', 'hello3']
        # pylint: disable=protected-access
        new_val = analyzer._get_attribute_value(
            current_val,
            extracted_value,
            False,
            True,
            True)
        new_val.sort()

        self.assertEqual(new_val, ['hello', 'hello2'])

        current_val = ['hello']
        extracted_value = ['hello2', 'hello3']
        # pylint: disable=protected-access
        new_val = analyzer._get_attribute_value(
            current_val,
            extracted_value,
            False,
            False,
            True)
        new_val.sort()

        self.assertEqual(new_val, ['hello2'])

        current_val = ['hello']
        extracted_value = ['hello2', 'hello3']
        # pylint: disable=protected-access
        new_val = analyzer._get_attribute_value(
            current_val,
            extracted_value,
            True,
            False,
            True)
        new_val.sort()

        self.assertEqual(new_val, ['hello2', 'hello3'])

        current_val = 'hello'
        extracted_value = ['hello2', 'hello3']
        # pylint: disable=protected-access
        new_val = analyzer._get_attribute_value(
            current_val,
            extracted_value,
            True,
            True,
            False)

        self.assertEqual(new_val, 'hello,hello2,hello3')

        current_val = 'hello'
        extracted_value = ['hello2', 'hello3']
        # pylint: disable=protected-access
        new_val = analyzer._get_attribute_value(
            current_val,
            extracted_value,
            False,
            True,
            False)

        self.assertEqual(new_val, 'hello,hello2')

        current_val = 'hello'
        extracted_value = ['hello2', 'hello3']
        # pylint: disable=protected-access
        new_val = analyzer._get_attribute_value(
            current_val,
            extracted_value,
            True,
            False,
            False)

        self.assertEqual(new_val, 'hello2,hello3')

        current_val = 'hello'
        extracted_value = ['hello2', 'hello3']
        # pylint: disable=protected-access
        new_val = analyzer._get_attribute_value(
            current_val,
            extracted_value,
            False,
            False,
            False)

        self.assertEqual(new_val, 'hello2')
