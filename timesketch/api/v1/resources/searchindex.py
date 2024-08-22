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
"""SearchIndex resources for version 1 of the Timesketch API."""
import logging

import opensearchpy
from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.lib import forms
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Timeline


logger = logging.getLogger("timesketch.index_api")


class SearchIndexListResource(resources.ResourceMixin, Resource):
    """Resource to get all search indices."""

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Returns:
            List of search indices in JSON (instance of flask.wrappers.Response)
        """
        indices = SearchIndex.all_with_acl(current_user).all()
        return self.to_json([i for i in indices if i.get_status.status != "deleted"])

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Returns:
            A search index in JSON (instance of flask.wrappers.Response)
        """
        form = forms.SearchIndexForm.build(request)
        searchindex_name = form.searchindex_name.data
        es_index_name = form.es_index_name.data
        public = form.public.data

        if not form.validate_on_submit():
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to validate form data")

        searchindex = SearchIndex.query.filter_by(index_name=es_index_name).first()
        metadata = {"created": True}

        if searchindex:
            metadata["created"] = False
            metadata["deleted"] = searchindex.get_status.status == "deleted"
            status_code = HTTP_STATUS_CODE_OK
        else:
            searchindex = SearchIndex.get_or_create(
                name=searchindex_name,
                description=searchindex_name,
                user=current_user,
                index_name=es_index_name,
            )
            searchindex.grant_permission(permission="read", user=current_user)
            searchindex.grant_permission(permission="write", user=current_user)
            searchindex.grant_permission(permission="delete", user=current_user)

            if public:
                searchindex.grant_permission(permission="read", user=None)

            datastore = self.datastore

            if not datastore.client.indices.exists(index=es_index_name):
                self.datastore.create_index(index_name=es_index_name)

            db_session.add(searchindex)
            db_session.commit()
            status_code = HTTP_STATUS_CODE_CREATED

        return self.to_json(searchindex, meta=metadata, status_code=status_code)


class SearchIndexResource(resources.ResourceMixin, Resource):
    """Resource to get search index."""

    @login_required
    def get(self, searchindex_id):
        """Handles GET request to the resource.

        Returns:
            Search index in JSON (instance of flask.wrappers.Response)
        """
        searchindex = SearchIndex.get_with_acl(searchindex_id)

        try:
            mapping = self.datastore.client.indices.get_mapping(searchindex.index_name)
        except opensearchpy.NotFoundError:
            logger.error("Unable to find index: {0:s}".format(searchindex.index_name))
            mapping = {}
            searchindex.set_status("fail")
            db_session.commit()

        fields = list(
            mapping.get(searchindex.index_name, {})
            .get("mappings", {})
            .get("properties", {})
            .keys()
        )

        meta = {
            "contains_timeline_id": bool("__ts_timeline_id" in fields),
            "fields": fields,
        }
        return self.to_json(searchindex, meta=meta)

    @login_required
    def post(self, searchindex_id):
        """Handles POST request to the resource.

        Returns:
            A search index in JSON (instance of flask.wrappers.Response)
        """
        form = request.json
        if not form:
            form = request.data

        if not searchindex_id:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Need to define a search index ID")

        searchindex = SearchIndex.get_with_acl(searchindex_id)
        if not searchindex:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No searchindex found with this ID.")

        if not searchindex.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                (
                    "User does not have sufficient access rights to "
                    "edit the search index."
                ),
            )

        if searchindex.get_status.status == "deleted":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Search index is marked deleted, unable to continue.",
            )

        commit_to_db = False
        new_status = form.get("status", "")
        valid_status = ("ready", "fail", "processing", "timeout")
        if new_status and new_status in valid_status:
            searchindex.set_status(status=new_status)
            commit_to_db = True

        description = form.get("description", "")
        if description:
            searchindex.description = description
            commit_to_db = True

        if commit_to_db:
            db_session.add(searchindex)
            db_session.commit()

        return self.to_json(searchindex)

    @login_required
    def delete(self, searchindex_id):
        """Handles DELETE request to the resource."""
        searchindex = SearchIndex.get_with_acl(searchindex_id)
        if not searchindex:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No searchindex found with this ID.")

        if not searchindex.has_permission(current_user, "delete"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                (
                    "User does not have sufficient access rights to "
                    "delete the search index."
                ),
            )

        if searchindex.get_status.status == "deleted":
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Search index already deleted.")

        timelines = Timeline.query.filter_by(searchindex=searchindex).all()
        sketches = [
            t.sketch
            for t in timelines
            if t.sketch and t.sketch.get_status.status != "deleted"
        ]

        if sketches:
            error_strings = ["WARNING: This timeline is in use by:"]
            for sketch in sketches:
                error_strings.append(" * {0:s}".format(sketch.name))
            abort(HTTP_STATUS_CODE_FORBIDDEN, "\n".join(error_strings))

        searchindex.set_status(status="deleted")
        # TODO: Actually implement to delete the index
        db_session.commit()

        other_indexes = SearchIndex.query.filter_by(
            index_name=searchindex.index_name
        ).all()
        if len(other_indexes) > 1:
            logger.warning(
                "Search index: {0:s} belongs to more than one "
                "db entry.".format(searchindex.index_name)
            )
            return HTTP_STATUS_CODE_OK

        try:
            self.datastore.client.indices.close(index=searchindex.index_name)
        except opensearchpy.NotFoundError:
            logger.warning(
                "Unable to close index: {0:s}, the index wasn't "
                "found.".format(searchindex.index_name)
            )

        return HTTP_STATUS_CODE_OK
