# Copyright 2026 Google Inc. All rights reserved.
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
"""Tests for telemetry."""

# pylint: disable=protected-access,unused-argument

from unittest import mock

try:
    from opentelemetry import trace as otel_trace
except ImportError:
    otel_trace = None
from timesketch.lib import telemetry
from timesketch.lib.testlib import BaseTest


class TelemetryTest(BaseTest):
    """Tests for telemetry functions."""

    def test_extract_total_hits(self):
        """Test _extract_total_hits helper function."""
        # Test int value
        self.assertEqual(telemetry._extract_total_hits(123), 123)

        # Test invalid types
        self.assertEqual(telemetry._extract_total_hits("string"), 0)
        self.assertEqual(telemetry._extract_total_hits(None), 0)

        # Test ES6 / Mock style dict (total is int)
        res_es6 = {"hits": {"total": 456}}
        self.assertEqual(telemetry._extract_total_hits(res_es6), 456)

        # Test ES7 / OS style dict (total is dict)
        res_es7 = {"hits": {"total": {"value": 789, "relation": "eq"}}}
        self.assertEqual(telemetry._extract_total_hits(res_es7), 789)

        # Test missing keys
        self.assertEqual(telemetry._extract_total_hits({}), 0)
        self.assertEqual(telemetry._extract_total_hits({"hits": {}}), 0)
        self.assertEqual(telemetry._extract_total_hits({"hits": None}), 0)
        self.assertEqual(telemetry._extract_total_hits({"hits": {"total": None}}), 0)

    @mock.patch("timesketch.lib.telemetry.is_enabled", return_value=True)
    @mock.patch("timesketch.lib.telemetry.trace")
    def test_instrument_search(self, mock_trace, mock_is_enabled):
        """Test instrument_search decorator adds expected attributes to span."""
        # Setup mocks with spec verification to ensure OTel compatibility
        mock_tracer = mock.MagicMock(spec=otel_trace.Tracer if otel_trace else None)
        mock_span = mock.MagicMock(spec=otel_trace.Span if otel_trace else None)
        mock_trace.get_tracer.return_value = mock_tracer
        mock_tracer.start_as_current_span.return_value.__enter__.return_value = (
            mock_span
        )

        # Define a mock search function that mimics OpenSearchDataStore.search
        @telemetry.instrument_search
        def dummy_search(
            sketch_id,
            indices,
            query_string="",
            query_filter=None,
            count=False,
            query_dsl=None,
            enable_scroll=False,
            use_wildcard_fields=False,
        ):
            if count:
                return 42
            return {"took": 15, "hits": {"hits": [{}], "total": {"value": 100}}}

        # 1. Test standard search call
        res = dummy_search(
            sketch_id=7,
            indices=["index1", "index2"],
            query_filter={"size": 10, "from": 20},
            use_wildcard_fields=True,
        )

        self.assertEqual(res["took"], 15)

        # Check standard arguments are logged
        mock_span.set_attribute.assert_any_call("timesketch.sketch_id", 7)
        mock_span.set_attribute.assert_any_call(
            "timesketch.search.use_wildcard_fields", True
        )
        mock_span.set_attribute.assert_any_call("timesketch.search.is_count", False)
        mock_span.set_attribute.assert_any_call("timesketch.search.is_dsl", False)
        mock_span.set_attribute.assert_any_call("timesketch.search.indices_count", 2)
        mock_span.set_attribute.assert_any_call("timesketch.search.page_size", 10)
        mock_span.set_attribute.assert_any_call("timesketch.search.page_offset", 20)

        # Check results are logged
        mock_span.set_attribute.assert_any_call("db.opensearch.took_ms", 15)
        mock_span.set_attribute.assert_any_call("timesketch.search.returned_hits", 1)
        mock_span.set_attribute.assert_any_call("timesketch.search.total_hits", 100)

        # 2. Test count search call with positional arguments
        mock_span.reset_mock()
        res_count = dummy_search(7, ["index1"], "query", {}, True, None, True, False)
        self.assertEqual(res_count, 42)

        mock_span.set_attribute.assert_any_call("timesketch.sketch_id", 7)
        mock_span.set_attribute.assert_any_call(
            "timesketch.search.use_wildcard_fields", False
        )
        mock_span.set_attribute.assert_any_call("timesketch.search.is_count", True)
        mock_span.set_attribute.assert_any_call("timesketch.search.enable_scroll", True)
        mock_span.set_attribute.assert_any_call("timesketch.search.total_hits", 42)

        # 3. Test string indices and None pagination parameters
        mock_span.reset_mock()
        res_none_page = dummy_search(
            sketch_id=7,
            indices="string_index",
            query_filter={"size": None, "from": None},
        )
        self.assertIsNotNone(res_none_page)
        mock_span.set_attribute.assert_any_call("timesketch.search.indices_count", 1)
        # Check that page_size and page_offset were NOT set (no call made for them)
        for call_arg in mock_span.set_attribute.call_args_list:
            attr_name = call_arg[0][0]
            self.assertNotIn(
                attr_name,
                ["timesketch.search.page_size", "timesketch.search.page_offset"],
            )

        # 4. Test dict result with hits set to None
        @telemetry.instrument_search
        def dummy_search_null_hits(sketch_id, indices):
            return {"took": 5, "hits": None}

        mock_span.reset_mock()
        res_null_hits = dummy_search_null_hits(7, ["index"])
        self.assertEqual(res_null_hits["hits"], None)
        # Should record took_ms, but returned_hits should not be set
        # (or should be skipped without exception)
        mock_span.set_attribute.assert_any_call("db.opensearch.took_ms", 5)
        # Verify returned_hits was not set
        for call_arg in mock_span.set_attribute.call_args_list:
            attr_name = call_arg[0][0]
            self.assertNotEqual(attr_name, "timesketch.search.returned_hits")
