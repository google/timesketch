# Copyright 2019 Google Inc. All rights reserved.
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
"""Tests for analysis utils."""

from __future__ import unicode_literals

import pandas as pd

import six

from timesketch.lib.testlib import BaseTest
from timesketch.lib.analyzers import utils


class TestAnalyzerUtils(BaseTest):
    """Tests the functionality of the utilities."""

    def __init__(self, *args, **kwargs):
        super(TestAnalyzerUtils, self).__init__(*args, **kwargs)

    def test_get_domain_from_url(self):
        """Test get_domain_from_url function."""
        url = 'http://www.example.com/?foo=bar'
        domain = utils.get_domain_from_url(url)
        self.assertEquals(domain, 'www.example.com')

    def test_get_tld_from_domain(self):
        """Test get_tld_from_domain function."""
        domain = 'this.is.a.subdomain.example.com'
        tld = utils.get_tld_from_domain(domain)
        self.assertEquals(tld, 'example.com')

        domain = 'a'
        tld = utils.get_tld_from_domain(domain)
        self.assertEquals(tld, 'a')

        domain = 'example.com'
        tld = utils.get_tld_from_domain(domain)
        self.assertEquals(tld, 'example.com')

    def test_strip_www_from_domain(self):
        """Test strip_www_from_domain function."""
        domain = 'www.mbl.is'
        stripped = utils.strip_www_from_domain(domain)
        self.assertEquals(stripped, 'mbl.is')

        domain = 'mbl.is'
        stripped = utils.strip_www_from_domain(domain)
        self.assertEquals(stripped, domain)

    def test_get_cdn_provider(self):
        """Test get_cdn_provider function."""
        domain = 'foobar.gstatic.com'
        provider = utils.get_cdn_provider(domain)
        self.assertIsInstance(provider, six.text_type)
        self.assertEquals(provider, 'Google')

        domain = 'www.mbl.is'
        provider = utils.get_cdn_provider(domain)
        self.assertIsInstance(provider, six.text_type)
        self.assertEquals(provider, '')

    def test_get_events_from_data_frame(self):
        """Test getting all events from data frame."""
        lines = [
            {'_id': '123', '_type': 'manual', '_index': 'asdfasdf',
             'tool': 'isskeid'},
            {'_id': '124', '_type': 'manual', '_index': 'asdfasdf',
             'tool': 'tong'},
            {'_id': '125', '_type': 'manual', '_index': 'asdfasdf',
             'tool': 'klemma'},
        ]
        frame = pd.DataFrame(lines)

        events = list(utils.get_events_from_data_frame(frame, None))
        self.assertEquals(len(events), 3)
        ids = [x.event_id for x in events]
        self.assertEquals(set(ids), set(['123', '124', '125']))
