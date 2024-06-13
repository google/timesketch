"""Test for MISP"""

import copy
import mock

from flask import current_app

from timesketch.lib.analyzers.contrib import misp_analyzer
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

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

QUERY_MISP = {
    "query_string": "filename:*",
    "attr": "filename",
    "timesketch_attr": "filename",
}


class TestMisp(BaseTest):
    """Tests the functionality of the analyzer."""

    def setUp(self):
        super().setUp()
        current_app.config["MISP_URL"] = "https://test.com/"
        current_app.config["MISP_API_KEY"] = "test"

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch("requests.post")
    def test_attr_match(self, mock_requests_post):
        """Test match"""
        analyzer = misp_analyzer.MispAnalyzer("test_index", 1, None, **QUERY_MISP)
        analyzer.datastore.client = mock.Mock()
        mock_requests_post.return_value.status_code = 200
        mock_requests_post.return_value.json.return_value = MISP_ATTR

        event = copy.deepcopy(MockDataStore.event_dict)
        event["_source"].update(MATCHING_MISP)
        analyzer.datastore.import_event("test_index", event["_source"], "0")

        message = analyzer.run()
        self.assertEqual(
            message,
            ("[filename] MISP Match: 1"),
        )
        mock_requests_post.assert_called_with(
            "https://test.com//attributes/restSearch/",
            json={"returnFormat": "json", "value": ["test.txt"], "type": "filename"},
            headers={"Authorization": "test"},
            verify=False,
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch("requests.post")
    def test_attr_nomatch(self, mock_requests_post):
        """Test no match"""
        analyzer = misp_analyzer.MispAnalyzer("test_index", 1, None, **QUERY_MISP)
        analyzer.datastore.client = mock.Mock()
        mock_requests_post.return_value.status_code = 200
        mock_requests_post.return_value.json.return_value = {
            "response": {"Attribute": []}
        }

        event = copy.deepcopy(MockDataStore.event_dict)
        event["_source"].update(MATCHING_MISP)
        analyzer.datastore.import_event("test_index", event["_source"], "0")

        message = analyzer.run()
        self.assertEqual(
            message,
            ("[filename] MISP Match: 0"),
        )
        mock_requests_post.assert_called_with(
            "https://test.com//attributes/restSearch/",
            json={"returnFormat": "json", "value": ["test.txt"], "type": "filename"},
            headers={"Authorization": "test"},
            verify=False,
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_get_kwargs(self):
        analyzer_init = misp_analyzer.MispAnalyzer("test_index", 1)
        queries = analyzer_init.get_kwargs()
        self.assertIsNotNone(queries)
        self.assertGreaterEqual(len(queries), 1)
        for query in queries:
            query_list_keys = query.keys()
            self.assertEqual(len(query_list_keys), 3)
            self.assertEqual(
                list(query_list_keys), ["query_string", "attr", "timesketch_attr"]
            )
