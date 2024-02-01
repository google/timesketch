"""Tests for Chain analyzer."""

from __future__ import unicode_literals

import uuid

import mock

from timesketch.lib import emojis
from timesketch.lib import testlib

from timesketch.lib.analyzers import chain
from timesketch.lib.analyzers.chain_plugins import interface
from timesketch.lib.analyzers.chain_plugins import manager


class FakeEvent(object):
    """Fake event object."""

    def __init__(self, source_dict):
        self.event_id = uuid.uuid4().hex
        self.attributes = {}
        self.emojis = []
        self.source = source_dict

    def add_attributes(self, attributes):
        for key, value in iter(attributes.items()):
            self.attributes[key] = value

    def add_emojis(self, emoji_codes):
        self.emojis.extend(emoji_codes)

    def commit(self):
        pass


class FakeAnalyzer(chain.ChainSketchPlugin):
    """Fake analyzer object used for "finding events"."""

    def event_stream(
        self,
        query_string=None,
        query_filter=None,
        query_dsl=None,
        indices=None,
        return_fields=None,
        scroll=True,
    ):
        """Yields few test events."""
        event_one = FakeEvent({"url": "http://minsida.biz", "stuff": "foo"})

        yield event_one

        event_two = FakeEvent(
            {
                "url": "http://onnursida.biz",
                "stuff": "bar",
                "annad": "lesa_um_mig_herna",
                "tenging": "ekki satt",
            }
        )

        yield event_two

        event_three = FakeEvent(
            {"tenging": "klarlega", "gengur": "bara svona lala", "url": "N/A"}
        )

        yield event_three


class FakeChainPlugin(interface.BaseChainPlugin):
    """Fake chain plugin."""

    NAME = "fake_chain"
    DESCRIPTION = "Fake plugin for the chain analyzer."
    SEARCH_QUERY = "give me all the data"
    EVENT_FIELDS = ["kedjur"]
    ALL_EVENTS = []

    def process_chain(self, base_event):
        return True

    def get_chained_events(self, base_event):
        """Implementation of the chained events."""
        url = base_event.source.get("url", "")
        tenging = base_event.source.get("tenging", "")
        self.ALL_EVENTS.append(base_event)

        if url == "http://onnursida.biz":
            event_a = FakeEvent({"domain": "minn en ekki thinn"})
            self.ALL_EVENTS.append(event_a)
            yield event_a

            event_b = FakeEvent({"some_bar": "foo"})
            self.ALL_EVENTS.append(event_b)
            yield event_b
        elif tenging == "klarlega":
            event_a = FakeEvent({"stuff": "yes please"})
            self.ALL_EVENTS.append(event_a)
            yield event_a
        else:
            events = [
                FakeEvent({"a": "q"}),
                FakeEvent({"b": "w"}),
                FakeEvent({"c": "e"}),
                FakeEvent({"d": "r"}),
                FakeEvent({"e": "t"}),
                FakeEvent({"f": "y"}),
            ]
            self.ALL_EVENTS.extend(events)
            for event in events:
                yield event


class TestChainAnalyzer(testlib.BaseTest):
    """Tests the functionality of the analyzer."""

    @mock.patch(
        "timesketch.lib.analyzers.interface.OpenSearchDataStore", testlib.MockDataStore
    )
    def test_get_chains(self):
        """Test the chain."""

        for plugin in manager.ChainPluginsManager.get_plugins(None):
            manager.ChainPluginsManager.deregister_plugin(plugin)

        manager.ChainPluginsManager.register_plugin(FakeChainPlugin)

        analyzer = FakeAnalyzer("test_index", sketch_id=1)
        analyzer.datastore.client = mock.Mock()

        plugins = getattr(analyzer, "_chain_plugins")
        self.assertEqual(len(plugins), 1)

        plugin = plugins[0]
        self.assertIsInstance(plugin, interface.BaseChainPlugin)

        analyzer_result = analyzer.run()
        expected_result = (
            "3 base events annotated with a chain UUID for 3 chains "
            "for a total of 9 events. [fake_chain] 9"
        )
        self.assertEqual(analyzer_result, expected_result)

        link_emoji = emojis.get_emoji("LINK")
        for event in plugin.ALL_EVENTS:
            attributes = event.attributes
            chains = attributes.get("chains", [])
            for event_chain in chains:
                plugin = event_chain.get("plugin", "")
                self.assertEqual(plugin, "fake_chain")

            event_emojis = event.emojis
            self.assertEqual(len(event_emojis), 1)
            self.assertEqual(event_emojis[0], link_emoji)
