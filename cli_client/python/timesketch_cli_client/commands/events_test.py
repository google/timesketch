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

    def test_add_event_tag(self):
        """Test to add a tag to an event."""
        runner = CliRunner()
        result = runner.invoke(
            events_group,
            [
                "--output-format",
                "json",
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
        print(result.output)
        print(result.exception)
        print(result.exit_code)
        assert "['test']" in result.output

    # todo: Fix the remaining tests here

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

    def test_add_event_tags_json(self):
        """Test to add multiple tags to an event and output as json."""
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

    def text_no_output_format_defined_in_config(self):
        """Test to add an event to a sketch."""

        self.ctx = test_lib.get_cli_context_no_output()
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
