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
"""Tests for DomainPlugin."""

from unittest import mock

from timesketch.lib.analyzers import domain
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore


class TestDomainPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    # Mock the OpenSearch datastore.
    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_domain_analyzer_class(self):
        """Test core functionality of the analyzer class."""
        index_name = "test"
        sketch_id = 1
        analyzer = domain.DomainSketchPlugin(index_name, sketch_id)
        self.assertEqual(analyzer.index_name, index_name)
        self.assertEqual(analyzer.sketch.id, sketch_id)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_domain_analyzer_no_events(self):
        """Test that the analyzer handles an empty event stream gracefully."""
        analyzer = domain.DomainSketchPlugin("test", 1)
        analyzer.datastore.client = mock.Mock()

        # No events in the store: run() should return early with a NOTE summary.
        result = analyzer.run()
        self.assertIn("No domains to analyze.", result)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_domain_extracted_from_url(self):
        """Test that domains are extracted from the url field when domain is absent."""
        analyzer = domain.DomainSketchPlugin("test", 1)
        analyzer.datastore.client = mock.Mock()

        # Inject a single event that carries a url but no domain field.
        event_id = "url_event_0"
        analyzer.datastore.event_store[event_id] = {
            "_id": event_id,
            "_index": "test",
            "_source": {
                "__ts_timeline_id": 1,
                "timestamp": 1410593222543942,
                "url": "https://www.example.com/some/path?q=1",
            },
        }

        result = analyzer.run()
        # example.com should have been recognised and counted as a domain.
        self.assertIn("1 domains discovered", result)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_rare_domain_tagged(self):
        """Test that domains appearing infrequently are counted in the result."""
        analyzer = domain.DomainSketchPlugin("test", 1)
        analyzer.datastore.client = mock.Mock()

        # Populate the datastore: one common domain (many hits) and one
        # rare domain (a single hit so it falls below the 20th percentile).
        for i in range(10):
            eid = "common_{:d}".format(i)
            analyzer.datastore.event_store[eid] = {
                "_id": eid,
                "_index": "test",
                "_source": {
                    "__ts_timeline_id": 1,
                    "timestamp": 1410593222543942 + i,
                    "domain": "common.example.com",
                },
            }

        rare_eid = "rare_0"
        analyzer.datastore.event_store[rare_eid] = {
            "_id": rare_eid,
            "_index": "test",
            "_source": {
                "__ts_timeline_id": 1,
                "timestamp": 1410593222543942,
                "domain": "rare.example.net",
            },
        }

        result = analyzer.run()
        # Both the common and the rare domain should be present in the summary.
        self.assertIn("2 domains discovered", result)

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_cdn_domain_tagged(self):
        """Test that events whose domain is a known CDN are reported."""
        analyzer = domain.DomainSketchPlugin("test", 1)
        analyzer.datastore.client = mock.Mock()

        cdn_eid = "cdn_0"
        analyzer.datastore.event_store[cdn_eid] = {
            "_id": cdn_eid,
            "_index": "test",
            "_source": {
                "__ts_timeline_id": 1,
                "timestamp": 1410593222543942,
                # .cloudfront.net is listed in KNOWN_CDN_DOMAINS as Amazon CloudFront.
                "domain": "assets.example.cloudfront.net",
            },
        }

        result = analyzer.run()
        self.assertIn("1 known CDN networks found.", result)
