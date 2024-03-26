"""Tests for ThreatintelPlugin."""

import json
import mock

from flask import current_app

from timesketch.lib.analyzers import yetiindicators
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


MOCK_YETI_ENTITY_REQUEST = {
    "entities": [
        {
            "type": "malware",
            "name": "xmrig",
            "description": "coin miner",
            "created": "2024-02-16T12:10:48.670039Z",
            "modified": "2024-02-16T12:10:48.670040Z",
            "kill_chain_phases": [],
            "aliases": [],
            "family": "miner",
            "id": "2152646",
            "tags": {},
            "root_type": "entity",
        }
    ],
    "total": 1,
}

MOCK_YETI_NEIGHBORS_RESPONSE = {
    "vertices": {
        "indicators/2152802": {
            "name": "typo'd dhcpd",
            "type": "regex",
            "description": "Random description",
            "created": "2024-02-16T12:12:14.564723Z",
            "modified": "2024-02-16T12:12:14.564729Z",
            "valid_from": "2024-02-16T12:12:14.564730Z",
            "valid_until": "2024-03-17T12:12:14.564758Z",
            "pattern": "/usr/bin/dhpcd",
            "location": "filesystem",
            "diamond": "victim",
            "kill_chain_phases": [],
            "relevant_tags": ["xmrig", "malware"],
            "id": "2152802",
            "root_type": "indicator",
        }
    },
    "paths": [
        [
            {
                "source": "entities/2152646",
                "target": "indicators/2152802",
                "type": "dropped in",
                "description": "",
                "created": "2024-02-16T12:28:52.731740Z",
                "modified": "2024-02-16T12:28:52.731747Z",
                "id": "2153330",
            }
        ]
    ],
    "total": 1,
}


MATCHING_PATH_MESSAGE = {
    "__ts_timeline_id": 1,
    "es_index": "",
    "es_id": "",
    "label": "",
    "timestamp": 1410895419859714,
    "timestamp_desc": "",
    "datetime": "2014-09-16T19:23:40+00:00",
    "source_short": "",
    "source_long": "",
    "message": "/usr/bin/dhpcd",
}


