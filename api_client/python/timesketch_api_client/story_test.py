# Copyright 2020 Google Inc. All rights reserved.
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
"""Tests for the Timesketch API client"""

import unittest
from unittest import mock

from . import client
from . import test_lib
from . import story as story_lib


class StoryTest(unittest.TestCase):
    """Test Story object."""

    @mock.patch("requests.Session", test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")
        self.sketch = self.api_client.get_sketch(1)

    def test_story(self):
        """Test story object."""
        story = self.sketch.list_stories()[0]
        self.assertIsInstance(story, story_lib.Story)
        self.assertEqual(story.id, 1)
        self.assertEqual(story.title, "My First Story")
        self.assertEqual(len(story), 3)
        blocks = list(story.blocks)
        text_count = 0
        view_count = 0
        for block in blocks:
            if block.TYPE == "text":
                text_count += 1
            elif block.TYPE == "view":
                view_count += 1

        self.assertEqual(text_count, 2)
        self.assertEqual(view_count, 1)

        self.assertEqual(blocks[0].text, "# My Heading\nWith Some Text.")

        blocks[0].move_down()
        blocks = list(story.blocks)
        self.assertEqual(len(blocks), 3)
        self.assertEqual(blocks[1].text, "# My Heading\nWith Some Text.")

    def test_add_text_commit_status(self):
        """Test add_text propagates the boolean commit status."""
        story = self.sketch.list_stories()[0]

        ok_response = mock.Mock(status_code=200)
        with mock.patch.object(
            self.api_client.session, "post", return_value=ok_response
        ):
            self.assertTrue(story.add_text("Committed text block"))

        fail_response = mock.Mock(
            status_code=500, reason="Internal Server Error", text="Server error"
        )
        with mock.patch.object(
            self.api_client.session, "post", return_value=fail_response
        ):
            self.assertFalse(story.add_text("Uncommitted text block"))

    def test_null_safe_exports_and_view_name(self):
        """Test None API values coalesce to empty strings instead of 'None'."""
        story = self.sketch.list_stories()[0]

        with mock.patch.object(story, "to_export_format", return_value={"story": None}):
            self.assertEqual(story.to_html(), "")
            self.assertEqual(story.to_markdown(), "")

        view_block = story_lib.ViewBlock(story, 0)
        mock_view = mock.Mock()
        mock_view.id = 1
        mock_view.name = None
        view_block.feed(mock_view)
        self.assertEqual(view_block.view_name, "")


if __name__ == "__main__":
    unittest.main()
