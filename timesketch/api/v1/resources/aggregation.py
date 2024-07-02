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
"""Aggregation resources for version 1 of the Timesketch API."""

import json
import time

from opensearchpy.exceptions import NotFoundError

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import marshal
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.lib import forms
from timesketch.lib import utils as lib_utils
from timesketch.lib.aggregators import apex
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.aggregators import manager as aggregator_manager
from timesketch.models import db_session
from timesketch.models.sketch import Aggregation
from timesketch.models.sketch import AggregationGroup
from timesketch.models.sketch import Sketch


class AggregationResource(resources.ResourceMixin, Resource):
    """Resource to query for aggregated results."""

    @login_required
    def get(self, sketch_id, aggregation_id):  # pylint: disable=unused-argument
        """Handles GET request to the resource.

        Handler for /api/v1/sketches/:sketch_id/aggregation/:aggregation_id

        Args:
            sketch_id: Integer primary key for a sketch database model.
            aggregation_id: Integer primary key for an aggregation database
                model.

        Returns:
            JSON with aggregation results
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )
        aggregation = Aggregation.get_by_id(aggregation_id)

        # Check that the aggregation exists
        if not aggregation:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "The aggregation ID ({0:d}) does not exist.".format(aggregation_id),
            )
        # Check that this aggregation belongs to the sketch
        if aggregation.sketch_id != sketch.id:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "The sketch ID ({0:d}) does not match with the defined "
                "sketch in the aggregation ({1:d})".format(
                    aggregation.sketch_id, sketch.id
                ),
            )

        # If this is a user state view, check that it
        # belongs to the current_user
        if aggregation.name == "" and aggregation.user != current_user:
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                ("A user state view can only be viewed by the user it belongs to."),
            )

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(aggregation)

    @login_required
    # pylint: disable=unused-argument
    def post(self, sketch_id, aggregation_id):
        """Handles POST request to the resource.

        Handler for /api/v1/sketches/:sketch_id/aggregation/:aggregation_id

        Args:
            sketch_id: Integer primary key for a sketch database model
            aggregation_id: Integer primary key for an aggregation database
                model
        """
        form = request.json
        if not form:
            form = request.data

        if not form:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to validate form data.")

        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch.",
            )

        aggregation = Aggregation.get_by_id(aggregation_id)
        if not aggregation:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No aggregation found with this ID.")

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have write permission on the sketch.",
            )

        aggregation.name = form.get("name", "")
        aggregation.description = form.get("description", "")
        aggregation.agg_type = form.get("agg_type", aggregation.agg_type)
        aggregation.chart_type = form.get("chart_type", aggregation.chart_type)
        aggregation.user = current_user
        aggregation.sketch = sketch

        labels = form.get("labels", "")
        if labels:
            for label in json.loads(labels):
                if aggregation.has_label(label):
                    continue
                aggregation.add_label(label)

        if form.get("parameters"):
            aggregation.parameters = json.dumps(
                form.get("parameters"), ensure_ascii=False
            )

        if form.get("view_id"):
            aggregation.view = form.get("view_id")

        db_session.add(aggregation)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(aggregation, status_code=HTTP_STATUS_CODE_CREATED)

    @login_required
    def delete(self, sketch_id, aggregation_id):
        """Handles DELETE request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model.
            group_id: Integer primary key for an aggregation group database
                model.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        aggregation = Aggregation.get_by_id(aggregation_id)
        if not aggregation:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No aggregation found with this ID.")

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have write permission on the sketch.",
            )

        # Check that this aggregation belongs to the sketch
        if aggregation.sketch_id != sketch.id:
            msg = (
                "The sketch ID ({0:d}) does not match with the aggregation "
                "sketch ID ({1:d})".format(sketch.id, aggregation.sketch_id)
            )
            abort(HTTP_STATUS_CODE_FORBIDDEN, msg)

        db_session.delete(aggregation)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return HTTP_STATUS_CODE_OK


