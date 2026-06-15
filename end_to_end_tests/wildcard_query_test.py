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
# pylint: disable=import-error
# pylint: disable=no-name-in-module
# pylint: disable=wrong-import-position
"""End to end tests of exact-match wildcard search and comparison metrics."""

from click.testing import CliRunner

from timesketch_cli_client.commands.search import search_wildcard

from . import interface
from . import manager


class E2EContext:
    """Lightweight context object for Click CLI commands."""

    def __init__(self, api_client, sketch_instance, output_format="json"):
        self.api = api_client
        self.sketch = sketch_instance
        self.output_format = output_format


class WildcardQueryTest(interface.BaseEndToEndTest):
    """End to end tests for raw wildcard search functionality."""

    NAME = "wildcard_query_test"

    def __init__(self):
        """Initialize the test case."""
        super().__init__()
        self.runner = CliRunner()

    def setup(self):
        """Import a dynamic test timeline."""
        self.import_timeline("evtx_direct.csv")

    def test_api_wildcard_search(self):
        """Test exact-match wildcard API client searches."""
        # 1. Standard raw exact search target (should return exactly 3 events)
        results = self.sketch.explore_wildcard(query_string="message:*Eventlog*")
        self.assertions.assertIsNotNone(results)
        self.assertions.assertIn("objects", results)

        field_events = results.get("objects", [])
        self.assertions.assertEqual(len(field_events), 3)

        # 3. Literal logic query checks (AND/OR are treated as raw characters)
        literal_results = self.sketch.explore_wildcard(
            query_string="message:*Eventlog AND Bypass*"
        )
        self.assertions.assertEqual(len(literal_results.get("objects", [])), 0)

        # 4. Global wildcard search (verifies multi-field should compilation)
        global_results = self.sketch.explore_wildcard(query_string="*Eventlog*")
        self.assertions.assertIsNotNone(global_results)
        self.assertions.assertIn("objects", global_results)

        global_events = global_results.get("objects", [])
        self.assertions.assertEqual(len(global_events), 3)

        # Verify that the exact same events are returned
        field_event_ids = {event["_id"] for event in field_events}
        global_event_ids = {event["_id"] for event in global_events}
        self.assertions.assertEqual(global_event_ids, field_event_ids)

        # 5. Global match-all wildcard search (should return all 13 events)
        all_results = self.sketch.explore_wildcard(query_string="*", limit=20)
        self.assertions.assertIsNotNone(all_results)
        self.assertions.assertIn("objects", all_results)

        all_events = all_results.get("objects", [])
        self.assertions.assertEqual(len(all_events), 13)

        # 6. Global search matching a field other than 'message' (verifies
        # multi-field search).
        # - 'winevtx' is the value of the 'parser' field, but does not
        # appear in the 'message' field.
        parser_results = self.sketch.explore_wildcard(
            query_string="parser:*winevtx*", limit=20
        )
        self.assertions.assertEqual(len(parser_results.get("objects", [])), 13)

        message_results = self.sketch.explore_wildcard(query_string="message:*winevtx*")
        self.assertions.assertEqual(len(message_results.get("objects", [])), 0)

        global_parser_results = self.sketch.explore_wildcard(
            query_string="*winevtx*", limit=20
        )
        self.assertions.assertEqual(len(global_parser_results.get("objects", [])), 13)

        # Verify that the global search matches the 'parser' field results exactly
        parser_event_ids = {event["_id"] for event in parser_results.get("objects", [])}
        global_parser_event_ids = {
            event["_id"] for event in global_parser_results.get("objects", [])
        }
        self.assertions.assertEqual(global_parser_event_ids, parser_event_ids)

    def test_cli_search_wildcard(self):
        """Test CLI 'search-wildcard' command with comparison modes."""
        cli_ctx = E2EContext(
            api_client=self.api,
            sketch_instance=self.sketch,
            output_format="json",
        )

        result = self.runner.invoke(
            search_wildcard,
            ["-q", "message:*Eventlog*", "--compare"],
            obj=cli_ctx,
        )

        self.assertions.assertEqual(
            result.exit_code,
            0,
            f"CLI wildcard command failed. Output:\n{result.output}",
        )
        self.assertions.assertIn("--- Comparison Diagnostics ---", result.output)
        self.assertions.assertIn("wildcard_search", result.output)


manager.EndToEndTestManager.register_test(WildcardQueryTest)
