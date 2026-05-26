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
"""Explore resources for version 1 of the Timesketch API."""

import datetime
import io
import json
import logging
import zipfile

import prometheus_client

from flask import abort
from flask import jsonify
from flask import current_app
from flask import request
from flask import send_file
from flask_restful import Resource
from flask_restful import reqparse
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import export
from timesketch.api.v1 import resources
from timesketch.lib import forms
from timesketch.lib import utils
from timesketch.lib.utils import get_validated_indices
from timesketch.lib.definitions import DEFAULT_SOURCE_FIELDS
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_GATEWAY_TIMEOUT
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import METRICS_NAMESPACE
from timesketch.lib.errors import DatastoreTimeoutError
from timesketch.models import db_session
from timesketch.models.sketch import Event
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import View
from timesketch.models.sketch import SearchHistory
from timesketch.models.sketch import Scenario
from timesketch.models.sketch import Facet
from timesketch.models.sketch import InvestigativeQuestion

# Metrics definitions
METRICS = {
    "searchhistory": prometheus_client.Counter(
        "searchhistory",
        "Search History actions",
        ["action"],
        namespace=METRICS_NAMESPACE,
    )
}

logger = logging.getLogger("timesketch.explore_api")


class ExploreResource(resources.ResourceMixin, Resource):
    """Resource to search the datastore based on a query and a filter."""

    @login_required
    def post(self, sketch_id: int):
        """Handles POST request to the resource.
        Handler for /api/v1/sketches/:sketch_id/explore/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            JSON with list of matched events
        """
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
                HTTP_STATUS_CODE_BAD_REQUEST, "Unable to query on an archived sketch."
            )

        form = forms.ExploreForm.build(request)

        if not form.validate_on_submit():
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to explore data, unable to validate form data",
            )

        # DFIQ context
        scenario = None
        facet = None
        question = None

        scenario_id = request.json.get("scenario", None)
        facet_id = request.json.get("facet", None)
        question_id = request.json.get("question", None)

        if scenario_id:
            scenario = Scenario.get_by_id(scenario_id)
            if scenario:
                if scenario.sketch_id != sketch.id:
                    abort(
                        HTTP_STATUS_CODE_BAD_REQUEST,
                        "Scenario is not part of this sketch.",
                    )

        if facet_id:
            facet = Facet.get_by_id(facet_id)
            if facet:
                if facet.scenario.sketch_id != sketch.id:
                    abort(
                        HTTP_STATUS_CODE_BAD_REQUEST,
                        "Facet is not part of this sketch.",
                    )

        if question_id:
            question = InvestigativeQuestion.get_by_id(question_id)
            if question:
                if question.sketch_id != sketch.id:
                    abort(
                        HTTP_STATUS_CODE_BAD_REQUEST,
                        "Question is not part of this sketch.",
                    )

        # TODO: Remove form and use json instead.
        query_dsl = form.dsl.data
        enable_scroll = form.enable_scroll.data
        scroll_id = form.scroll_id.data
        file_name = form.file_name.data
        count = bool(form.count.data)

        query_filter = request.json.get("filter", {})
        parent = request.json.get("parent", None)
        incognito = request.json.get("incognito", False)

        include_processing_timelines = False
        if current_app.config.get("SEARCH_PROCESSING_TIMELINES", False):
            include_processing_timelines = request.json.get(
                "include_processing_timelines", False
            )

        return_field_string = form.fields.data
        if return_field_string:
            return_fields = [x.strip() for x in return_field_string.split(",")]
        else:
            return_fields = query_filter.get("fields", [])
            return_fields = [field["field"] for field in return_fields]
            return_fields.extend(DEFAULT_SOURCE_FIELDS)

        if not query_filter:
            query_filter = {}

        all_timeline_ids = [t.id for t in sketch.timelines]
        indices = query_filter.get("indices", all_timeline_ids)

        # If _all in indices then execute the query on all indices
        if "_all" in indices:
            indices = all_timeline_ids

        # Make sure that the indices in the filter are part of the sketch.
        # This will also remove any deleted timeline from the search result.
        indices, timeline_ids = get_validated_indices(
            indices, sketch, include_processing_timelines
        )

        # Remove indices that don't exist from search.
        indices = utils.validate_indices(indices, self.datastore)

        if not indices:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "No valid search indices were found to perform the search on.",
            )

        # Make sure we have a query string or star filter
        if not (
            form.query.data,
            query_filter.get("star"),
            query_filter.get("events"),
            query_dsl,
        ):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "The request needs a query string/DSL and or a star filter.",
            )

        # Aggregate hit count per index.
        index_stats_agg = {
            "indices": {
                "terms": {
                    "field": "_index",
                    "min_doc_count": 0,
                    "size": len(sketch.timelines),
                }
            },
            "timelines": {
                "terms": {
                    "field": "__ts_timeline_id",
                    "min_doc_count": 0,
                    "size": len(sketch.timelines),
                }
            },
            "count_over_time": {
                "auto_date_histogram": {
                    "field": "datetime",
                    "buckets": 50,
                }
            },
        }
        if count:
            # Count operations do not support size parameters.
            if "size" in query_filter:
                _ = query_filter.pop("size")
            if "terminate_after" in query_filter:
                _ = query_filter.pop("terminate_after")

            try:
                result = self.datastore.search(
                    sketch_id=sketch_id,
                    query_string=form.query.data,
                    query_filter=query_filter,
                    query_dsl=query_dsl,
                    indices=indices,
                    timeline_ids=timeline_ids,
                    count=True,
                )
            except DatastoreTimeoutError as e:
                abort(HTTP_STATUS_CODE_GATEWAY_TIMEOUT, str(e))
            except ValueError as e:
                abort(HTTP_STATUS_CODE_BAD_REQUEST, str(e))

            # Get number of matching documents per index.
            schema = {"meta": {"total_count": result}, "objects": []}
            return jsonify(schema)

        if file_name:
            file_object = io.BytesIO()

            form_data = {
                "created_at": datetime.datetime.utcnow().isoformat(),
                "created_by": current_user.username,
                "sketch": sketch_id,
                "query": form.query.data,
                "query_dsl": query_dsl,
                "query_filter": query_filter,
                "return_fields": return_fields,
            }
            with zipfile.ZipFile(file_object, mode="w") as zip_file:
                zip_file.writestr("METADATA", data=json.dumps(form_data))
                fh = export.query_to_filehandle(
                    query_string=form.query.data,
                    query_dsl=query_dsl,
                    query_filter=query_filter,
                    indices=indices,
                    sketch=sketch,
                    datastore=self.datastore,
                    return_fields=return_fields,
                    timeline_ids=timeline_ids,
                )
                fh.seek(0)
                zip_file.writestr("query_results.csv", fh.read())
            file_object.seek(0)
            return send_file(file_object, mimetype="zip", download_name=file_name)

        if scroll_id:
            # pylint: disable=unexpected-keyword-arg
            result = self.datastore.client.scroll(scroll_id=scroll_id, scroll="1m")
        else:
            try:
                result = self.datastore.search(
                    sketch_id=sketch_id,
                    query_string=form.query.data,
                    query_filter=query_filter,
                    query_dsl=query_dsl,
                    indices=indices,
                    aggregations=index_stats_agg,
                    return_fields=return_fields,
                    enable_scroll=enable_scroll,
                    timeline_ids=timeline_ids,
                )
            except DatastoreTimeoutError as e:
                abort(HTTP_STATUS_CODE_GATEWAY_TIMEOUT, str(e))
            except ValueError as e:
                abort(HTTP_STATUS_CODE_BAD_REQUEST, str(e))

        # Get number of matching documents over time.
        histogram_interval = (
            result.get("aggregations", {})
            .get("count_over_time", {})
            .get("interval", "")
        )
        count_over_time = {"data": {}, "interval": histogram_interval}
        try:
            for bucket in result["aggregations"]["count_over_time"]["buckets"]:
                key = bucket.get("key")
                if key:
                    count_over_time["data"][key] = bucket.get("doc_count")
        except KeyError:
            pass

        # Get number of matching documents per index.
        count_per_index = {}
        try:
            for bucket in result["aggregations"]["indices"]["buckets"]:
                key = bucket.get("key")
                if key:
                    count_per_index[key] = bucket.get("doc_count")
        except KeyError:
            pass

        # Get number of matching documents per timeline.
        count_per_timeline = {}
        try:
            for bucket in result["aggregations"]["timelines"]["buckets"]:
                key = bucket.get("key")
                if key:
                    count_per_timeline[key] = bucket.get("doc_count")
        except KeyError:
            pass

        # Total count for query regardless of returned results.
        count_total_complete = sum(count_per_index.values())

        comments = {}
        if "comment" in return_fields:
            try:
                events_with_comments = Event.get_with_comments(sketch=sketch)
                for event in events_with_comments:
                    for comment in event.comments:
                        comments.setdefault(event.document_id, [])
                        comments[event.document_id].append(comment.comment)
            except Exception as e:  # pylint: disable=broad-except
                logger.error(
                    "Failed to get comments for events in sketch ID [%s], "
                    "but explore will "
                    "proceed without them. Error: %s",
                    sketch_id,
                    e,
                    exc_info=True,
                )

        # Get labels for each event that matches the sketch.
        # Remove all other labels.
        for event in result["hits"]["hits"]:
            event["selected"] = False
            event["_source"]["label"] = []
            try:
                for label in event["_source"]["timesketch_label"]:
                    if sketch.id != label["sketch_id"]:
                        continue
                    event["_source"]["label"].append(label["name"])
                del event["_source"]["timesketch_label"]
            except KeyError:
                pass

        if "comment" in return_fields:
            comments = {}
            try:
                events_with_comments = Event.get_with_comments(sketch=sketch)
                for event in events_with_comments:
                    for comment in event.comments:
                        comments.setdefault(event.document_id, [])
                        comments[event.document_id].append(comment.comment)
            except Exception as e:  # pylint: disable=broad-except
                logger.error(
                    "Failed to get comments for events in sketch ID [%s], "
                    "but explore will "
                    "proceed without them. Error: %s",
                    sketch_id,
                    e,
                    exc_info=True,
                )

        for event in result["hits"]["hits"]:
            if "comment" in return_fields:
                event["_source"]["comment"] = comments.get(event["_id"], [])

        # Update or create user state view. This is used in the UI to let
        # the user get back to the last state in the explore view.
        # TODO: Deprecate this and change how last activity is determined, e.g
        # use the new Search History feature instead.
        view = View.get_or_create(user=current_user, sketch=sketch, name="")
        view.update_modification_time()
        view.query_string = form.query.data
        view.query_filter = json.dumps(query_filter, ensure_ascii=False)
        view.query_dsl = json.dumps(query_dsl, ensure_ascii=False)
        db_session.add(view)
        db_session.commit()

        # Search History
        search_node = None
        new_search = SearchHistory(user=current_user, sketch=sketch)

        if parent:
            previous_search = SearchHistory.get_by_id(parent)
        else:
            previous_search = (
                SearchHistory.query.filter_by(user=current_user, sketch=sketch)
                .order_by(SearchHistory.id.desc())
                .first()
            )

        if not incognito:
            is_same_query = False
            is_same_filter = False

            new_search.query_string = form.query.data
            new_search.query_filter = json.dumps(query_filter, ensure_ascii=False)

            new_search.query_result_count = count_total_complete
            new_search.query_time = result["took"]

            # Add DFIQ context
            new_search.scenario = scenario
            new_search.facet = facet
            new_search.investigativequestion = question

            if previous_search:
                new_search.parent = previous_search

                new_query = new_search.query_string
                new_filter = new_search.query_filter
                previous_query = previous_search.query_string
                previous_filter = previous_search.query_filter

                is_same_query = previous_query == new_query
                is_same_filter = previous_filter == new_filter

            if not all([is_same_query, is_same_filter]):
                db_session.add(new_search)
                db_session.commit()
                # Create metric if user creates a new branch.
                if new_search.parent:
                    if len(new_search.parent.children) > 1:
                        METRICS["searchhistory"].labels(action="branch").inc()
            else:
                METRICS["searchhistory"].labels(action="ignore_same_query").inc()
        else:
            METRICS["searchhistory"].labels(action="incognito").inc()

        search_node = new_search if new_search.id else previous_search

        if not search_node:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to save search")

        search_node = search_node.build_tree(search_node, {}, recurse=False)

        # Add metadata for the query result. This is used by the UI to
        # render the event correctly and to display timing and hit count
        # information.
        tl_colors = {}
        tl_names = {}
        for timeline in sketch.timelines:
            tl_colors[timeline.searchindex.index_name] = timeline.color
            tl_names[timeline.searchindex.index_name] = timeline.name

        meta = {
            "es_time": result["took"],
            "es_total_count": result["hits"]["total"],
            "es_total_count_complete": count_total_complete,
            "timeline_colors": tl_colors,
            "timeline_names": tl_names,
            "count_per_index": count_per_index,
            "count_per_timeline": count_per_timeline,
            "count_over_time": count_over_time,
            "scroll_id": result.get("_scroll_id", ""),
            "search_node": search_node,
        }

        # Elasticsearch version 7.x returns total hits as a dictionary.
        # TODO: Refactor when version 6.x has been deprecated.
        if isinstance(meta["es_total_count"], dict):
            meta["es_total_count"] = meta["es_total_count"].get("value", 0)

        schema = {"meta": meta, "objects": result["hits"]["hits"]}
        return jsonify(schema)


