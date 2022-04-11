# Copyright 2021 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for GeoIP analyzer."""
from __future__ import unicode_literals

import mock

from timesketch.lib.analyzers.geoip import MaxMindDbGeoIPAnalyzer
from timesketch.lib.analyzers.geoip import MaxMindDbWebIPAnalyzer

from timesketch.lib import emojis
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

# TODO _create_mock_event will be renamed in another pull request. It's name
# should be also changed here.
from timesketch.lib.analyzers.base_sessionizer_test import _create_mock_event


class MockReader(object):
    """A mock implementation of a GeoLite2 database reader"""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def open(self, *unused_args):
        return self

    def __exit__(self, *args):
        pass

    def ip2geo(self, *unused_args):
        return "a", "b", "c", "d", "e"


class TestMaxMindDbGeoIPAnalyzer(BaseTest):
    """Tests for the functionality of the MaxMind Database based Geo IP
    Analyzer."""

    _TEST_ISO_CODE = "FLAG_US"
    _TEST_EMOJI = "&#x1F1FA&#x1F1F8"

    def testEmoji(self):
        """Test a flag emoji exists"""
        flag_emoji = emojis.get_emoji(self._TEST_ISO_CODE)
        self.assertEqual(flag_emoji, self._TEST_EMOJI)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def testValidIPv4(self):
        """Test valid IPv4 addresses result in new attributes"""
        analyzer = MaxMindDbGeoIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader

        analyzer.datastore.client = mock.Mock()

        IP_FIELDS = [
            "ip",
            "host_ip",
            "src_ip",
            "dst_ip",
            "source_ip",
            "dest_ip",
            "ip_address",
            "client_ip",
            "address",
            "saddr",
            "daddr",
            "requestMetadata_callerIp",
            "a_answer",
        ]

        _create_mock_event(
            analyzer.datastore,
            0,
            1,
            source_attrs={ip_field: "8.8.8.8" for ip_field in IP_FIELDS},
        )

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        for ip_field in IP_FIELDS:
            self.assertTrue("{0}_latitude".format(ip_field) in event["_source"])
            self.assertTrue("{0}_longitude".format(ip_field) in event["_source"])
            self.assertTrue("{0}_iso_code".format(ip_field) in event["_source"])
            self.assertTrue("{0}_city".format(ip_field) in event["_source"])
        self.assertEqual(message, "Found 1 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def testValidIPv6(self):
        """Test valid IPv6 addresses result in new attributes"""
        analyzer = MaxMindDbGeoIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader

        analyzer.datastore.client = mock.Mock()

        IP_FIELDS = [
            "ip",
            "host_ip",
            "src_ip",
            "dst_ip",
            "source_ip",
            "dest_ip",
            "ip_address",
            "client_ip",
            "address",
            "saddr",
            "daddr",
            "requestMetadata_callerIp",
            "a_answer",
        ]

        _create_mock_event(
            analyzer.datastore,
            0,
            1,
            source_attrs={ip_field: "2001:4860:4860::8888" for ip_field in IP_FIELDS},
        )

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        for ip_field in IP_FIELDS:
            self.assertTrue("{0}_latitude".format(ip_field) in event["_source"])
            self.assertTrue("{0}_longitude".format(ip_field) in event["_source"])
            self.assertTrue("{0}_iso_code".format(ip_field) in event["_source"])
            self.assertTrue("{0}_city".format(ip_field) in event["_source"])
        self.assertEqual(message, "Found 1 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def testPrivateIPv4(self):
        """Test private IPv4 address does not result in new attributes"""
        analyzer = MaxMindDbGeoIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader
        analyzer.datastore.client = mock.Mock()

        _create_mock_event(
            analyzer.datastore, 0, 1, source_attrs={"ip_address": "127.0.0.1"}
        )

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        self.assertTrue("ip_address_latitude" not in event["_source"])
        self.assertTrue("ip_address_longitude" not in event["_source"])
        self.assertTrue("ip_address_iso_code" not in event["_source"])
        self.assertTrue("ip_address_city" not in event["_source"])
        self.assertEqual(message, "Found 0 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def testInvalidIPv4(self):
        """Test invalid IP address"""
        analyzer = MaxMindDbGeoIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader
        analyzer.datastore.client = mock.Mock()

        _create_mock_event(analyzer.datastore, 0, 1, source_attrs={"ip_address": None})

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        self.assertTrue("ip_address_latitude" not in event["_source"])
        self.assertTrue("ip_address_longitude" not in event["_source"])
        self.assertTrue("ip_address_iso_code" not in event["_source"])
        self.assertTrue("ip_address_city" not in event["_source"])
        self.assertEqual(message, "Found 0 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def testNoEvents(self):
        """Test no events"""
        analyzer = MaxMindDbGeoIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader
        analyzer.datastore.client = mock.Mock()

        message = analyzer.run()

        self.assertEqual(message, "Found 0 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch("geoip2.database.Reader", MockReader)
    def testMultipleValidIPv4(self):
        """Test valid IPv4 addresses result in new attributes"""
        analyzer = MaxMindDbGeoIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader
        analyzer.datastore.client = mock.Mock()

        _create_mock_event(
            analyzer.datastore,
            0,
            1,
            source_attrs={"ip_address": ["8.8.8.8", "8.8.4.4"]},
        )

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        self.assertTrue("ip_address_latitude" in event["_source"])
        self.assertTrue("ip_address_longitude" in event["_source"])
        self.assertTrue("ip_address_iso_code" in event["_source"])
        self.assertTrue("ip_address_city" in event["_source"])
        self.assertEqual(message, "Found 2 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch("geoip2.database.Reader", MockReader)
    def testMixedValidIP(self):
        """Test valid IPv4 addresses result in new attributes"""
        analyzer = MaxMindDbGeoIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader
        analyzer.datastore.client = mock.Mock()

        _create_mock_event(
            analyzer.datastore,
            0,
            1,
            source_attrs={"ip_address": ["8.8.8.8", "2001:4860:4860::8844"]},
        )

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        self.assertTrue("ip_address_latitude" in event["_source"])
        self.assertTrue("ip_address_longitude" in event["_source"])
        self.assertTrue("ip_address_iso_code" in event["_source"])
        self.assertTrue("ip_address_city" in event["_source"])
        self.assertEqual(message, "Found 2 IP address(es).")


class TestMaxMindDbWebIPAnalyzer(BaseTest):
    """Tests for the functionality of the MaxMind web service based Geo IP
    Analyzer."""

    _TEST_ISO_CODE = "FLAG_US"
    _TEST_EMOJI = "&#x1F1FA&#x1F1F8"

    def testEmoji(self):
        """Test a flag emoji exists"""
        flag_emoji = emojis.get_emoji(self._TEST_ISO_CODE)
        self.assertEqual(flag_emoji, self._TEST_EMOJI)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def testValidIPv4(self):
        """Test valid IPv4 addresses result in new attributes"""
        analyzer = MaxMindDbWebIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader

        analyzer.datastore.client = mock.Mock()

        IP_FIELDS = [
            "ip",
            "host_ip",
            "src_ip",
            "dst_ip",
            "source_ip",
            "dest_ip",
            "ip_address",
            "client_ip",
            "address",
            "saddr",
            "daddr",
            "requestMetadata_callerIp",
            "a_answer",
        ]

        _create_mock_event(
            analyzer.datastore,
            0,
            1,
            source_attrs={ip_field: "8.8.8.8" for ip_field in IP_FIELDS},
        )

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        for ip_field in IP_FIELDS:
            self.assertTrue("{0}_latitude".format(ip_field) in event["_source"])
            self.assertTrue("{0}_longitude".format(ip_field) in event["_source"])
            self.assertTrue("{0}_iso_code".format(ip_field) in event["_source"])
            self.assertTrue("{0}_city".format(ip_field) in event["_source"])
        self.assertEqual(message, "Found 1 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def testValidIPv6(self):
        """Test valid IPv6 addresses result in new attributes"""
        analyzer = MaxMindDbWebIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader

        analyzer.datastore.client = mock.Mock()

        IP_FIELDS = [
            "ip",
            "host_ip",
            "src_ip",
            "dst_ip",
            "source_ip",
            "dest_ip",
            "ip_address",
            "client_ip",
            "address",
            "saddr",
            "daddr",
            "requestMetadata_callerIp",
            "a_answer",
        ]

        _create_mock_event(
            analyzer.datastore,
            0,
            1,
            source_attrs={ip_field: "2001:4860:4860::8888" for ip_field in IP_FIELDS},
        )

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        for ip_field in IP_FIELDS:
            self.assertTrue("{0}_latitude".format(ip_field) in event["_source"])
            self.assertTrue("{0}_longitude".format(ip_field) in event["_source"])
            self.assertTrue("{0}_iso_code".format(ip_field) in event["_source"])
            self.assertTrue("{0}_city".format(ip_field) in event["_source"])
        self.assertEqual(message, "Found 1 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def testPrivateIPv4(self):
        """Test private IPv4 address does not result in new attributes"""
        analyzer = MaxMindDbWebIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader
        analyzer.datastore.client = mock.Mock()

        _create_mock_event(
            analyzer.datastore, 0, 1, source_attrs={"ip_address": "127.0.0.1"}
        )

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        self.assertTrue("ip_address_latitude" not in event["_source"])
        self.assertTrue("ip_address_longitude" not in event["_source"])
        self.assertTrue("ip_address_iso_code" not in event["_source"])
        self.assertTrue("ip_address_city" not in event["_source"])
        self.assertEqual(message, "Found 0 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def testInvalidIPv4(self):
        """Test invalid IP address"""
        analyzer = MaxMindDbWebIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader
        analyzer.datastore.client = mock.Mock()

        _create_mock_event(analyzer.datastore, 0, 1, source_attrs={"ip_address": None})

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        self.assertTrue("ip_address_latitude" not in event["_source"])
        self.assertTrue("ip_address_longitude" not in event["_source"])
        self.assertTrue("ip_address_iso_code" not in event["_source"])
        self.assertTrue("ip_address_city" not in event["_source"])
        self.assertEqual(message, "Found 0 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def testNoEvents(self):
        """Test no events"""
        analyzer = MaxMindDbWebIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader
        analyzer.datastore.client = mock.Mock()

        message = analyzer.run()

        self.assertEqual(message, "Found 0 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch("geoip2.database.Reader", MockReader)
    def testMultipleValidIPv4(self):
        """Test valid IPv4 addresses result in new attributes"""
        analyzer = MaxMindDbWebIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader
        analyzer.datastore.client = mock.Mock()

        _create_mock_event(
            analyzer.datastore,
            0,
            1,
            source_attrs={"ip_address": ["8.8.8.8", "8.8.4.4"]},
        )

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        self.assertTrue("ip_address_latitude" in event["_source"])
        self.assertTrue("ip_address_longitude" in event["_source"])
        self.assertTrue("ip_address_iso_code" in event["_source"])
        self.assertTrue("ip_address_city" in event["_source"])
        self.assertEqual(message, "Found 2 IP address(es).")

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch("geoip2.database.Reader", MockReader)
    def testMixedValidIP(self):
        """Test valid IPv4 addresses result in new attributes"""
        analyzer = MaxMindDbWebIPAnalyzer("test", 1)
        analyzer.GEOIP_CLIENT = MockReader
        analyzer.datastore.client = mock.Mock()

        _create_mock_event(
            analyzer.datastore,
            0,
            1,
            source_attrs={"ip_address": ["8.8.8.8", "2001:4860:4860::8844"]},
        )

        message = analyzer.run()
        event = analyzer.datastore.event_store["0"]

        self.assertTrue("ip_address_latitude" in event["_source"])
        self.assertTrue("ip_address_longitude" in event["_source"])
        self.assertTrue("ip_address_iso_code" in event["_source"])
        self.assertTrue("ip_address_city" in event["_source"])
        self.assertEqual(message, "Found 2 IP address(es).")
