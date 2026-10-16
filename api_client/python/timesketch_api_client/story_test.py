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

from __future__ import unicode_literals

import json
import unittest
import mock

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

    def test_add_text_to_unloaded_story_keeps_existing_blocks(self):
        """Test adding a block before the blocks were read keeps them."""
        story = self.sketch.list_stories()[0]
        session = story._api.session  # pylint: disable=protected-access
        with mock.patch.object(session, "post", wraps=session.post) as post:
            story.add_text("A new note.")

        posted = json.loads(post.call_args_list[0].kwargs["json"]["content"])
        self.assertEqual(len(posted), 4)
        self.assertEqual(posted[0]["content"], "# My Heading\nWith Some Text.")
        self.assertEqual(posted[-1]["content"], "A new note.")
