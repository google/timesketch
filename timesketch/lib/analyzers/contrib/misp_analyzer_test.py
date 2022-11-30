"""Test for MISP"""

import copy
import mock

from flask import current_app

from timesketch.lib.analyzers.contrib import misp_analyzer
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

SHA256_VALUE = "ac7233de5daa4ab262e2e751028f56a7e9d5b9e724624c1d55e8b070d8c3cd09"
MISP_ATTR = {
    "response": {
        "Attribute": [
            {
                "event_id": "5",
                "category": "Payload delivery",
                "type": "filename",
                "value": "test.txt",
                "Event": {
                    "org_id": "1",
                    "id": "5",
                    "info": "Hash Test",
                    "uuid": "1f456b69-00c6-4fb0-8d92-709a0061b7d4",
                },
            },
        ]
    }
}
MATCHING_MISP = {"filename": "test.txt"}


class TestMisp(BaseTest):
    """Tests the functionality of the analyzer."""

    def setUp(self):
        super().setUp()
        current_app.config["MISP_URL"] = "blah"
        current_app.config["MISP_API_KEY"] = "blah"

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch(
        "timesketch.lib.analyzers.contrib.misp_analyzer."
        "MispAnalyzer.get_misp_attributes"
    )
    def test_attr_match(self, mock_get_misp_attributes):
        """Test match"""
        analyzer = misp_analyzer.MispAnalyzer("test_index", 1)
        analyzer.misp_url = "blah"
        analyzer.misp_api_key = "blah"
        analyzer.datastore.client = mock.Mock()
        mock_get_misp_attributes.return_value = MISP_ATTR["response"]["Attribute"]

        event = copy.deepcopy(MockDataStore.event_dict)
        event["_source"].update(MATCHING_MISP)
        analyzer.datastore.import_event("test_index", event["_source"], "0")

        message = analyzer.run()
        self.assertEqual(
            message,
            ("MISP Match: 1"),
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch(
        "timesketch.lib.analyzers.contrib.misp_analyzer."
        "MispAnalyzer.get_misp_attributes"
    )
    def test_attr_nomatch(self, mock_get_misp_attributes):
        """Test no match"""
        analyzer = misp_analyzer.MispAnalyzer("test_index", 1)
        analyzer.misp_url = "blah"
        analyzer.misp_api_key = "blah"
        analyzer.datastore.client = mock.Mock()
        mock_get_misp_attributes.return_value = []

        event = copy.deepcopy(MockDataStore.event_dict)
        event["_source"].update(MATCHING_MISP)
        analyzer.datastore.import_event("test_index", event["_source"], "0")

        message = analyzer.run()
        self.assertEqual(
            message,
            ("MISP Match: 0"),
        )