class TestYetiIndicators(BaseTest):
    """Tests the functionality of the YetiIndicators analyzer."""

    def setUp(self):
        super().setUp()
        current_app.config["YETI_API_ROOT"] = "blah"
        current_app.config["YETI_API_KEY"] = "blah"
        yetiindicators.NEIGHBOR_CACHE = {}

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch(
        "timesketch.lib.analyzers.yetiindicators."
        "YetiBaseAnalyzer._get_neighbors_request"
    )
    @mock.patch(
        "timesketch.lib.analyzers.yetiindicators."
        "YetiBaseAnalyzer._get_entities_request"
    )
    def test_indicator_match(self, mock_get_entities, mock_get_neighbors):
        """Test that ES queries for indicators are correctly built."""
        analyzer = yetiindicators.YetiMalwareIndicators("test_index", 1, 123)
        analyzer.datastore.client = mock.Mock()
        mock_get_entities.return_value = MOCK_YETI_ENTITY_REQUEST
        mock_get_neighbors.return_value = MOCK_YETI_NEIGHBORS_RESPONSE

        analyzer.datastore.import_event("test_index", MATCHING_PATH_MESSAGE, "0")

        message = json.loads(analyzer.run())
        self.assertEqual(
            message["result_summary"],
            (
                "1 events matched 1 indicators (out of 1 processed).\n\n"
                "Entities found: xmrig:malware"
            ),
        )
        mock_get_entities.assert_called_once()
        mock_get_neighbors.assert_called_once()
        self.assertEqual(
            sorted(analyzer.tagged_events["0"]["tags"]),
            sorted(["malware", "xmrig"]),
        )

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch(
        "timesketch.lib.analyzers.yetiindicators."
        "YetiBaseAnalyzer._get_neighbors_request"
    )
    @mock.patch(
        "timesketch.lib.analyzers.yetiindicators."
        "YetiBaseAnalyzer._get_entities_request"
    )
    def test_indicator_nomatch(self, mock_get_entities, mock_get_neighbors):
        """Test that ES queries for indicators are correctly built."""
        analyzer = yetiindicators.YetiMalwareIndicators("test_index", 1, 123)
        analyzer.datastore.client = mock.Mock()
        mock_get_entities.return_value = MOCK_YETI_ENTITY_REQUEST
        mock_get_neighbors.return_value = MOCK_YETI_NEIGHBORS_RESPONSE

        message = json.loads(analyzer.run())
        self.assertEqual(
            message["result_summary"],
            "No indicators were found in the timeline.",
        )
        mock_get_entities.assert_called_once()
        mock_get_neighbors.asset_called_once()

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_slug(self):
        """Tests that slugs are formed correctly."""
        analyzer = yetiindicators.YetiMalwareIndicators("test_index", 1, 123)
        mock_event = mock.Mock()
        mock_event.get_comments.return_value = []
        analyzer.mark_event(
            MOCK_YETI_NEIGHBORS_RESPONSE["vertices"]["indicators/2152802"],
            mock_event,
            MOCK_YETI_ENTITY_REQUEST["entities"],
        )
        mock_event.add_tags.assert_called_once()
        self.assertIn(
            sorted(["xmrig", "malware"]),
            [sorted(x) for x in mock_event.add_tags.call_args[0]],
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_build_query_from_regexp(self):
        """Tests that that queries are correctly built from regex indicators."""
        analyzer = yetiindicators.YetiMalwareIndicators("test_index", 1, 123)
        query = analyzer.build_query_from_regexp(
            {
                "name": "random regex",
                "type": "regex",
                "description": "Random description",
                "created": "2024-02-16T12:12:14.564723Z",
                "modified": "2024-02-16T12:12:14.564729Z",
                "valid_from": "2024-02-16T12:12:14.564730Z",
                "valid_until": "2024-03-17T12:12:14.564758Z",
                "pattern": r"this_is_my_{2,3}regex[0-9]",
                "location": "filesystem",
                "diamond": "victim",
                "kill_chain_phases": [],
                "relevant_tags": ["regex"],
                "id": "2152802",
                "root_type": "indicator",
            }
        )
        self.assertEqual(
            query,
            {
                "query": {
                    "bool": {
                        "should": [
                            {
                                "regexp": {
                                    "filename.keyword": {
                                        "value": r".*this_is_my_{2,3}regex[0-9].*",
                                        "case_insensitive": True,
                                    }
                                }
                            },
                            {
                                "regexp": {
                                    "display_name.keyword": {
                                        "value": r".*this_is_my_{2,3}regex[0-9].*",
                                        "case_insensitive": True,
                                    }
                                }
                            },
                        ]
                    }
                }
            },
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_build_query_from_sigma(self):
        """Tests that that queries are correctly built from sigma indicators."""
        analyzer = yetiindicators.YetiMalwareIndicators("test_index", 1, 123)
        sigma_pattern = """id: asd
title: test
description: test
status: experimental
date: 2024/01/01
author: 'tomchop'
references:
  - blah
logsource:
    category: winprefetch
    service: winprefetch
detection:
    selection1:
      Image|endswith:
        - '\\rundll32.exe'
    condition: selection1
falsepositives:
    - Uknown
level: medium
tags:
    - blah
"""
        query = analyzer.build_query_from_sigma(
            {
                "name": "random sigma",
                "type": "sigma",
                "description": "Random description",
                "created": "2024-02-16T12:12:14.564723Z",
                "modified": "2024-02-16T12:12:14.564729Z",
                "valid_from": "2024-02-16T12:12:14.564730Z",
                "valid_until": "2024-03-17T12:12:14.564758Z",
                "pattern": sigma_pattern,
                "location": "not_used",
                "diamond": "victim",
                "kill_chain_phases": [],
                "relevant_tags": ["sigma"],
                "id": "2152802",
                "root_type": "indicator",
            }
        )
        self.assertEqual(
            query,
            {
                "query": {
                    "query_string": {
                        "query": (
                            '(data_type:"windows\\:prefetch\\:execution" '
                            'AND message:("\\\\rundll32.exe"))'
                        )
                    }
                }
            },
        )