class QueryResource(resources.ResourceMixin, Resource):
    """Resource to get a query."""

    @login_required
    def post(self, sketch_id: int):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            A story in JSON (instance of flask.wrappers.Response)
        """
        form = forms.ExploreForm.build(request)
        if not form.validate_on_submit():
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to validate form data.")
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )
        schema = {"objects": [], "meta": {}}
        query_string = form.query.data
        query_filter = form.filter.data
        query_dsl = form.dsl.data
        query = self.datastore.build_query(
            sketch.id, query_string, query_filter, query_dsl
        )
        schema["objects"].append(query)
        return jsonify(schema)


class SearchHistoryResource(resources.ResourceMixin, Resource):
    """Resource to get search history for a user."""

    def __init__(self):
        super().__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument("limit", type=int, required=False, location="args")
        self.parser.add_argument("question", type=int, required=False, location="args")

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            Search history in JSON (instance of flask.wrappers.Response)
        """
        SQL_LIMIT = 100  # Limit to fetch first 100 results
        DEFAULT_LIMIT = 12

        # How many results to return (12 if nothing is specified)
        args = self.parser.parse_args()
        limit = args.get("limit")
        question_id = args.get("question")

        if not limit:
            limit = DEFAULT_LIMIT

        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        result = []

        if question_id:
            question = InvestigativeQuestion.get_by_id(question_id)
            if question.sketch.id != sketch.id:
                abort(
                    HTTP_STATUS_CODE_NOT_FOUND,
                    "No question found with this ID for this sketch.",
                )
            nodes = (
                SearchHistory.query.filter_by(
                    user=current_user, sketch=sketch, investigativequestion=question
                )
                .order_by(SearchHistory.id.desc())
                .limit(SQL_LIMIT)
                .all()
            )
        else:
            nodes = (
                SearchHistory.query.filter_by(user=current_user, sketch=sketch)
                .order_by(SearchHistory.id.desc())
                .limit(SQL_LIMIT)
                .all()
            )

        uniq_queries = set()
        count = 0
        for node in nodes:
            if node.query_string not in uniq_queries:
                if count >= int(limit):
                    break
                result.append(node.build_node_dict({}, node))
                uniq_queries.add(node.query_string)
                count += 1

        schema = {"objects": result, "meta": {}}

        return jsonify(schema)


