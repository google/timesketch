# Copyright 2023 Google Inc. All rights reserved.
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
"""Tests for events command."""

import unittest
import mock

from click.testing import CliRunner

from timesketch_api_client import test_lib as api_test_lib


from .. import test_lib
from .events import events_group


class EventsTest(unittest.TestCase):
    """Test Events."""

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.ctx = test_lib.get_cli_context()

    def test_add_event_wrong_param(self):
        """Test to add a tag to an event with wrong parameters."""
        runner = CliRunner()
        result = runner.invoke(
            events_group,
            ["annotate", "--event_id", "1", "--tag", "test", "1"],
            obj=self.ctx,
        )
        assert (
            "Error: No such option: --event_id Did you mean --event-id?"
            in result.output
        )

    def test_add_event_tag_missing_timeline_id(self):
        """Test to add a tag to an event."""
        runner = CliRunner()
        result = runner.invoke(
            events_group,
            ["annotate", "--event-id", "1", "--tag", "test", "1"],
            obj=self.ctx,
        )
        assert "Error: Missing option '--timeline-id'." in result.output

    def test_add_event_comment_vs_comments(self):
        """Test to add a comment to an event but using comment instead of comments"""
        runner = CliRunner()
        result = runner.invoke(
            events_group,
            [
                "annotate",
                "--event-id",
                "1",
                "--comments",
                "test foobar",
                "--timeline-id",
                "1",
            ],
            obj=self.ctx,
        )

        expected_output = "No such option: --comments Did you mean --comment?"
        assert expected_output in result.output

    # TODO: Fix test
    def test_add_event_tag(self):
        """Test to add a tag to an event."""
        runner = CliRunner()
        # The annotate command echoes a dictionary directly; its output format
        # is not controlled by ctx.obj.output_format.
        # Setting output_format_from_flag might have unintended side effects
        # on the context object, so we'll rely on the default context setup.
        # self.ctx.output_format_from_flag = "text"

        # Get the existing sketch object from the context.
        sketch_to_configure = self.ctx.sketch

        # Explicitly mock the methods on the sketch_to_configure object
        sketch_to_configure.get_timeline = mock.MagicMock()
        sketch_to_configure.tag_events = mock.MagicMock()
        sketch_to_configure.get_event = mock.MagicMock()
        sketch_to_configure.comment_event = (
            mock.MagicMock()
        )  # In case comment is also used

        # Mock get_timeline to return a mock timeline with an index_name
        mock_timeline = mock.MagicMock()
        mock_timeline.index_name = "mock_timeline_index_123"
        sketch_to_configure.get_timeline.return_value = mock_timeline

        # Mock tag_events to be a simple no-op or a safe mock
        sketch_to_configure.tag_events.return_value = None

        # Mock get_event to return the event structure expected by the command's output
        sketch_to_configure.get_event.return_value = (
            {  # The output of click.echo(return_value) should contain "['test']"
                "message": "Event with tag",
                "labels": ["test"],
                "_id": "1",
                "_index": mock_timeline.index_name,
            }
        )

        result = runner.invoke(
            events_group,
            [
                "annotate",
                "--event-id",
                "1",
                "--timeline-id",
                "1",
                "--tag",
                "test",
            ],
            obj=self.ctx,
        )

        final_output = result.output
        exit_code = result.exit_code
        exception_info = result.exc_info
        exception_obj = result.exception

        # Print debugging information if an exception occurred
        if exception_obj:
            import traceback

            print(f"Command failed with exception: {exception_obj}")
            traceback.print_tb(exception_info[2])

        assert exit_code == 0, (
            f"Command exited with code {exit_code}.\n"
            f"Output:\n{final_output}\n"
            f"Exception: {exception_obj}"
        )

        assert (
            "['test']" in final_output
        ), f"Substring \"['test']\" not found in output.\nOutput:\n{final_output}"

    # TODO: Fix test
    def test_add_event_tags(self):
        """Test to add multiple tags to an event."""
        runner = CliRunner()
        result = runner.invoke(
            events_group,
            [
                "annotate",
                "--event-id",
                "1",
                "--tag",
                "test1,test2",
                "--timeline-id",
                "1",
            ],
            obj=self.ctx,
        )

        assert 0 is result.exit_code

    # TODO: Fix test
    def test_add_event_tags_for_non_existent_event_json(self):
        """Test 'events annotate' for a non-existent event with JSON output
        format.

        Verifies that attempting to tag an event that cannot be found,
        while requesting JSON output, results in an error message and
        a non-zero exit code.
        """
        runner = CliRunner()
        result = runner.invoke(
            events_group,
            [
                "--output-format",
                "json",
                "annotate",
                "--event-id",
                "1",
                "--tag",
                "test1,test2",
                "--timeline-id",
                "1",
            ],
            obj=self.ctx,
        )

        assert "No such event" in result.output
        assert 1 is result.exit_code

    def test_failed_add_event(self):
        """Test to add an event to a sketch with an error."""
        runner = CliRunner()
        result = runner.invoke(events_group, ["add"], obj=self.ctx)
        assert "Error: Missing option '--message'" in result.output

    def test_add_event(self):
        """Test to add an event to a sketch."""
        runner = CliRunner()
        result = runner.invoke(
            events_group,
            [
                "add",
                "--message",
                "test message",
                "--date",
                "2023-03-04T11:31:12",
                "--timestamp-desc",
                "test",
            ],
            obj=self.ctx,
        )
        assert "Event added to sketch: test" in result.output
