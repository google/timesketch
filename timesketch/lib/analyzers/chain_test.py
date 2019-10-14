"""Tests for Chain analyzer."""
from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers import chain
from timesketch.lib.analyzers.chain_plugins import interface
from timesketch.lib.analyzers.chain_plugins import manager

from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class FakeEvent(object):
    """Fake event object."""

    def __init__(self, source_dict):
        self.source = source_dict

    def add_attributes(self, unusued_attributes):
        pass

    def add_emojis(self, unused_list):
        pass

    def commit(self):
        pass


class FakeAnalyzer(chain.ChainSketchPlugin):
    """Fake analyzer object used for "finding events"."""

    def event_stream(self, search_query, return_fields):
        """Yields few test events."""
        event_one = FakeEvent({
            'url': 'http://minsida.biz',
            'stuff': 'foo'})

        yield event_one

        event_two = FakeEvent({
            'url': 'http://onnursida.biz',
            'stuff': 'bar',
            'annad': 'lesa_um_mig_herna',
            'tenging': 'ekki satt'})

        yield event_two

        event_three = FakeEvent({
            'tenging': 'klarlega',
            'gengur': 'bara svona lala',
            'url': 'N/A'})

        yield event_three


class FakeChainPlugin(interface.BaseChainPlugin):
    """Fake chain plugin."""

    NAME = 'fake_chain'
    DESCRIPTION = 'Fake plugin for the chain analyzer.'
    SEARCH_QUERY = 'give me all the data'
    EVENT_FIELDS = ['kedjur']

    def ProcessChain(self, base_event):
        return True

    def GetChainedEvents(self, base_event):
        url = base_event.source.get('url', '')
        tenging = base_event.source.get('tenging', '')

        if url == 'http://onnursida.biz':
            yield FakeEvent({'domain': 'minn en ekki thinn'})
            yield FakeEvent({'some_bar': 'foo'})
        elif tenging == 'klarlega':
            yield FakeEvent({'stuff': 'yes please'})
        else:
            yield FakeEvent({'a': 'q'})
            yield FakeEvent({'b': 'w'})
            yield FakeEvent({'c': 'e'})
            yield FakeEvent({'d': 'r'})
            yield FakeEvent({'e': 't'})
            yield FakeEvent({'f': 'y'})


class TestChainAnalyzer(BaseTest):
    """Tests the functionality of the analyzer."""

    def setUp(self):
        """Setting the test up."""
        for plugin in manager.ChainPluginsManager.GetPlugins(None):
            manager.ChainPluginsManager.DeregisterPlugin(plugin)

        manager.ChainPluginsManager.RegisterPlugin(FakeChainPlugin)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_get_chains(self):
        """Test the chain."""
        analyzer = FakeAnalyzer('test_index', sketch_id=1)
        analyzer.datastore.client = mock.Mock()

        plugins = manager.ChainPluginsManager.GetPlugins(analyzer)
        self.assertEqual(len(plugins), 1)

        plugin = plugins[0]

        #message = analyzer.run()
        #self.assertText(message, 'not right')

