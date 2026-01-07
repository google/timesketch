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
"""End to end tests for Timesketch CLI client commands."""

import os
import uuid
from click.testing import CliRunner

from timesketch_cli_client.commands.sketch import sketch_group

from . import interface
from . import manager


class E2ECliContextObject:
    """A context object for running CLI client commands in E2E tests."""

    def __init__(self, api_client, sketch_instance, output_format="text"):
        self.api = api_client
        self.sketch = sketch_instance  # The active sketch for the commands
        self.output_format = output_format


class CliClientE2ETest(interface.BaseEndToEndTest):
    """End to end tests for the Timesketch CLI client."""

    NAME = (
        "cli_client_e2e_test"  # Sketch created by BaseEndToEndTest will have this name
    )

    def __init__(self):
        """Initialize the test case."""
        super().__init__()  # This initializes self.api and self.sketch
        self.runner = CliRunner()

    def test_cli_sketch_list(self):
        """Tests 'timesketch sketch list' using the CLI client's command group."""
        sketch_to_find = self.sketch

        # Prepare the context object for the CLI command.
        # 'sketch list' uses ctx.obj.api and ctx.obj.output_format.
        cli_ctx_obj = E2ECliContextObject(
            api_client=self.api,
            sketch_instance=sketch_to_find,
            output_format="text",
        )

        result = self.runner.invoke(sketch_group, ["list"], obj=cli_ctx_obj)

        # Assertions
        self.assertions.assertEqual(
            result.exit_code,
            0,
            f"CLI command 'sketch list' failed.\nOutput:\n{result.output}\n"
            f"Exception:\n{result.exception}",
        )
        self.assertions.assertIn(
            sketch_to_find.name,
            result.output,
            f"Sketch name '{sketch_to_find.name}' not found in 'sketch list' output.",
        )
        self.assertions.assertIn(
            str(sketch_to_find.id),
            result.output,
            f"Sketch ID '{sketch_to_find.id}' not found in 'sketch list' output.",
        )

    def test_cli_sketch_describe(self):
        """Tests 'timesketch sketch describe' using the CLI client's command group."""
        # self.sketch is the active sketch for this test.
        active_sketch = self.sketch

        # Prepare the context object.
        # 'sketch describe' uses ctx.obj.sketch and ctx.obj.output_format.
        cli_ctx_obj = E2ECliContextObject(
            api_client=self.api,
            sketch_instance=active_sketch,
            output_format="text",
        )

        # Invoke the 'describe' command.
        result = self.runner.invoke(sketch_group, ["describe"], obj=cli_ctx_obj)

        # Assertions
        self.assertions.assertEqual(
            result.exit_code,
            0,
            f"CLI command 'sketch describe' failed.\n"
            f"Output:\n{result.output}\nException:\n{result.exception}",
        )
        self.assertions.assertIn(
            f"Name: {active_sketch.name}",
            result.output,
            "Sketch name not found or incorrect in 'sketch describe' output.",
        )

        self.assertions.assertIn(
            f"Description: {active_sketch.description}",
            result.output,
            "Sketch description not found or incorrect in 'sketch describe' output.",
        )

    def test_cli_sketch_export(self):
        """Tests 'timesketch sketch export'."""
        sketch_name = f"cli_client_e2e_test_export_{uuid.uuid4().hex}"
        active_sketch = self.api.create_sketch(name=sketch_name)
        self.import_timeline("evtx_part.csv", sketch=active_sketch)  # ensure some data

        cli_ctx_obj = E2ECliContextObject(
            api_client=self.api,
            sketch_instance=active_sketch,
            output_format="text",
        )

        # Test default export
        with self.runner.isolated_filesystem():
            filename = "export.zip"
            result = self.runner.invoke(
                sketch_group, ["export", "--filename", filename], obj=cli_ctx_obj
            )
            self.assertions.assertEqual(result.exit_code, 0, f"Output: {result.output}")
            self.assertions.assertTrue(os.path.exists(filename))

            # Test streaming export
            filename_stream = "export_stream.zip"
            result_stream = self.runner.invoke(
                sketch_group,
                ["export", "--filename", filename_stream, "--stream"],
                obj=cli_ctx_obj,
            )
            self.assertions.assertEqual(
                result_stream.exit_code, 0, f"Output: {result_stream.output}"
            )
            self.assertions.assertTrue(os.path.exists(filename_stream))

            # Test use_sketch_export
            filename_full = "export_full.zip"
            result_full = self.runner.invoke(
                sketch_group,
                ["export", "--filename", filename_full, "--use_sketch_export"],
                obj=cli_ctx_obj,
            )
            self.assertions.assertEqual(
                result_full.exit_code, 0, f"Output: {result_full.output}"
            )
            self.assertions.assertTrue(os.path.exists(filename_full))


# Register the new test class with the test manager
manager.EndToEndTestManager.register_test(CliClientE2ETest)
