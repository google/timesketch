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
"""Sketch resources for version 1 of the Timesketch API."""

import logging

import opensearchpy

from flask import jsonify
from flask import request
from flask import abort
from flask import current_app
from flask_restful import Resource
from flask_restful import reqparse
from flask_restful import inputs
from flask_login import login_required
from flask_login import current_user
from sqlalchemy import not_
from sqlalchemy import or_

from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.lib import forms
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.aggregators import manager as aggregator_manager
from timesketch.lib.emojis import get_emojis_as_dict
from timesketch.models import db_session
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sketch import View


logger = logging.getLogger("timesketch.sketch_api")


class SketchListResource(resources.ResourceMixin, Resource):
    """Resource for listing sketches."""

    DEFAULT_SKETCHES_PER_PAGE = 10

    def __init__(self):
        super().__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            "scope", type=str, required=False, default="user", location="args"
        )
        self.parser.add_argument(
            "page", type=int, required=False, default=1, location="args"
        )
        self.parser.add_argument(
            "per_page",
            type=int,
            required=False,
            default=self.DEFAULT_SKETCHES_PER_PAGE,
            location="args",
        )
        self.parser.add_argument(
            "search_query", type=str, required=False, default=None, location="args"
        )
        self.parser.add_argument(
            "include_archived",
            type=inputs.boolean,
            required=False,
            default=False,
            location="args",
        )

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of sketches (instance of flask.wrappers.Response)
        """
        args = self.parser.parse_args()
        scope = args.get("scope")
        page = args.get("page")
        per_page = args.get("per_page")
        search_query = args.get("search_query")
        include_archived = args.get("include_archived")

        if current_user.admin and scope == "admin":
            sketch_query = Sketch.query
        else:
            sketch_query = Sketch.all_with_acl()

        base_filter = sketch_query.filter(
            not_(Sketch.Status.status == "deleted"),
            not_(Sketch.Status.status == "archived"),
            Sketch.Status.parent,
        ).order_by(Sketch.updated_at.desc())

        base_filter_with_archived = sketch_query.filter(
            not_(Sketch.Status.status == "deleted"), Sketch.Status.parent
        ).order_by(Sketch.updated_at.desc())

        filtered_sketches = base_filter_with_archived
        sketches = []
        return_sketches = []

        has_next = False
        has_prev = False
        next_page = None
        prev_page = None
        current_page = 1
        total_pages = 0
        total_items = 0

        if scope == "recent":
            # Get list of sketches that the user has actively searched in.
            # TODO: Make this cover more actions such as story updates etc.
            # TODO: Right now we only return the top 3, make this configurable.
            views = (
                View.query.filter_by(user=current_user, name="")
                .order_by(View.updated_at.desc())
                .limit(10)
            )
            sketches = [
                view.sketch
                for view in views
                if view.sketch.get_status.status != "deleted"
            ]
            total_items = len(sketches)
        elif scope == "admin":
            if not current_user.admin:
                abort(HTTP_STATUS_CODE_FORBIDDEN, "User is not an admin.")
            if include_archived:
                filtered_sketches = base_filter_with_archived
            else:
                filtered_sketches = base_filter
        elif scope == "user":
            filtered_sketches = base_filter.filter_by(user=current_user)
        elif scope == "archived":
            filtered_sketches = sketch_query.filter(
                Sketch.status.any(status="archived")
            )
        elif scope == "shared":
            filtered_sketches = base_filter.filter(Sketch.user != current_user)
        elif scope == "search":
            filtered_sketches = base_filter_with_archived.filter(
                or_(
                    Sketch.name.ilike(f"%{search_query}%"),
                    Sketch.description.ilike(f"%{search_query}%"),
                )
            )

        if not sketches:
            pagination = filtered_sketches.paginate(page=page, per_page=per_page)
            sketches = pagination.items
            has_next = pagination.has_next
            has_prev = pagination.has_prev
            next_page = pagination.next_num
            prev_page = pagination.prev_num
            current_page = pagination.page
            total_pages = pagination.pages
            total_items = pagination.total

        for sketch in sketches:
            # Return a subset of the sketch objects to reduce the amount of
            # data sent to the client.
            return_sketches.append(
                {
                    "id": sketch.id,
                    "name": sketch.name,
                    "description": sketch.description,
                    "created_at": str(sketch.created_at),
                    "last_activity": utils.get_sketch_last_activity(sketch),
                    "user": sketch.user.username,
                    "status": sketch.get_status.status,
                }
            )

        meta = {
            "current_user": current_user.username,
            "has_next": has_next,
            "has_prev": has_prev,
            "next_page": next_page,
            "prev_page": prev_page,
            "current_page": current_page,
            "total_pages": total_pages,
            "total_items": total_items,
        }
        return jsonify({"objects": return_sketches, "meta": meta})

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        form = forms.NameDescriptionForm.build(request)
        if not form.validate_on_submit():
            error_message = "Unable to validate form data: "
            for error in form.errors.values():
                error_message += f"{error}, "
            abort(HTTP_STATUS_CODE_BAD_REQUEST, error_message[:-2])

        sketch = Sketch(name=form.name.data, description=form.description.data)
        db_session.add(sketch)
        sketch.user = current_user
        sketch.status.append(sketch.Status(user=None, status="new"))
        db_session.commit()

        # Give the requesting user permissions on the new sketch.
        sketch.grant_permission(permission="read", user=current_user)
        sketch.grant_permission(permission="write", user=current_user)
        sketch.grant_permission(permission="delete", user=current_user)
        return self.to_json(sketch, status_code=HTTP_STATUS_CODE_CREATED)


class SketchResource(resources.ResourceMixin, Resource):
    """Resource to get a sketch."""

    @staticmethod
    def _add_label(sketch, label):
        """Add a label to the sketch."""
        if sketch.has_label(label):
            logger.warning(
                "Unable to apply the label [{0:s}] to sketch {1:d}, "
                "already exists.".format(label, sketch.id)
            )
            return False
        sketch.add_label(label, user=current_user)
        return True

    @staticmethod
    def _remove_label(sketch, label):
        """Removes a label to the sketch."""
        if not sketch.has_label(label):
            logger.warning(
                "Unable to remove the label [{0:s}] to sketch {1:d}, "
                "label does not exist.".format(label, sketch.id)
            )
            return False
        sketch.remove_label(label)
        return True

    @staticmethod
    def _get_sketch_for_admin(sketch):
        """Returns a limited sketch view for administrators.

        An administrator needs to get information about all sketches
        that are stored on the backend. However that view should be
        limited for sketches that user does not have explicit read
        or other permissions as well. In those cases the returned
        sketch only contains information about the name, description,
        etc but not any information about the data, nor any access
        to the underlying data of the sketch.

        Args:
            sketch: a sketch object (instance of models.Sketch)

        Returns:
            A limited view of a sketch in JSON (instance of
            flask.wrappers.Response)
        """
        if sketch.get_status.status == "archived":
            status = "archived"
        else:
            status = "admin_view"

        sketch_fields = {
            "id": sketch.id,
            "name": sketch.name,
            "description": sketch.description,
            "user": {"username": current_user.username},
            "timelines": [],
            "stories": [],
            "active_timelines": [],
            "label_string": sketch.label_string,
            "status": [{"id": 0, "status": status}],
            "all_permissions": sketch.all_permissions,
            "created_at": sketch.created_at,
            "updated_at": sketch.updated_at,
        }

        meta = {
            "current_user": current_user.username,
            "last_activity": utils.get_sketch_last_activity(sketch),
        }
        return jsonify({"objects": [sketch_fields], "meta": meta})

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        if current_user.admin:
            sketch = Sketch.get_by_id(sketch_id)
            if not sketch.has_permission(current_user, "read"):
                return self._get_sketch_for_admin(sketch)
        else:
            sketch = Sketch.get_with_acl(sketch_id)

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        aggregators = {}
        for _, cls in aggregator_manager.AggregatorManager.get_aggregators():
            aggregators[cls.NAME] = {
                "form_fields": cls.FORM_FIELDS,
                "display_name": cls.DISPLAY_NAME,
                "description": cls.DESCRIPTION,
            }

        # Get mappings for all indices in the sketch. This is used to set
        # columns shown in the event list.
        sketch_indices = [t.searchindex.index_name for t in sketch.active_timelines]

        # Make sure the list of index names is uniq
        sketch_indices = list(set(sketch_indices))

        # Get event count and size on disk for each index in the sketch.
        indices_metadata = {}
        stats_per_timeline = {}
        for timeline in sketch.active_timelines:
            indices_metadata[timeline.searchindex.index_name] = {}
            stats_per_timeline[timeline.id] = {"count": 0}

        if not sketch_indices:
            mappings_settings = {}
        else:
            try:
                mappings_settings = self.datastore.client.indices.get_mapping(
                    index=sketch_indices
                )
            except opensearchpy.NotFoundError:
                logger.error(
                    "Unable to get indices mapping in datastore, for "
                    "indices: {0:s}".format(",".join(sketch_indices))
                )
                mappings_settings = {}

        mappings = []

        for index_name, value in mappings_settings.items():
            # The structure is different in ES version 6.x and lower. This check
            # makes sure we support both old and new versions.
            properties = value["mappings"].get("properties")
            if not properties:
                properties = next(iter(value["mappings"].values())).get("properties")

            # Determine if index is from the time before multiple timelines per
            # index. This is used in the UI to support both modes.
            is_legacy = bool("__ts_timeline_id" not in properties)
            indices_metadata[index_name]["is_legacy"] = is_legacy

            for field, value_dict in properties.items():
                mapping_dict = {}
                # Exclude internal fields
                if field.startswith("__"):
                    continue
                if field == "timesketch_label":
                    continue
                mapping_dict["field"] = field
                mapping_dict["type"] = value_dict.get("type", "n/a")
                mappings.append(mapping_dict)

        # Get number of events per timeline
        if sketch_indices:
            # Support legacy indices.
            for timeline in sketch.active_timelines:
                index_name = timeline.searchindex.index_name
                if indices_metadata[index_name].get("is_legacy", False):
                    doc_count, _ = self.datastore.count(indices=index_name)
                    stats_per_timeline[timeline.id] = {"count": doc_count}
            count_agg_spec = {
                "aggs": {
                    "per_timeline": {
                        "terms": {
                            "field": "__ts_timeline_id",
                            "size": len(sketch.timelines),
                        }
                    }
                }
            }
            # pylint: disable=unexpected-keyword-arg, no-value-for-parameter
            count_agg = self.datastore.client.search(
                index=sketch_indices, body=count_agg_spec, size=0
            )

            count_per_timeline = (
                count_agg.get("aggregations", {})
                .get("per_timeline", {})
                .get("buckets", [])
            )
            for count_stat in count_per_timeline:
                stats_per_timeline[count_stat["key"]] = {
                    "count": count_stat["doc_count"]
                }

        # Make the list of dicts unique
        mappings = {v["field"]: v for v in mappings}.values()

        views = []
        for view in sketch.get_named_views:
            if not view.user:
                username = "System"
            else:
                username = view.user.username
            view = {
                "name": view.name,
                "description": view.description,
                "id": view.id,
                "query": view.query_string,
                "filter": view.query_filter,
                "user": username,
                "created_at": view.created_at,
                "updated_at": view.updated_at,
            }
            views.append(view)

        views.sort(key=lambda x: x.get("name", "Z").lower())

        stories = []
        for story in sketch.stories:
            if not story.user:
                username = "System"
            else:
                username = story.user.username
            story = {
                "id": story.id,
                "title": story.title,
                "user": username,
                "created_at": story.created_at,
                "updated_at": story.updated_at,
            }
            stories.append(story)
        meta = dict(
            aggregators=aggregators,
            views=views,
            stories=stories,
            searchtemplates=[
                {"name": searchtemplate.name, "id": searchtemplate.id}
                for searchtemplate in SearchTemplate.query.all()
            ],
            emojis=get_emojis_as_dict(),
            permissions={
                "public": bool(sketch.is_public),
                "read": bool(sketch.has_permission(current_user, "read")),
                "write": bool(sketch.has_permission(current_user, "write")),
                "delete": bool(sketch.has_permission(current_user, "delete")),
            },
            collaborators={
                "users": [user.username for user in sketch.collaborators],
                "groups": [group.name for group in sketch.groups],
            },
            attributes=utils.get_sketch_attributes(sketch),
            mappings=list(mappings),
            indices_metadata=indices_metadata,
            stats_per_timeline=stats_per_timeline,
            last_activity=utils.get_sketch_last_activity(sketch),
            sketch_labels=[label.label for label in sketch.labels],
            filter_labels=self.datastore.get_filter_labels(sketch.id, sketch_indices),
        )
        return self.to_json(sketch, meta=meta)

    @login_required
    def delete(self, sketch_id):
        """Handles DELETE request to the resource."""
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "delete"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                ("User does not have sufficient access rights to " "delete a sketch."),
            )
        not_delete_labels = current_app.config.get("LABELS_TO_PREVENT_DELETION", [])
        for label in not_delete_labels:
            if sketch.has_label(label):
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    "Sketch with the label [{0:s}] cannot be deleted.".format(label),
                )
        sketch.set_status(status="deleted")
        return HTTP_STATUS_CODE_OK

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            A sketch in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch.",
            )

        form = request.json
        if not form:
            form = request.data

        update_object = False
        name = form.get("name", "")
        if name:
            sketch.name = name
            update_object = True

        description = form.get("description", "")
        if description:
            sketch.description = description
            update_object = True

        labels = form.get("labels", [])
        label_action = form.get("label_action", "add")
        if label_action not in ("add", "remove"):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Label actions needs to be either "add" or "remove", '
                "not [{0:s}]".format(label_action),
            )

        if labels and isinstance(labels, (tuple, list)):
            for label in labels:
                if label_action == "add":
                    changed = self._add_label(sketch=sketch, label=label)
                elif label_action == "remove":
                    changed = self._remove_label(sketch=sketch, label=label)

                if changed:
                    update_object = True

        if update_object:
            db_session.add(sketch)
            db_session.commit()

        return self.to_json(sketch, status_code=HTTP_STATUS_CODE_CREATED)
