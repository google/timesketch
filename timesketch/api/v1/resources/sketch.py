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
from opensearchpy.exceptions import NotFoundError


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
from timesketch.lib.definitions import HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR
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

        Returns a list of sketches that the user has access to, filtered
        and paginated according to the provided query parameters.

        Query Parameters:
            scope (str): Optional. Defines the scope of the sketches to return.
                Can be one of:
                - "user": (Default) Sketches owned by the current user.
                - "shared": Sketches shared with the current user.
                - "all": All sketches accessible by the user (owned and shared).
                - "recent": Sketches recently accessed by the user.
                - "archived": All archived sketches the user has access to.
                - "admin": All sketches on the system (admin only).
                - "search": Sketches matching the search_query.
            page (int): Optional. The page number for pagination. Defaults to 1.
            per_page (int): Optional. The number of sketches per page.
                Defaults to 10.
            search_query (str): Optional. The search term to use when scope
                is "search".
            include_archived (bool): Optional. Whether to include archived
                sketches. This applies to "user", "shared", "all", and "admin"
                scopes. Defaults to False.

        Returns:
            A flask.wrappers.Response object with a JSON payload containing:
            - "objects": A list of sketch dictionaries.
            - "meta": A dictionary with pagination information.
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

        filtered_sketches = None
        sketches = []
        return_sketches = []

        has_next = False
        has_prev = False
        next_page = None
        prev_page = None
        current_page = 1
        total_pages = 0
        total_items = 0

        if include_archived:
            base_filter = base_filter_with_archived
        else:
            base_filter = base_filter.filter(not_(Sketch.status.any(status="archived")))

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
        elif scope == "archived":
            filtered_sketches = base_filter_with_archived.filter(
                Sketch.status.any(status="archived"),
            )
        elif scope == "admin":
            if not current_user.admin:
                abort(HTTP_STATUS_CODE_FORBIDDEN, "User is not an admin.")
            filtered_sketches = base_filter
        elif scope == "user":
            filtered_sketches = base_filter.filter_by(user=current_user)
        elif scope == "shared":
            filtered_sketches = base_filter.filter(Sketch.user != current_user)
        elif scope == "all":
            filtered_sketches = base_filter
        elif scope == "search":
            search_base = base_filter
            filtered_sketches = search_base.filter(
                or_(
                    Sketch.name.ilike(f"%{search_query}%"),
                    Sketch.description.ilike(f"%{search_query}%"),
                )
            )

        if not sketches and filtered_sketches:
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
            error_messages = []
            for field_errors in form.errors.values():
                error_messages.extend(field_errors)
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                f"Unable to validate form data: {', '.join(error_messages)}",
            )

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
                "Unable to apply the label [%s] to sketch %s, already exists.",
                label,
                sketch.id,
            )
            return False
        sketch.add_label(label, user=current_user)
        return True

    @staticmethod
    def _remove_label(sketch, label):
        """Removes a label to the sketch."""
        if not sketch.has_label(label):
            logger.warning(
                "Unable to remove the label [%s] to sketch %s, label does not exist.",
                label,
                sketch.id,
            )
            return False
        sketch.remove_label(label)
        return True

    @staticmethod
    def _get_sketch_for_admin(sketch: Sketch):
        """Returns a limited sketch view for administrators.

        An administrator needs to get information about all sketches
        that are stored on the backend. However that view should be
        limited for sketches that user does not have explicit read
        or other permissions as well. In those cases the returned
        sketch only contains information about the name, description,
        etc but not any information about the data, nor any access
        to the underlying data of the sketch.

        Args:
            sketch: (object) a sketch object (instance of models.Sketch)

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
        sketch_indices = [
            t.searchindex.index_name
            for t in sketch.active_timelines
            if t.searchindex.get_status.status == "ready"
        ]

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
                    "Unable to get indices mapping in datastore, for indices: [%s]",
                    ",".join(sketch_indices),
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
                "size": 0,
                "aggs": {
                    "per_timeline": {
                        "terms": {
                            "field": "__ts_timeline_id",
                            "size": len(sketch.timelines),
                        }
                    }
                },
            }
            count_agg = self.datastore.search(
                sketch_id=sketch.id,
                indices=sketch_indices,
                query_dsl=count_agg_spec,
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
        meta = {
            "aggregators": aggregators,
            "views": views,
            "stories": stories,
            "searchtemplates": [
                {"name": searchtemplate.name, "id": searchtemplate.id}
                for searchtemplate in SearchTemplate.query.all()
            ],
            "emojis": get_emojis_as_dict(),
            "permissions": {
                "public": bool(sketch.is_public),
                "read": bool(sketch.has_permission(current_user, "read")),
                "write": bool(sketch.has_permission(current_user, "write")),
                "delete": bool(sketch.has_permission(current_user, "delete")),
            },
            "collaborators": {
                "users": [user.username for user in sketch.collaborators],
                "groups": [group.name for group in sketch.groups],
            },
            "attributes": utils.get_sketch_attributes(sketch),
            "mappings": list(mappings),
            "indices_metadata": indices_metadata,
            "stats_per_timeline": stats_per_timeline,
            "last_activity": utils.get_sketch_last_activity(sketch),
            "sketch_labels": [label.label for label in sketch.labels],
            "filter_labels": (
                self.datastore.get_filter_labels(sketch.id, sketch_indices)
                if sketch_indices
                else []
            ),
        }
        return self.to_json(sketch, meta=meta)

    @login_required
    def delete(self, sketch_id: int, force_delete: bool = False):
        """Handles DELETE request to mark a sketch as deleted or permanently remove it.

        By default (force_delete=False), this method marks the sketch as 'deleted'
        in the database but does not remove the underlying OpenSearch indices or
        associated data. This is a soft delete, primarily for historical reasons
        and safety.

        If force_delete is set to True (either via the parameter or the 'force'
        URL query parameter), the sketch, its timelines, associated search indices,
        and all related data in the database and OpenSearch will be permanently
        removed. This is a hard delete and is irreversible.

        Deletion (both soft and hard) is prevented if the sketch has a label
        defined in the LABELS_TO_PREVENT_DELETION configuration setting.

        Requires 'delete' permission on the sketch and the
            user must be an administrator.

        Args:
            sketch_id (int): The ID of the sketch to delete.
            force_delete (bool): If True, performs a hard delete, permanently
                removing the sketch and all its associated data (timelines,
                search indices, etc.). Defaults to False (soft delete).
                Can also be triggered by setting the 'force' URL query parameter.

        Returns:
            int: HTTP_STATUS_CODE_OK (200) if the operation is successful (even
                 for a soft delete where data is only marked).

        Raises:
            HTTP_STATUS_CODE_NOT_FOUND (404): If no sketch is found with the
                given ID.
            HTTP_STATUS_CODE_FORBIDDEN (403): If the user does not have 'delete'
                permission on the sketch, or if the sketch has a label
                preventing deletion, or if the user is not an admin.
            HTTP_STATUS_CODE_BAD_REQUEST (400): If there's an issue during the
                deletion process e.g. the sketch being archived,
                or if timelines are still processing.
            HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR (500): If there's an unrecoverable
                error during OpenSearch index deletion.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "delete"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                ("User does not have sufficient access rights to delete a sketch."),
            )

        not_delete_labels = current_app.config.get("LABELS_TO_PREVENT_DELETION", [])
        for label in not_delete_labels:
            if sketch.has_label(label):
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    f"Sketch with the label [{label:s}] cannot be deleted.",
                )
        if sketch.get_status.status == "archived":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to delete a sketch that is already archived.",
            )

        if not force_delete:
            url_force_delete = request.args.get("force")
            if url_force_delete is not None:
                force_delete = True  # If the 'force' URL parameter exists, set to True
                logger.debug("Force delete detected from URL parameter.")
            else:
                logger.debug("Force delete not present, will keep the OS data.")

        # Check if user has admin privileges for force deletion
        if force_delete:
            if current_user.admin:
                logger.debug(
                    "User: %s is going to delete sketch %s", current_user, sketch_id
                )
            else:
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    "Sketch cannot be deleted. User is not an admin",
                )

        # Check if any timeline is still processing
        is_any_timeline_processing = any(
            t.get_status.status == "processing" for t in sketch.timelines
        )
        if is_any_timeline_processing:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Cannot delete sketch: one or more timelines are still processing.",
            )

        sketch.set_status(status="deleted")

        # Default behaviour for historical reasons: exit with 200 without
        # deleting
        if not force_delete:
            return HTTP_STATUS_CODE_OK

        # now the real deletion
        for timeline in sketch.timelines:
            timeline.set_status(status="deleted")
            searchindex = timeline.searchindex
            # remove the opensearch index
            index_name_to_delete = searchindex.index_name

            try:
                # Attempt to delete the OpenSearch index
                self.datastore.client.indices.delete(index=index_name_to_delete)
                logger.debug(
                    "User: %s is going to delete OS index %s",
                    current_user,
                    index_name_to_delete,
                )

                # Check if the index is really deleted
                if self.datastore.client.indices.exists(index=index_name_to_delete):
                    e_msg = (
                        f"Failed to delete OpenSearch index "
                        f"{index_name_to_delete}. Please check logs."
                    )
                    logger.error(e_msg)
                    abort(HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR, e_msg)
                else:
                    logger.debug(
                        "OpenSearch index %s successfully deleted.",
                        index_name_to_delete,
                    )

            except NotFoundError:
                # This can happen if the index was already deleted or never existed.
                e_msg = (
                    f"OpenSearch index {index_name_to_delete} was not found "
                    f"during deletion attempt. It might have been deleted "
                    f"already."
                )
                logger.warning(e_msg)
            except ConnectionError as e:
                e_msg = (
                    f"Connection error while trying to delete OpenSearch index "
                    f"{index_name_to_delete}:\n"
                    f"{e}"
                )
                logger.error(e_msg)
                abort(
                    HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                    e_msg,
                )
            except Exception as e:  # pylint: disable=broad-except
                # Catch any other unexpected errors during deletion
                e_msg = (
                    f"An unexpected error occurred while deleting "
                    f"OpenSearch index {index_name_to_delete}: {e}"
                )
                logger.error(e_msg)
                abort(
                    HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                    e_msg,
                )

            db_session.delete(searchindex)
            db_session.delete(timeline)

        db_session.delete(sketch)
        db_session.commit()
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
            msg = (
                "Label actions needs to be either 'add' or 'remove', "
                f"not [{label_action}]"
            )
            abort(HTTP_STATUS_CODE_BAD_REQUEST, msg)

        changed = False
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
