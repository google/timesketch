# Copyright 2015 Google Inc. All rights reserved.
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
"""This module implements HTTP request handlers for the story views."""

from flask import Blueprint
from flask import current_app
from flask import render_template
from flask_login import login_required

from timesketch.models.sketch import Sketch
from timesketch.models.story import Story

# Register flask blueprint
story_views = Blueprint(u'story_views', __name__)


@story_views.route(u'/sketch/<int:sketch_id>/stories/')
@story_views.route(u'/sketch/<int:sketch_id>/stories/<int:story_id>/')
@login_required
def story(sketch_id, story_id=None):
    """Generates the story list template.

    Returns:
        Template with context.
    """
    sketch = Sketch.query.get_with_acl(sketch_id)
    graphs_enabled = current_app.config[u'GRAPH_BACKEND_ENABLED']

    current_story = None
    if story_id:
        current_story = Story.query.get(story_id)
    return render_template(
        u'sketch/stories.html', sketch=sketch, story=current_story,
        graphs_enabled=graphs_enabled)
