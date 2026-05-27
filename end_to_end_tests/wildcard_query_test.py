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
        # 1. Standard raw exact search target
        results = self.sketch.explore_wildcard(
            query_string="message:*powershell.exe*"
        )
        self.assertions.assertIsNotNone(results)
        self.assertions.assertIn("objects", results)
        self.assertions.assertIn("meta", results)



        # 3. Literal logic query checks (AND/OR are treated as raw characters)
        literal_results = self.sketch.explore_wildcard(
            query_string="message:*powershell.exe AND Bypass*"
        )
        self.assertions.assertEqual(len(literal_results.get("objects", [])), 0)

    def test_cli_search_wildcard(self):
        """Test CLI 'search-wildcard' command with comparison modes."""
        cli_ctx = E2EContext(
            api_client=self.api,
            sketch_instance=self.sketch,
            output_format="json",
        )

        result = self.runner.invoke(
            search_wildcard,
            ["-q", "message:*powershell.exe*", "--compare"],
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
