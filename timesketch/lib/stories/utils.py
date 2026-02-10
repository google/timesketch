# Copyright 2025 Google Inc. All rights reserved.
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
"""Actions for LLM features in Timesketch."""
import json
import logging
import time
from timesketch.models import db_session
from timesketch.models.sketch import Sketch, Story

logger = logging.getLogger("timesketch.lib.stories.utils")


def create_story(sketch: Sketch, content: str, title: str = None) -> int:
    """Creates a Timesketch story with the given content.
    Args:
        sketch: Sketch object.
        content: Text content to add to the story.
        title: Title for the story. If None, a default title
            with timestamp will be used.
    Returns:
        The ID of the newly created story.
    Raises:
        ValueError: If there's an error creating the story.
    """
    if title is None:
        title = f"Investigation Report - {time.strftime('%Y-%m-%d %H:%M')}"
    try:
        story = Story(title=title, sketch=sketch, user=sketch.user)
        content_blocks = [
            {
                "componentName": "",
                "componentProps": {},
                "content": content,
                "edit": False,
                "showPanel": False,
                "isActive": False,
            }
        ]
        story.content = json.dumps(content_blocks)
        db_session.add(story)
        db_session.commit()
        logger.debug("Created story with ID %s for sketch %s", story.id, sketch.id)
        return story.id
    except Exception as e:
        raise ValueError(f"Error creating story: {e}") from e
