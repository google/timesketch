# Copyright 2022 Google Inc. All rights reserved.
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
"""Tests for complex attributes."""

from timesketch.lib import event_attributes
from timesketch.lib.testlib import BaseTest


class TestComplexAttributes(BaseTest):
    """Tests for the emojis support library."""

    # We only test Hostname here; it's the same structure for other attributes.
    def test_simple_attribute_serialize(self):
      attr = event_attributes.Hostname(value='google.com')
      serialized = attr.serialize()
      self.assertDictEqual(
        serialized,
        { '__hostname': {'type': 'hostname', 'value': 'google.com'}})

    def test_simple_attribute_serialize_with_source(self):
      attr = event_attributes.Hostname(value='google.com')
      serialized = attr.serialize(source='tests')
      self.assertDictEqual(
        serialized,
        {
          '__hostname': {
            'source': 'tests',
            'type': 'hostname',
            'value': 'google.com'
          }
        })

    def test_simple_attribute_load(self):
      attr = event_attributes.Hostname.load({
        '__hostname' : {'type': 'hostname', 'value': 'youtube.com'}
      })
      self.assertIsInstance(attr, event_attributes.Hostname)
      self.assertEquals(attr.value, 'youtube.com')

    def test_simple_attribtue_load_fail(self):
      with self.assertRaises(ValueError) as error:
        attr = event_attributes.Hostname.load({
          '__not_a_hostname' : {'type': 'hostname', 'value': 'youtube.com'}
        })
      self.assertEquals(
        str(error.exception),
        ("The JSON object passed is not representing a hostname: "
        "{'__not_a_hostname': {'type': 'hostname', 'value': 'youtube.com'}}"))

    def test_geoip_serialize(self):
        attr = event_attributes.GeoIP(0, 0)
        self.assertIsNotNone(attr)
        serialized = attr.serialize()
        self.assertEquals(
            serialized,
            {
              '__geoip': {
                'type': 'geoip',
                'ip_address_latitude': 0.0,
                'ip_address_longitude': 0.0
              }
            })

    def test_geoip_load(self):
        attr = event_attributes.GeoIP.load(
            {
              '__geoip': {
                'type': 'geoip',
                'ip_address_latitude': 123.0,
                'ip_address_longitude': 456.0
              }
            }
        )
        self.assertEquals(attr.ip_address_latitude, 123.0)
        self.assertEquals(attr.ip_address_longitude, 456.0)

    def test_browser_search_serialize(self):
      attr = event_attributes.BrowserSearch()
      attr.search_string = 'random_search'
      attr.search_engine = event_attributes.Hostname(value='google.com')
      serialized = attr.serialize()

      self.assertDictEqual(
          serialized,
          {
            '__browser_search': {
              'type': 'browser_search',
              'search_string': 'random_search',
              'search_engine': {
                '__hostname': {
                  'type': 'hostname',
                  'value': 'google.com'
                }
              }
            }
          }
      )

    def test_browser_search_load(self):
      attr = event_attributes.BrowserSearch.load(
        {
          '__browser_search': {
            'type': 'browser_search',
            'search_string': 'random_search',
            'search_engine': {
              '__hostname': {
                'type': 'hostname',
                'value': 'google.com'
                }
            }
          }
        }
      )

      self.assertEqual(attr.search_string, 'random_search')
      self.assertIsInstance(attr.search_engine, event_attributes.Hostname)
      self.assertEqual(attr.search_engine.value, 'google.com')
