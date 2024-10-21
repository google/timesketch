"""Tests for AwsCloudtrailPlugin."""

from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers.contrib import aws_cloudtrail
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestAwsCloudtrailPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def __init__(self, *args, **kwargs):
        super(TestAwsCloudtrailPlugin, self).__init__(*args, **kwargs)

    # Mock the Elasticsearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_event_tagging(self):
        """Tests that AWS CloudTrail events are tagged as expected."""
        analyzer = aws_cloudtrail.AwsCloudtrailSketchPlugin("test_index", 1)
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
            "data_type": "aws:cloudtrail:entry",
            "cloud_trail_event": '{"readOnly":true}',
        }

        datastore.import_event("test_index", source_attributes, "0")
        analyzer.run()
        self.assertEqual(analyzer.tagged_events["0"]["tags"], ["readOnly"])

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_network_tagging(self):
        """Tests that AWS CloudTrail events are tagged as expected."""
        analyzer = aws_cloudtrail.AwsCloudtrailSketchPlugin("test_index", 1)
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
            "data_type": "aws:cloudtrail:entry",
            "event_name": "AuthorizeSecurityGroupIngress",
        }

        datastore.import_event("test_index", source_attributes, "0")
        analyzer.run()
        self.assertEqual(
            sorted(analyzer.tagged_events["0"]["tags"]),
            sorted(["NetworkChanged", "SGChanged"]),
        )