class AggregationInfoResource(resources.ResourceMixin, Resource):
    """Resource to get information about an aggregation class."""

    REMOVE_FIELDS = frozenset(["_shards", "hits", "timed_out", "took"])

    @staticmethod
    def _get_info(aggregator_name):
        """Returns a dict with information about an aggregation."""
        agg_class = aggregator_manager.AggregatorManager.get_aggregator(aggregator_name)

        field_lines = []
        for form_field in agg_class.FORM_FIELDS:
            field = {
                "name": form_field.get("name", "N/A"),
                "description": form_field.get("label", "N/A"),
            }
            field_lines.append(field)

        return {
            "name": agg_class.NAME,
            "display_name": agg_class.DISPLAY_NAME,
            "description": agg_class.DESCRIPTION,
            "fields": field_lines,
        }

    @login_required
    def get(self):
        """Handles GET request to the resource.

        Handler for /api/v1/aggregation/info/

        Returns:
            JSON with information about every aggregator.
        """
        agg_list = []
        for name, _ in aggregator_manager.AggregatorManager.get_aggregators():
            agg_list.append(self._get_info(name))
        return jsonify(agg_list)

    @login_required
    def post(self):
        """Handles POST request to the resource.

        Handler for /api/v1/aggregation/info/

        Returns:
            JSON with aggregation information for a single aggregator.
        """
        form = request.json
        if not form:
            form = request.data

        aggregator_name = form.get("aggregator")
        if not aggregator_name:
            return abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Not able to gather information about an aggregator, "
                "missing the aggregator name.",
            )

        return jsonify(self._get_info(aggregator_name))


class AggregationGroupResource(resources.ResourceMixin, Resource):
    """Resource for aggregation group requests."""

    @login_required
    def get(self, sketch_id, group_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model.
            group_id: Integer primary key for an aggregation group database
        """
        sketch = Sketch.get_with_acl(sketch_id)
        group = AggregationGroup.get_by_id(group_id)

        if not group:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No Group found with this ID.")

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(user=current_user, permission="read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have read permission on the sketch.",
            )

        # Check that this group belongs to the sketch
        if group.sketch_id != sketch.id:
            msg = (
                "The sketch ID ({0:d}) does not match with the aggregation "
                "group sketch ID ({1:d})".format(sketch.id, group.sketch_id)
            )
            abort(HTTP_STATUS_CODE_FORBIDDEN, msg)

        _, objects, meta = utils.run_aggregator_group(group, sketch_id=sketch.id)

        group_fields = self.fields_registry[group.__tablename__]
        group_dict = marshal(group, group_fields)
        group_dict["agg_ids"] = [a.id for a in group.aggregations]

        objects[0].update(group_dict)

        schema = {"meta": meta, "objects": objects}

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return jsonify(schema)

    @login_required
    def post(self, sketch_id, group_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model.
            group_id: Integer primary key for an aggregation group database
                model.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        group = AggregationGroup.get_by_id(group_id)
        if not group:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No Group found with this ID.")

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        # Check that this group belongs to the sketch
        if group.sketch_id != sketch.id:
            msg = (
                "The sketch ID ({0:d}) does not match with the aggregation "
                "group sketch ID ({1:d})".format(sketch.id, group.sketch_id)
            )
            abort(HTTP_STATUS_CODE_FORBIDDEN, msg)

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have write permission on the sketch.",
            )

        form = request.json
        if not form:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "No JSON data, unable to process request to create "
                "a new aggregation group.",
            )

        group.name = form.get("name", group.name)
        group.description = form.get("description", group.description)
        group.parameters = form.get("parameters", group.parameters)
        group.orientation = form.get("orientation", group.orientation)
        group.user = current_user
        group.sketch = sketch

        agg_ids = json.loads(form.get("aggregations", group.aggregations))
        aggregations = []

        for agg_id in agg_ids:
            aggregation = Aggregation.get_by_id(agg_id)
            if not aggregation:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "No aggregation found for ID: {0:d}".format(agg_id),
                )
            aggregations.append(aggregation)

        group.aggregations = aggregations

        db_session.add(group)
        db_session.commit()

        return self.to_json(group, status_code=HTTP_STATUS_CODE_CREATED)

    @login_required
    def delete(self, sketch_id, group_id):
        """Handles DELETE request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model.
            group_id: Integer primary key for an aggregation group database
                model.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        group = AggregationGroup.get_by_id(group_id)

        if not group:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No Group found with this ID.")

        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        # Check that this group belongs to the sketch
        if group.sketch_id != sketch.id:
            msg = (
                "The sketch ID ({0:d}) does not match with the aggregation "
                "group sketch ID ({1:d})".format(sketch.id, group.sketch_id)
            )
            abort(HTTP_STATUS_CODE_FORBIDDEN, msg)

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have write permission on the sketch.",
            )

        db_session.delete(group)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return HTTP_STATUS_CODE_OK


