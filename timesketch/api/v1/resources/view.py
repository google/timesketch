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
"""View resources for version 1 of the Timesketch API."""

import json

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.lib import forms
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models import db_session
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sketch import View


class ViewListResource(resources.ResourceMixin, Resource):
    """Resource to create a View."""

    @staticmethod
    def create_view_from_form(sketch, form):
        """Creates a view from form data.

        Args:
            sketch: Instance of timesketch.models.sketch.Sketch
            form: Instance of timesketch.lib.forms.SaveViewForm

        Returns:
            A view (Instance of timesketch.models.sketch.View)
        """
        # Default to user supplied data
        view_name = form.name.data
        query_string = form.query.data

        query_filter_dict = form.filter.data
        # Stripping potential pagination from views before saving it.
        if "from" in query_filter_dict:
            del query_filter_dict["from"]
        query_filter = json.dumps(query_filter_dict, ensure_ascii=False)
        query_dsl = json.dumps(form.dsl.data, ensure_ascii=False)

        if isinstance(query_filter, tuple):
            query_filter = query_filter[0]

        # No search template by default (before we know if the user want to
        # create a template or use an existing template when creating the view)
        searchtemplate = None

        # Create view from a search template
        if form.from_searchtemplate_id.data:
            # Get the template from the datastore
            template_id = form.from_searchtemplate_id.data
            searchtemplate = SearchTemplate.get_by_id(template_id)

            # Copy values from the template
            view_name = searchtemplate.name
            query_string = searchtemplate.query_string
            query_filter = searchtemplate.query_filter
            query_dsl = searchtemplate.query_dsl
            # WTF form returns a tuple for the filter. This is not
            # compatible with SQLAlchemy.
            if isinstance(query_filter, tuple):
                query_filter = query_filter[0]

        if not view_name:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "View name is missing.")

        # Create a new search template based on this view (only if requested by
        # the user).
        if form.new_searchtemplate.data:
            query_filter_dict = json.loads(query_filter)
            if query_filter_dict.get("indices", None):
                query_filter_dict["indices"] = "_all"

            query_filter = json.dumps(query_filter_dict, ensure_ascii=False)

            searchtemplate = SearchTemplate(
                name=view_name,
                user=current_user,
                query_string=query_string,
                query_filter=query_filter,
                query_dsl=query_dsl,
            )
            db_session.add(searchtemplate)
            db_session.commit()

        # Create the view in the database
        view = View(
            name=view_name,
            sketch=sketch,
            user=current_user,
            query_string=query_string,
            query_filter=query_filter,
            query_dsl=query_dsl,
            searchtemplate=searchtemplate,
        )
        db_session.add(view)
        db_session.commit()

        return view

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            Views in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )
        return self.to_json(sketch.get_named_views)

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        form = forms.SaveViewForm.build(request)
        if not form.validate_on_submit():
            error_message = "Unable to save view, not able to validate form data: "
            for error in form.errors.values():
                error_message += f"{error}, "
            abort(HTTP_STATUS_CODE_BAD_REQUEST, error_message[:-2])

        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch.",
            )

        view = self.create_view_from_form(sketch, form)

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(view, status_code=HTTP_STATUS_CODE_CREATED)


class ViewResource(resources.ResourceMixin, Resource):
    """Resource to get a view."""

    @login_required
    def get(self, sketch_id, view_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            view_id: Integer primary key for a view database model

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        view = View.get_by_id(view_id)

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )

        # Check that this view belongs to the sketch
        if view.sketch_id != sketch.id:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "Sketch ID ({0:d}) does not match with the sketch ID "
                "that is defined in the view ({1:d})".format(view.sketch_id, sketch.id),
            )

        # If this is a user state view, check that it
        # belongs to the current_user
        if view.name == "" and view.user != current_user:
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "Unable to view a state view that belongs to a " "different user.",
            )

        # Check if view has been deleted
        if view.get_status.status == "deleted":
            meta = dict(deleted=True, name=view.name)
            schema = dict(meta=meta, objects=[])
            return jsonify(schema)

        # Make sure we have all expected attributes in the query filter.
        view.query_filter = view.validate_filter()
        db_session.add(view)
        db_session.commit()

        return self.to_json(view)

    @login_required
    def delete(self, sketch_id, view_id):
        """Handles DELETE request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            view_id: Integer primary key for a view database model
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch.",
            )
        view = View.get_by_id(view_id)
        if not view:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No view found with this ID.")

        # Check that this view belongs to the sketch
        if view.sketch_id != sketch.id:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "The view does not belong to the sketch ({0:d} vs "
                "{1:d})".format(view.sketch_id, sketch.id),
            )

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write permission on sketch.",
            )

        view.set_status(status="deleted")

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return HTTP_STATUS_CODE_OK

    @login_required
    def post(self, sketch_id, view_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model
            view_id: Integer primary key for a view database model

        Returns:
            A view in JSON (instance of flask.wrappers.Response)
        """
        form = forms.SaveViewForm.build(request)
        if not form.validate_on_submit():
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to update view, not able to validate form data",
            )
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch.",
            )

        view = View.get_by_id(view_id)
        if not view:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No view found with this ID.")

        if view.sketch.id != sketch.id:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to update view, view not attached to sketch.",
            )

        view.query_string = form.query.data
        description = form.description.data
        if description:
            view.description = description

        query_filter = form.filter.data

        # Stripping potential pagination from views before saving it.
        if "from" in query_filter:
            del query_filter["from"]

        view.query_filter = json.dumps(query_filter, ensure_ascii=False)

        view.query_dsl = json.dumps(form.dsl.data, ensure_ascii=False)

        name = form.name.data
        if name:
            view.name = name

        view.user = current_user
        view.sketch = sketch

        if form.dsl.data:
            view.query_string = ""

        db_session.add(view)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(view, status_code=HTTP_STATUS_CODE_CREATED)
