"""Tests for ThreatintelPlugin."""
from __future__ import unicode_literals

import copy
import re
import mock

from flask import current_app

from timesketch.lib.analyzers import yetiindicators
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

MOCK_YETI_INTEL = {
    'x-regex--6ebc9344-1111-4d65-8bdd-b6dddf613068': {
        'id': 'x-regex--6ebc9344-1111-4d65-8bdd-b6dddf613068',
        'name': 'Secret Fancy Bear c2',
        'pattern': 'baddomain\\.com',
        'compiled_regexp': re.compile('baddomain\\.com'),
        'type': 'x-regex',
    }
}

MOCK_YETI_NEIGHBORS = [{
    'id': 'x-incident--6ebc9344-1111-4d65-8bdd-b6dddf613068',
    'name': 'Random incident',
    'type': 'x-incident',
}]

MATCHING_DOMAIN_MESSAGE = {'message': 'baddomain.com'}
OK_DOMAIN_MESSAGE = {'message': 'okdomain.com'}



class TestThreatintelPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def setUp(self):
        super(TestThreatintelPlugin, self).setUp()
        current_app.config['YETI_API_ROOT'] = 'blah'
        current_app.config['YETI_API_KEY'] = 'blah'

    # Mock the Elasticsearch datastore.
    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    @mock.patch('timesketch.lib.analyzers.yetiindicators.'
                'YetiIndicators.get_neighbors')
    @mock.patch('timesketch.lib.analyzers.yetiindicators.'
                'YetiIndicators.get_indicators')
    def test_indicator_match(self, mock_get_indicators, mock_get_neighbors):
        """Test that ES queries for indicators are correctly built."""
        sessionizer = yetiindicators.YetiIndicators('test_index', 1)
        sessionizer.datastore.client = mock.Mock()
        sessionizer.intel = MOCK_YETI_INTEL
        mock_get_neighbors.return_value = MOCK_YETI_NEIGHBORS

        event = copy.deepcopy(MockDataStore.event_dict)
        event['_source'].update(MATCHING_DOMAIN_MESSAGE)
        sessionizer.datastore.import_event(
            'test_index', event['_type'], event['_source'], '0')

        message = sessionizer.run()
        self.assertEqual(
            message,
            '1 events matched 1 indicators. [Random incident:x-incident]')
        mock_get_indicators.assert_called_once()
        mock_get_neighbors.assert_called_once()

    # Mock the Elasticsearch datastore.
    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    @mock.patch('timesketch.lib.analyzers.yetiindicators.'
                'YetiIndicators.get_neighbors')
    @mock.patch('timesketch.lib.analyzers.yetiindicators.'
                'YetiIndicators.get_indicators')
    def test_indicator_nomatch(self, mock_get_indicators, mock_get_neighbors):
        """Test that ES queries for indicators are correctly built."""
        sessionizer = yetiindicators.YetiIndicators('test_index', 1)
        sessionizer.datastore.client = mock.Mock()
        sessionizer.intel = MOCK_YETI_INTEL
        mock_get_neighbors.return_value = MOCK_YETI_NEIGHBORS

        event = copy.deepcopy(MockDataStore.event_dict)
        event['_source'].update(OK_DOMAIN_MESSAGE)
        sessionizer.datastore.import_event(
            'test_index', event['_type'], event['_source'], '0')

        message = sessionizer.run()
        self.assertEqual(message, 'No indicators were found in the timeline.')
        mock_get_indicators.assert_called_once()
        mock_get_neighbors.assert_not_called()

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def test_slug(self):
        sessionizer = yetiindicators.YetiIndicators('test_index', 1)
        mock_event = mock.Mock()
        sessionizer.mark_event(
            MOCK_YETI_INTEL['x-regex--6ebc9344-1111-4d65-8bdd-b6dddf613068'],
            mock_event,
            MOCK_YETI_NEIGHBORS)
        # The name of the entity is "Random incident"
        mock_event.add_tags.assert_called_once_with(['random-incident'])