class AggregationExploreResource(resources.ResourceMixin, Resource):
    """Resource to send an aggregation request."""

    REMOVE_FIELDS = frozenset(["_shards", "hits", "timed_out", "took"])

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Handler for /api/v1/sketches/<int:sketch_id>/aggregation/explore/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            JSON with aggregation results
        """
        form = forms.AggregationExploreForm.build(request)
        if not form.validate_on_submit():
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Not able to run aggregation, unable to validate form data.",
            )

        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )

        if sketch.get_status.status == "archived":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Not able to run aggregation on an archived sketch.",
            )

        sketch_indices = {
            t.searchindex.index_name
            for t in sketch.timelines
            if t.get_status.status.lower() == "ready"
        }

        aggregation_dsl = form.aggregation_dsl.data
        aggregator_name = form.aggregator_name.data

        if aggregator_name:
            agg_class = aggregator_manager.AggregatorManager.get_aggregator(
                aggregator_name
            )
            if not agg_class:
                abort(
                    HTTP_STATUS_CODE_NOT_FOUND,
                    f"Aggregator {aggregator_name} not found",
                )

            if form.aggregator_parameters.data:
                aggregator_parameters = form.aggregator_parameters.data
                if not isinstance(aggregator_parameters, dict):
                    aggregator_parameters = json.loads(aggregator_parameters)
            else:
                aggregator_parameters = {}

            indices = aggregator_parameters.pop("index", sketch_indices)
            indices, timeline_ids = lib_utils.get_validated_indices(indices, sketch)

            if not (indices or timeline_ids):
                abort(HTTP_STATUS_CODE_BAD_REQUEST, "No indices to aggregate on")

            aggregator = agg_class(
                sketch_id=sketch_id, indices=indices, timeline_ids=timeline_ids
            )
            aggregator_description = aggregator.describe

            # legacy chart settings
            chart_type = aggregator_parameters.pop("supported_charts", None)

            time_before = time.time()
            try:
                result_obj = aggregator.run(**aggregator_parameters)
            except NotFoundError:
                abort(
                    HTTP_STATUS_CODE_NOT_FOUND,
                    "Attempting to run an aggregation on a non-existing "
                    "index, index: {0:s} and parameters: {1!s}".format(
                        ",".join(indices), aggregator_parameters
                    ),
                )
            except ValueError as exc:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Unable to run the aggregation, with error: {0!s}".format(exc),
                )
            time_after = time.time()

            buckets = result_obj.to_dict()
            buckets["buckets"] = buckets.pop("values")
            if "labels" in buckets:
                buckets["labels"] = buckets.pop("labels")
            if "chart_options" in buckets:
                buckets["chart_options"] = buckets.pop("chart_options")

            result = {"aggregation_result": {aggregator_name: buckets}}
            meta = {
                "method": "aggregator_run",
                "aggregator_class": (
                    "apex" if isinstance(aggregator, apex.ApexAggregation) else "legacy"
                ),
                "chart_type": chart_type,
                "name": aggregator_description.get("name"),
                "description": aggregator_description.get("description"),
                "es_time": time_after - time_before,
            }

            if chart_type:
                chart_color = aggregator_parameters.pop("chart_color", "")
                chart_title = aggregator_parameters.pop("chart_title", None)
                chart_spec = result_obj.to_chart(
                    chart_name=chart_type, chart_title=chart_title, color=chart_color
                )
                if chart_spec:
                    meta["vega_spec"] = chart_spec
                    if not chart_title:
                        chart_title = aggregator.chart_title
                    meta["vega_chart_title"] = chart_title

        elif aggregation_dsl:
            # pylint: disable=unexpected-keyword-arg
            result = self.datastore.client.search(
                index=",".join(sketch_indices), body=aggregation_dsl, size=0
            )

            meta = {
                "es_time": result.get("took", 0),
                "es_total_count": result.get("hits", {}).get("total", 0),
                "timed_out": result.get("timed_out", False),
                "method": "aggregator_query",
                "max_score": result.get("hits", {}).get("max_score", 0.0),
            }
        else:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "An aggregation DSL or a name for an aggregator name needs "
                "to be provided!",
            )

        result_keys = set(result.keys()) - self.REMOVE_FIELDS
        objects = [result[key] for key in result_keys]
        schema = {"meta": meta, "objects": objects}

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return jsonify(schema)


class AggregationListResource(resources.ResourceMixin, Resource):
    """Resource to query for a list of stored aggregation queries."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Handler for /api/v1/sketches/<int:sketch_id>/aggregation/

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
        aggregations = sketch.get_named_aggregations

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(aggregations)

    @staticmethod
    def create_aggregation_from_form(sketch, form):
        """Creates an aggregation from form data.

        Args:
            sketch: Instance of timesketch.models.sketch.Sketch
            form: Instance of timesketch.lib.forms.SaveAggregationForm

        Returns:
            An aggregation (instance of timesketch.models.sketch.Aggregation)
        """
        # Default to user supplied data
        name = form.get("name", "")
        description = form.get("description", "")
        agg_type = form.get("agg_type", "")
        parameter_data = form.get("parameters", {})
        parameters = json.dumps(parameter_data, ensure_ascii=False)
        chart_type = form.get("chart_type", "")
        view_id = form.get("view_id")

        # Create the aggregation in the database
        aggregation = Aggregation(
            name=name,
            description=description,
            agg_type=agg_type,
            parameters=parameters,
            chart_type=chart_type,
            user=current_user,
            sketch=sketch,
            view=view_id,
        )

        labels = form.get("labels", "")
        if labels:
            for label in json.loads(labels):
                if aggregation.has_label(label):
                    continue
                aggregation.add_label(label)

        db_session.add(aggregation)
        db_session.commit()

        return aggregation

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            An aggregation in JSON (instance of flask.wrappers.Response)
        """
        form = request.json
        if not form:
            form = request.data

        if not form:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to validate form data.")

        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have write permission on the sketch.",
            )

        aggregation = self.create_aggregation_from_form(sketch, form)

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(aggregation, status_code=HTTP_STATUS_CODE_CREATED)


class AggregationGroupListResource(resources.ResourceMixin, Resource):
    """Resource to query for a list of stored aggregation queries."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Handler for /api/v1/sketches/<int:sketch_id>/aggregation/group/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            Views in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(user=current_user, permission="read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have read permission on the sketch.",
            )
        groups = AggregationGroup.query.filter_by(sketch_id=sketch_id).all()
        meta = {
            "command": "list_groups",
        }
        objects = []
        for group in groups:
            group_dict = {
                "id": group.id,
                "name": group.name,
                "parameters": group.parameters,
                "orientation": group.orientation,
                "description": group.description,
                "agg_ids": json.dumps([x.id for x in group.aggregations]),
            }
            objects.append(group_dict)
        response = jsonify({"meta": meta, "objects": objects})
        response.status_code = HTTP_STATUS_CODE_OK

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return response

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            An aggregation in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(user=current_user, permission="write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "The user does not have write permission on the sketch.",
            )

        form = request.json
        if not form:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "No JSON data, unable to process request to create "
                "a new aggregation group.",
            )

        aggregation_string = form.get("aggregations", "")
        if not aggregation_string:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to create an empty group.")

        agg_list = json.loads(aggregation_string)
        if not isinstance(agg_list, (list, tuple)):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST, "Aggregations needs to be a list of IDs."
            )

        named_aggs = sketch.get_named_aggregations
        aggregations = [agg for agg in named_aggs if agg.id in agg_list]

        # Create the aggregation in the database
        aggregation_group = AggregationGroup(
            name=form.get("name", "No Group Name"),
            description=form.get("description", ""),
            parameters=form.get("parameters", ""),
            aggregations=aggregations,
            orientation=form.get("orientation", "layer"),
            user=current_user,
            sketch=sketch,
            view=form.get("view_id"),
        )
        db_session.add(aggregation_group)
        db_session.commit()

        # Update the last activity of a sketch.
        utils.update_sketch_last_activity(sketch)

        return self.to_json(aggregation_group, status_code=HTTP_STATUS_CODE_CREATED)
