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
"""Story resources for version 1 of the Timesketch API."""

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user
from sqlalchemy import desc

from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.lib import forms
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.stories import api_fetcher as story_api_fetcher
from timesketch.lib.stories import manager as story_export_manager
from timesketch.models import db_session
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Story


class StoryListResource(resources.ResourceMixin, Resource):
    """Resource to get all stories for a sketch or to create a new story."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            Stories in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )

        stories = []
        for story in Story.query.filter_by(sketch=sketch).order_by(
            desc(Story.created_at)
        ):
            stories.append(story)
        return self.to_json(stories)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        form = forms.StoryForm.build(request)
        if not form.validate_on_submit():
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to validate form data.")

        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch.",
            )

        title = ""
        if form.title.data:
            title = form.title.data
        story = Story(title=title, content="[]", sketch=sketch, user=current_user)
        db_session.add(story)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)
        return self.to_json(story, status_code=HTTP_STATUS_CODE_CREATED)


class StoryResource(resources.ResourceMixin, Resource):
    """Resource to get a story."""

    @staticmethod
    def _export_story(story, sketch_id, export_format="markdown"):
        """Returns a story in a format as requested in export_format.

        Args:
            story: a story object (instance of Story) that is to be exported.
            sketch_id: integer with the sketch ID.
            export_format: string with the name of the format to export the
                story to. Defaults to "markdown".

        Returns:
            The exported story in the format described. This could be a text
            or a binary, depending on the output format.
        """
        exporter_class = story_export_manager.StoryExportManager.get_exporter(
            export_format
        )
        if not exporter_class:
            return b""

        with exporter_class() as exporter:
            data_fetcher = story_api_fetcher.ApiDataFetcher()
            data_fetcher.set_sketch_id(sketch_id)

            exporter.set_data_fetcher(data_fetcher)
            exporter.set_title(story.title)
            exporter.set_creation_date(story.created_at.isoformat())
            if story.user:
                exporter.set_author(story.user.username)
            exporter.set_exporter(current_user.username)

            exporter.from_string(story.content)
            return exporter.export_story()

    @login_required
    def get(self, sketch_id, story_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            story_id: Integer primary key for a story database model

        Returns:
            A story in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        story = Story.get_by_id(story_id)

        if not story:
            msg = "No Story found with this ID."
            abort(HTTP_STATUS_CODE_NOT_FOUND, msg)

        if not sketch:
            msg = "No sketch found with this ID."
            abort(HTTP_STATUS_CODE_NOT_FOUND, msg)

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )

        # Check that this story belongs to the sketch
        if story.sketch_id != sketch.id:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "Sketch ID ({0:d}) does not match with the ID in "
                "the story ({1:d})".format(sketch.id, story.sketch_id),
            )

        # Only allow editing if the current user is the author.
        # This is needed until we have proper collaborative editing and
        # locking implemented.
        meta = dict(is_editable=False)
        if current_user == story.user:
            meta["is_editable"] = True

        return self.to_json(story, meta=meta)

    @login_required
    def post(self, sketch_id, story_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            story_id: Integer primary key for a story database model

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        story = Story.get_by_id(story_id)

        if not story:
            msg = "No Story found with this ID."
            abort(HTTP_STATUS_CODE_NOT_FOUND, msg)

        if not sketch:
            msg = "No sketch found with this ID."
            abort(HTTP_STATUS_CODE_NOT_FOUND, msg)

        if story.sketch_id != sketch.id:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "Sketch ID ({0:d}) does not match with the ID in "
                "the story ({1:d})".format(sketch.id, story.sketch_id),
            )

        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch.",
            )

        form = request.json
        if not form:
            form = request.data

        if form and form.get("export_format"):
            export_format = form.get("export_format")
            return jsonify(
                story=self._export_story(
                    story=story, sketch_id=sketch_id, export_format=export_format
                )
            )

        story.title = form.get("title", "")
        story.content = form.get("content", "[]")
        db_session.add(story)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(story, status_code=HTTP_STATUS_CODE_CREATED)

    @login_required
    def delete(self, sketch_id, story_id):
        """Handles DELETE request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            story_id: Integer primary key for a story database model
        """
        sketch = Sketch.get_with_acl(sketch_id)
        story = Story.get_by_id(story_id)

        if not story:
            msg = "No Story found with this ID."
            abort(HTTP_STATUS_CODE_NOT_FOUND, msg)

        if not sketch:
            msg = "No sketch found with this ID."
            abort(HTTP_STATUS_CODE_NOT_FOUND, msg)

        # Check that this timeline belongs to the sketch
        if story.sketch_id != sketch.id:
            msg = (
                "The sketch ID ({0:d}) does not match with the story"
                "sketch ID ({1:d})".format(sketch.id, story.sketch_id)
            )
            abort(HTTP_STATUS_CODE_FORBIDDEN, msg)

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have write permission on the sketch.",
            )

        sketch.stories.remove(story)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return HTTP_STATUS_CODE_OK