class SearchHistoryTreeResource(resources.ResourceMixin, Resource):
    """Resource to get search history for a user."""

    HISTORY_NODE_LIMIT = 10  # To prevent heap exhaustion during recursion.

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            Search history in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        tree = {}

        # Get last history node for the current user and a specific sketch.
        last_node = (
            SearchHistory.query.filter_by(user=current_user, sketch=sketch)
            .order_by(SearchHistory.id.desc())
            .first()
        )

        # Traverse (in reverse) the history tree 10 steps from the last node in order to
        # not build an unesessary big graph.
        root_node = last_node
        for _ in range(self.HISTORY_NODE_LIMIT):
            if not root_node:
                break

            if not root_node.parent:
                break
            root_node = root_node.parent

        if root_node:
            tree = root_node.build_tree(root_node, {})

        schema = {
            "objects": [tree],
            "meta": {"last_node_id": last_node.id if last_node else None},
        }

        return jsonify(schema)


class ExploreWildcardResource(resources.ResourceMixin, Resource):
    """Explore resources for running wildcard queries on the datastore.

    This API endpoint allows exact-match wildcard searching on targeted document
    fields (e.g. message, xml_string), bypassing standard Lucene string query
    parser tokenization.
    """

    def _verify_wildcard_mappings(
        self, indices: list[str], fields_list: list[str]
    ) -> dict[str, str]:
        """Verifies that all targeted fields possess active wildcard mappings.

        Args:
            indices (list): List of active index names to search.
            fields_list (list): List of targeted user field names.

        Returns:
            dict: A mapping from target field name to the exact subfield path to
                query (e.g. {"message": "message.wildcard"}).

        Raises:
            ValueError: If a targeted field lacks a wildcard field type mapping.
        """
        try:
            # Retrieve complete mappings for all target timeline indices
            mappings = self.datastore.client.indices.get_mapping(index=indices)
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise ValueError(f"Unable to retrieve datastore mappings: {e}") from e

        field_paths = {}

        for target_field in fields_list:
            supported_in_all_indices = True
            exact_subfield_path = None

            for index_name in indices:
                # Safely navigate to properties tree
                properties = (
                    mappings.get(index_name, {})
                    .get("mappings", {})
                    .get("properties", {})
                )
                field_def = properties.get(target_field)
                if not field_def:
                    supported_in_all_indices = False
                    break

                # Case A: The field itself is of type 'wildcard'
                if field_def.get("type") == "wildcard":
                    exact_subfield_path = target_field
                    continue

                # Case B: Field has subfield of type 'wildcard' (standard suffix)
                subfields = field_def.get("fields", {})
                wildcard_subfield_key = None
                for key, sub_def in subfields.items():
                    if sub_def.get("type") == "wildcard":
                        wildcard_subfield_key = key
                        break

                if wildcard_subfield_key:
                    exact_subfield_path = f"{target_field}.{wildcard_subfield_key}"
                else:
                    supported_in_all_indices = False
                    break

            if not supported_in_all_indices or not exact_subfield_path:
                raise ValueError(
                    f"Field '{target_field}' does not support exact wildcard "
                    f"searches. Ensure it is mapped with a 'wildcard' field "
                    f"type suffix (e.g. '.wildcard')."
                )

            field_paths[target_field] = exact_subfield_path

        return field_paths

    @login_required
    def post(self, sketch_id: int):
        """Handles POST request to the resource.

        Handler for /api/v1/sketches/:sketch_id/explore_wildcard/

        Args:
            sketch_id: Integer primary key for a sketch database model.

        Input JSON parameters (request body):
            query (str): Raw wildcard search expression (e.g. '*evil_term*' or
                'message:*evil*').
            filter (dict): Optional dictionary representing search filters
                (e.g. size/limit).

        Returns:
            A Flask Response (JSON format) containing the skeleton search response,
            including an empty hits list.

        Raises:
            HTTPStatus.NOT_FOUND (404): If the sketch cannot be found.
            HTTPStatus.FORBIDDEN (403): If current user lacks read
                permissions on sketch.
            HTTPStatus.BAD_REQUEST (400): If the sketch is currently archived.
        """
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
                HTTP_STATUS_CODE_BAD_REQUEST, "Unable to query on an archived sketch."
            )

        # Resolve active search indices in the sketch
        all_timeline_ids = [t.id for t in sketch.timelines]
        indices, _ = get_validated_indices(all_timeline_ids, sketch)
        indices = utils.validate_indices(indices, self.datastore)
        if not indices:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "No active timelines with valid search indices found in this sketch.",
            )

        # TODO: In the actual search execution phase (Iteration 2), we must verify
        # that the target fields in these indices possess a specific '.wildcard'
        # subfield of type 'wildcard'. We want to work ONLY with the 'wildcard'
        # field type (not 'keyword' or standard 'text' types) to ensure high-performance
        # leading wildcard matching. If no suitable 'wildcard' type mappings are
        # present, we should raise a 400 Bad Request error.

        # TODO: In the actual search execution phase (Iteration 2), we should
        # define a custom forms.ExploreWildcardForm class. This sanitizes
        # parameters from dynamic JSON request injections, checks for safe query
        # string bounds (like minimum safe search terms lengths), and
        # standardizes format exceptions. For this first skeleton iteration, we
        # just accept the query and fields parameters but do not build the raw
        # OpenSearch search query yet.
        request_data = request.json or {}
        query_string = request_data.get("query", "").strip()
        if not query_string:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "A non-empty 'query' parameter is required.",
            )

        # Parse query prefix pattern (e.g. field_name:search_pattern)
        if ":" in query_string:
            field_prefix, search_pattern = query_string.split(":", 1)
            fields_list = [field_prefix.strip()]
            wildcard_query = search_pattern.strip()
        else:
            fields_list = ["message"]
            wildcard_query = query_string

        # Verify targeted fields possess active wildcard type mappings
        try:
            field_paths = self._verify_wildcard_mappings(indices, fields_list)
        except ValueError as e:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, str(e))

        logger.info(
            "ExploreWildcardResource: Sketch ID: %d, Query: %r, "
            "Extracted Fields: %r, Extracted Wildcard Query: %r, "
            "Resolved Paths: %r",
            sketch_id,
            query_string,
            fields_list,
            wildcard_query,
            field_paths,
        )

        # Extract limit parameter safely from filter settings
        limit = request_data.get("filter", {}).get("size")
        if limit is not None:
            try:
                limit = max(0, int(limit))
            except (ValueError, TypeError):
                limit = 40
        else:
            limit = 40

        # Construct raw OpenSearch search query payload targeting the .wildcard subfield
        query_dsl = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "bool": {
                                "should": [
                                    {
                                        "wildcard": {
                                            exact_path: {
                                                "value": wildcard_query,
                                                "case_insensitive": True,
                                            }
                                        }
                                    }
                                    for exact_path in field_paths.values()
                                ],
                                "minimum_should_match": 1,
                            }
                        }
                    ],
                    "filter": [],
                }
            },
            "size": min(limit, 10000) if limit is not None else 40,
            "sort": [{"datetime": {"order": "asc"}}],
        }

        # Execute search query payload against datastore OpenSearch client
        try:
            result = self.datastore.search(
                sketch_id=sketch_id,
                query_dsl=query_dsl,
                indices=indices,
            )
        except DatastoreTimeoutError as e:
            abort(HTTP_STATUS_CODE_GATEWAY_TIMEOUT, str(e))
        except ValueError as e:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, str(e))

        # Extract comparison flag
        compare = request_data.get("compare", False)
        comparison_data = None

        if compare:
            standard_ids = []
            standard_took = 0
            standard_total_hits = 0
            standard_error = None

            try:
                # Execute baseline standard inverted search
                standard_results = self.datastore.search(
                    sketch_id=sketch_id,
                    query_string=query_string,
                    indices=indices,
                    query_filter={"size": limit},
                )
                standard_ids = [hit["_id"] for hit in standard_results["hits"]["hits"]]
                standard_took = standard_results["took"]
                standard_total_hits = standard_results["hits"]["total"]
                if isinstance(standard_total_hits, dict):
                    standard_total_hits = standard_total_hits.get("value", 0)
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning("Comparison standard search execution failed: %s", e)
                standard_error = str(e)

            # Compute set-differencing arrays between event document collections
            wildcard_ids = [hit["_id"] for hit in result["hits"]["hits"]]
            only_in_wildcard = list(set(wildcard_ids) - set(standard_ids))
            only_in_standard = list(set(standard_ids) - set(wildcard_ids))

            wildcard_total_hits = result["hits"]["total"]
            if isinstance(wildcard_total_hits, dict):
                wildcard_total_hits = wildcard_total_hits.get("value", 0)

            comparison_data = {
                "standard_search": {
                    "took_ms": standard_took,
                    "total_hits": standard_total_hits,
                    "event_ids": standard_ids,
                    "error": standard_error,
                },
                "wildcard_search": {
                    "took_ms": result["took"],
                    "total_hits": wildcard_total_hits,
                    "event_ids": wildcard_ids,
                },
                "diff": {
                    "only_in_wildcard": only_in_wildcard,
                    "only_in_standard": only_in_standard,
                },
            }

        # Build timeline colors and names reference maps
        tl_colors = {}
        tl_names = {}
        for timeline in sketch.timelines:
            tl_colors[timeline.searchindex.index_name] = timeline.color
            tl_names[timeline.searchindex.index_name] = timeline.name

        # Parse timesketch labels for response hits
        for event in result["hits"]["hits"]:
            event["selected"] = False
            event["_source"]["label"] = []
            try:
                for label in event["_source"]["timesketch_label"]:
                    if sketch.id != label["sketch_id"]:
                        continue
                    event["_source"]["label"].append(label["name"])
                del event["_source"]["timesketch_label"]
            except KeyError:
                pass

        # Resolve total hits count
        es_total_count = result["hits"]["total"]
        if isinstance(es_total_count, dict):
            es_total_count = es_total_count.get("value", 0)

        # Return standard search JSON structure with real database results
        meta = {
            "fields_list": fields_list,
            "wildcard_query": wildcard_query,
            "field_paths": field_paths,
            "es_time": result["took"],
            "es_total_count": es_total_count,
            "es_total_count_complete": es_total_count,
            "timeline_colors": tl_colors,
            "timeline_names": tl_names,
            "count_per_index": {},
            "count_per_timeline": {},
            "count_over_time": {"data": {}, "interval": ""},
            "scroll_id": result.get("_scroll_id", ""),
            "search_node": None,
            "comparison": comparison_data,
        }
        schema = {"meta": meta, "objects": result["hits"]["hits"]}
        return jsonify(schema)
