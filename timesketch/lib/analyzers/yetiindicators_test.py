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
    "12345": {
        "id": "12345",
        "name": "Random regex",
        "pattern": "[0-9a-f]",
        "compiled_regexp": re.compile("[0-9a-f]"),
        "type": "regex",
    }
}

MOCK_YETI_NEIGHBORS = [
    {
        "id": "98765",
        "name": "Bad malware",
        "type": "malware",
    }
]

MATCHING_DOMAIN_MESSAGE = {"message": "baddomain.com"}
OK_DOMAIN_MESSAGE = {"message": "okdomain.com"}


class TestYetiIndicators(BaseTest):
    """Tests the functionality of the YetiIndicators analyzer."""

    def setUp(self):
        super().setUp()
        current_app.config["YETI_API_ROOT"] = "blah"
        current_app.config["YETI_API_KEY"] = "blah"

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch(
        "timesketch.lib.analyzers.yetiindicators." "YetiIndicators.get_neighbors"
    )
    @mock.patch(
        "timesketch.lib.analyzers.yetiindicators." "YetiIndicators.get_indicators"
    )
    def test_indicator_match(self, mock_get_indicators, mock_get_neighbors):
        """Test that ES queries for indicators are correctly built."""
        analyzer = yetiindicators.YetiIndicators("test_index", 1)
        analyzer.datastore.client = mock.Mock()
        analyzer.intel = MOCK_YETI_INTEL
        mock_get_neighbors.return_value = MOCK_YETI_NEIGHBORS

        event = copy.deepcopy(MockDataStore.event_dict)
        event["_source"].update(MATCHING_DOMAIN_MESSAGE)
        analyzer.datastore.import_event("test_index", event["_source"], "0")

        message = analyzer.run()
        self.assertEqual(
            message,
            ("1 events matched 1 new indicators. Found: Random incident:x-incident"),
        )
        mock_get_indicators.assert_called_once()
        mock_get_neighbors.assert_called_once()

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch(
        "timesketch.lib.analyzers.yetiindicators." "YetiIndicators.get_neighbors"
    )
    @mock.patch(
        "timesketch.lib.analyzers.yetiindicators." "YetiIndicators.get_indicators"
    )
    def test_indicator_nomatch(self, mock_get_indicators, mock_get_neighbors):
        """Test that ES queries for indicators are correctly built."""
        analyzer = yetiindicators.YetiIndicators("test_index", 1)
        analyzer.datastore.client = mock.Mock()
        analyzer.intel = MOCK_YETI_INTEL
        mock_get_neighbors.return_value = MOCK_YETI_NEIGHBORS

        message = analyzer.run()
        self.assertEqual(message, "No indicators were found in the timeline.")
        mock_get_indicators.assert_called_once()
        mock_get_neighbors.asset_called_once()

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_slug(self):
        analyzer = yetiindicators.YetiIndicators("test_index", 1)
        mock_event = mock.Mock()
        mock_event.get_comments.return_value = []
        analyzer.mark_event(
            MOCK_YETI_INTEL["12345"],
            mock_event,
            MOCK_YETI_NEIGHBORS,
        )
        # The name of the entity is "Random incident"
        mock_event.add_tags.assert_called_once_with(["Bad malware"])
