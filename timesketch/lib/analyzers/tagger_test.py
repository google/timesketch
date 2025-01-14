"""Tests for TaggerSketchPlugin."""

import yaml
import mock

from timesketch.lib import emojis
from timesketch.lib.analyzers import tagger
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestTaggerPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def _config_validation(self, config):
        """Validate that all items of a config are valid."""
        query = config.get("query_string", config.get("query_dsl"))
        self.assertIsNotNone(query)
        self.assertIsInstance(query, str)

        emojis_to_add = config.get("emojis")
        if emojis_to_add:
            self.assertIsInstance(emojis_to_add, (list, tuple))
            for emoji_name in emojis_to_add:
                emoji_code = emojis.get_emoji(emoji_name)
                self.assertNotEqual(emoji_code, "")

        tags = config.get("tags")
        if tags:
            self.assertIsInstance(tags, (list, tuple))

        create_view = config.get("create_view")
        if create_view:
            self.assertIsInstance(create_view, bool)

    # TODO: Add tests for the tagger.
    def test_config(self):
        """Tests that the config is valid."""
        test_config = yaml.safe_load(
            """
        place_holder:
          query_string: '*'
          tags: ['place-holder']
          emojis: ['ID_BUTTON']
          """
        )

        self.assertIsInstance(test_config, dict)

        for key, value in iter(test_config.items()):
            self.assertIsInstance(key, str)
            self.assertIsInstance(value, dict)
            self._config_validation(value)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_event_tagging(self):
        """Tests that events are tagged as expected."""
        config = yaml.safe_load(
            """dummy_tagger:
            query_string: '*'
            tags: ['dummyTag']
            save_search: true
            search_name: 'Random test tagging'"""
        )
        analyzer = tagger.TaggerSketchPlugin(
            "test_index", 1, tag_config=config["dummy_tagger"], tag="dummy_tagger"
        )
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        source_attributes = {
            "__ts_timeline_id": 1,
            "es_index": "",
            "es_id": "",
            "label": "",
            "timestamp": 1410895419859714,
            "timestamp_desc": "",
            "datetime": "2014-09-16T19:23:40+00:00",
            "source_short": "",
            "source_long": "",
            "message": "Dummy message",
        }

        datastore.import_event("blah", source_attributes, "0")
        message = analyzer.run()
        self.assertEqual(analyzer.tagged_events["0"]["tags"], ["dummyTag"])
        self.assertEqual(message, "1 events tagged for [dummy_tagger]")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_regex_tagging(self):
        """Tests that regexes matches filter out events to tag."""
        config = yaml.safe_load(
            """regex_tagger:
            query_string: '*'
            tags: ['regexTag']
            save_search: true
            regular_expression: 'exist[0-9]'
            re_attribute: 'message'
            search_name: 'Regex tagging'"""
        )
        analyzer = tagger.TaggerSketchPlugin(
            "test_index", 1, tag_config=config["regex_tagger"], tag="regex_tagger"
        )
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        source_attributes = {
            "__ts_timeline_id": 1,
            "es_index": "",
            "es_id": "",
            "label": "",
            "timestamp": 1410895419859714,
            "timestamp_desc": "",
            "datetime": "2014-09-16T19:23:40+00:00",
            "source_short": "",
            "source_long": "",
            "message": "This event should not be tagged.",
        }
        datastore.import_event("blah", source_attributes.copy(), "0")
        source_attributes["message"] = "This exist1 event should be tagged."
        datastore.import_event("blah", source_attributes.copy(), "1")

        message = analyzer.run()

        self.assertEqual(message, "1 events tagged for [regex_tagger]")
        self.assertNotIn("0", analyzer.tagged_events)
        self.assertEqual(analyzer.tagged_events["1"]["tags"], ["regexTag"])

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_dynamic_tag_extraction(self):
        """Tests that dynamic tags are extracted and converted."""
        config = yaml.safe_load(
            """yara_match_tagger:
            query_string: '_exists_:yara_match AND NOT yara_match.keyword:"-"'
            tags: ['yara', '$yara_match']
            modifiers: ['split']
            save_search: true
            search_name: 'Yara rule matches'"""
        )
        analyzer = tagger.TaggerSketchPlugin(
            "test_index",
            1,
            tag_config=config["yara_match_tagger"],
            tag="yara_match_tagger",
        )
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        source_attributes = {
            "__ts_timeline_id": 1,
            "es_index": "",
            "es_id": "",
            "label": "",
            "timestamp": 1410895419859714,
            "timestamp_desc": "",
            "datetime": "2014-09-16T19:23:40+00:00",
            "source_short": "",
            "source_long": "",
            "message": "Dummy message",
            "yara_match": "rule1 rule2",
        }

        datastore.import_event("blah", source_attributes, "0")
        message = analyzer.run()
        self.assertEqual(
            sorted(analyzer.tagged_events["0"]["tags"]),
            sorted(["yara", "rule2", "rule1"]),
        )
        self.assertEqual(message, "1 events tagged for [yara_match_tagger]")
