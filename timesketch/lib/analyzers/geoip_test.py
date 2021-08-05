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

import geoip2.database
from timesketch.lib.analyzers.geoip import GeoIPSketchPlugin

from timesketch.lib import emojis
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

# TODO _create_mock_event will be renamed in another pull request. It's name
# should be also changed here.
from timesketch.lib.analyzers.base_sessionizer_test \
    import _create_mock_event


class MockCity(object):
    """A mock of a City that returns dummy data."""
    name = 'City'


class MockCountry(object):
    """A mock of a Country that returns dummy data."""
    iso_code = 'XX'
    name = 'Country'


class MockLocation(object):
    """A mock of a Location that returns dummy data."""
    latitude = 1.0
    longitude = 2.0


class MockResponse(object):
    """A mock response to a database lookup."""
    location = MockLocation()
    country = MockCountry()
    city = MockCity()


class MockReader(object):
    """A mock implementation of a GeoLite2 database reader"""
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        return self

    def open(self, *args):
        return self

    def __exit__(self, *args):
        pass

    def city(self, *args):
        return MockResponse()


class TestGeoIPAnalyzer(BaseTest):
    """Tests for the functionality of the Geo IP Analyzer."""

    _TEST_ISO_CODE = "US"
    _TEST_EMOJI = "&#x1F1FA&#x1F1F8"


    def testEmoji(self):
        """Test a flag emoji exists"""
        flag_emoji = emojis.get_emoji(self._TEST_ISO_CODE)
        self.assertEqual(flag_emoji, self._TEST_EMOJI)

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    @mock.patch('geoip2.database.Reader')
    def testGeoIPConfigNotFound(self, reader):
        """Test when the GeoIP Database configuration in timesketch.conf does 
           not exist"""
        reader.side_effect = FileNotFoundError()

        analyzer = GeoIPSketchPlugin('test', 1)
        message = analyzer.run()
        self.assertEqual(message, 
            'GeoIP analyzer error - database configuration not set.')

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    @mock.patch('geoip2.database.Reader')
    def testGeoIPDatabaseNotFound(self, reader):
        """Test when the GeoIP Database does not exist"""
        reader.side_effect = FileNotFoundError()

        analyzer = GeoIPSketchPlugin('test', 1)
        analyzer._geolite_database = 'mock'
        message = analyzer.run()
        self.assertEqual(message, 'GeoIP analyzer error - database not found.')

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    @mock.patch('geoip2.database.Reader')
    def testGeoIPDatabaseCorrupt(self, reader):
        """Test when the GeoIP Database is corrupt"""
        reader.side_effect = geoip2.database.maxminddb.InvalidDatabaseError()

        analyzer = GeoIPSketchPlugin('test', 1)
        analyzer._geolite_database = 'mock'
        message = analyzer.run()
        self.assertEqual(message, 'GeoIP analyzer error - corrupt database.')

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    @mock.patch('geoip2.database.Reader', MockReader)
    def testValidIPv4(self):
        """Test valid IPv4 addresses result in new attributes"""
        analyzer = GeoIPSketchPlugin('test', 1)
        analyzer._geolite_database = 'mock'
        analyzer.datastore.client = mock.Mock()

        IP_FIELDS = ['ip', 'host_ip', 'src_ip', 'dst_ip', 'source_ip', 
        'dest_ip', 'ip_address', 'client_ip', 'address', 'saddr', 'daddr', 
        'requestMetadata_callerIp', 'a_answer']

        _create_mock_event(analyzer.datastore, 0, 1,
            source_attrs={
                ip_field: '8.8.8.8' for ip_field in IP_FIELDS
            })

        message = analyzer.run()
        event = analyzer.datastore.event_store['0']
        print(event)
        for ip_field in IP_FIELDS:
            self.assertTrue('{0}_latitude'.format(ip_field) 
                in event['_source'])
            self.assertTrue('{0}_longitude'.format(ip_field) 
                in event['_source'])
            self.assertTrue('{0}_iso_code'.format(ip_field) 
                in event['_source'])
            self.assertTrue('{0}_city'.format(ip_field) 
                in event['_source'])
        self.assertEqual(message, 'GeoIP analyzer completed.')

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def testPrivateIPv4(self):
        """Test private IPv4 address does not result in new attributes"""
        geoip2.database.Reader = mock.mock_open()

        analyzer = GeoIPSketchPlugin('test', 1)
        analyzer._geolite_database = 'mock'
        analyzer.datastore.client = mock.Mock()
        _create_mock_event(analyzer.datastore, 0, 1,
            source_attrs={
                'ip_address': '127.0.0.1'
            })

        message = analyzer.run()
        event = analyzer.datastore.event_store['0']

        self.assertTrue('ip_address_latitude' not in event['_source'])
        self.assertTrue('ip_address_longitude' not in event['_source'])
        self.assertTrue('ip_address_iso_code' not in event['_source'])
        self.assertTrue('ip_address_city' not in event['_source'])
        self.assertEqual(message, 'GeoIP analyzer completed.')

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def testInvalidIPv4(self):
        """Test invalid IP address"""
        geoip2.database.Reader = mock.mock_open()

        analyzer = GeoIPSketchPlugin('test', 1)
        analyzer._geolite_database = 'mock'
        analyzer.datastore.client = mock.Mock()
        _create_mock_event(analyzer.datastore, 0, 1,
            source_attrs={
                'ip_address': None
            })

        message = analyzer.run()
        event = analyzer.datastore.event_store['0']

        self.assertTrue('ip_address_latitude' not in event['_source'])
        self.assertTrue('ip_address_longitude' not in event['_source'])
        self.assertTrue('ip_address_iso_code' not in event['_source'])
        self.assertTrue('ip_address_city' not in event['_source'])
        self.assertEqual(message, 'GeoIP analyzer completed.')

    @mock.patch('timesketch.lib.analyzers.interface.ElasticsearchDataStore',
                MockDataStore)
    def testNoEvents(self):
        """Test no events"""
        geoip2.database.Reader = mock.mock_open()

        analyzer = GeoIPSketchPlugin('test', 1)
        analyzer._geolite_database = 'mock'
        analyzer.datastore.client = mock.Mock()

        message = analyzer.run()

        self.assertEqual(message, 'GeoIP analyzer completed.')
