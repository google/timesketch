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

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_readOnly_tagging(self):
        """Tests that AWS CloudTrail readOnly events are tagged as expected."""
        analyzer = aws_cloudtrail.AwsCloudtrailSketchPlugin("test_index", 1)
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        source_attributes = {
            "data_type": "aws:cloudtrail:entry",
            "cloud_trail_event": '{"readOnly":true}',
        }

        datastore.import_event("test_index", source_attributes, "0")
        analyzer.run()
        self.assertEqual(analyzer.tagged_events["0"]["tags"], ["readOnly"])

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_unauthorizedAPICall_tagging(self):
        """Tests that AWS CloudTrail AccessDenied events are tagged as expected."""
        analyzer = aws_cloudtrail.AwsCloudtrailSketchPlugin("test_index", 1)
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        source_attributes = {
            "data_type": "aws:cloudtrail:entry",
            "cloud_trail_event": '{"errorCode":"AccessDenied"}',
        }

        datastore.import_event("test_index", source_attributes, "0")
        analyzer.run()
        self.assertEqual(analyzer.tagged_events["0"]["tags"], ["UnauthorizedAPICall"])

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_failedLoginNonExistentIAMUser_tagging(self):
        """Tests that AWS CloudTrail FailedLoginNonExistentIAMUser events are tagged as expected."""
        analyzer = aws_cloudtrail.AwsCloudtrailSketchPlugin("test_index", 1)
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        source_attributes = {
            "data_type": "aws:cloudtrail:entry",
            "cloud_trail_event": '{"userIdentity": {"userName": "HIDDEN_DUE_TO_SECURITY_REASONS"},"errorMessage": "No username found in supplied account"}',
        }

        datastore.import_event("test_index", source_attributes, "0")
        analyzer.run()
        self.assertEqual(
            analyzer.tagged_events["0"]["tags"], ["FailedLoginNonExistentIAMUser"]
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_network_tagging(self):
        """Tests that AWS CloudTrail NetworkChanged events are tagged as expected."""
        analyzer = aws_cloudtrail.AwsCloudtrailSketchPlugin("test_index", 1)
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        source_attributes = {
            "data_type": "aws:cloudtrail:entry",
            "event_name": "AuthorizeSecurityGroupIngress",
        }

        datastore.import_event("test_index", source_attributes, "0")
        analyzer.run()
        self.assertEqual(
            sorted(analyzer.tagged_events["0"]["tags"]),
            sorted(["NetworkChanged", "SG"]),
        )

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_consoleLogin_tagging(self):
        """Tests that AWS CloudTrail ConsoleLogin events are tagged as expected."""
        analyzer = aws_cloudtrail.AwsCloudtrailSketchPlugin("test_index", 1)
        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        source_attributes = {
            "data_type": "aws:cloudtrail:entry",
            "event_name": "ConsoleLogin",
        }

        datastore.import_event("test_index", source_attributes, "0")
        analyzer.run()
        self.assertEqual(analyzer.tagged_events["0"]["tags"], ["ConsoleLogin"])
