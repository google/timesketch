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

import six

import pandas as pd

from timesketch.lib.testlib import BaseTest
from timesketch.lib.analyzers import utils


class TestAnalyzerUtils(BaseTest):
    """Tests the functionality of the utilities."""

    def test_get_domain_from_url(self):
        """Test get_domain_from_url function."""
        url = "http://www.example.com/?foo=bar"
        domain = utils.get_domain_from_url(url)
        self.assertEqual(domain, "www.example.com")

    def test_get_tld_from_domain(self):
        """Test get_tld_from_domain function."""
        domain = "this.is.a.subdomain.example.com"
        tld = utils.get_tld_from_domain(domain)
        self.assertEqual(tld, "example.com")

        domain = "a"
        tld = utils.get_tld_from_domain(domain)
        self.assertEqual(tld, "a")

        domain = "example.com"
        tld = utils.get_tld_from_domain(domain)
        self.assertEqual(tld, "example.com")

    def test_strip_www_from_domain(self):
        """Test strip_www_from_domain function."""
        domain = "www.mbl.is"
        stripped = utils.strip_www_from_domain(domain)
        self.assertEqual(stripped, "mbl.is")

        domain = "mbl.is"
        stripped = utils.strip_www_from_domain(domain)
        self.assertEqual(stripped, domain)

    def test_get_cdn_provider(self):
        """Test get_cdn_provider function."""
        domain = "foobar.gstatic.com"
        provider = utils.get_cdn_provider(domain)
        self.assertIsInstance(provider, six.text_type)
        self.assertEqual(provider, "Google")

        domain = "www.mbl.is"
        provider = utils.get_cdn_provider(domain)
        self.assertIsInstance(provider, six.text_type)
        self.assertEqual(provider, "")

    def test_get_events_from_data_frame(self):
        """Test getting all events from data frame."""
        lines = [
            {"_id": "123", "_type": "manual", "_index": "asdfasdf", "tool": "isskeid"},
            {"_id": "124", "_type": "manual", "_index": "asdfasdf", "tool": "tong"},
            {"_id": "125", "_type": "manual", "_index": "asdfasdf", "tool": "klemma"},
        ]
        frame = pd.DataFrame(lines)

        events = list(utils.get_events_from_data_frame(frame, None))
        self.assertEqual(len(events), 3)
        ids = [x.event_id for x in events]
        self.assertEqual(set(ids), set(["123", "124", "125"]))

    def test_regular_expression_compile(self):
        """Test compiling regular expressions."""
        test_re_string = r"Foo[0-9]bar"
        string_test = "foo2bar"
        string_test_2 = "Foo9bar"

        expression = utils.compile_regular_expression(expression_string=test_re_string)
        self.assertFalse(expression.match(string_test))
        self.assertTrue(expression.match(string_test_2))

        expression = utils.compile_regular_expression(
            expression_string=test_re_string, expression_flags=["IGNORECASE"]
        )
        self.assertTrue(expression.match(string_test))

        test_re_string = r"Foo[0-9]{param}"
        re_parameters = {
            "param": "bar",
        }
        expression = utils.compile_regular_expression(
            expression_string=test_re_string,
            expression_flags=["IGNORECASE"],
            expression_parameters=re_parameters,
        )
        self.assertTrue(expression.match(string_test))
