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
"""Event resources for version 1 of the Timesketch API."""

import codecs
import datetime
import hashlib
import json
import logging
import math
import time
import six

import dateutil
from opensearchpy.exceptions import RequestError
import numpy as np
import pandas as pd

from flask import jsonify
from flask import request
from flask import abort
from flask_restful import Resource
from flask_restful import reqparse
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
from timesketch.models.sketch import Event
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline
from timesketch.models.sketch import SearchHistory


logger = logging.getLogger("timesketch.event_api")


def _tag_event(row, tag_dict, tags_to_add, datastore, flush_interval):
    """Tag each event from a dataframe with tags.

    Args:
        row (np.Series): a single row of data with existing tags and
            information about the event in order to be able to add
            tags to it.
        tag_dict (dict): a dict that contains information to be returned
            by the API call to the user.
        tags_to_add (list[str]): a list of strings of tags to add to each
            event.
        datastore (opensearch.OpenSearchDataStore): the datastore object.
        flush_interval (int): the number of events to import before a bulk
            update is done with the datastore.
    """
    tag_dict["events_processed_by_api"] += 1
    existing_tags = set()

    if "tag" in row:
        tag = row["tag"]
        if isinstance(tag, (list, tuple)):
            existing_tags = set(tag)

        new_tags = list(set().union(existing_tags, set(tags_to_add)))
    else:
        new_tags = tags_to_add

    if set(existing_tags) == set(new_tags):
        return

    datastore.import_event(
        index_name=row["_index"],
        event_id=row["_id"],
        event={"tag": new_tags},
        flush_interval=flush_interval,
    )

    tag_dict["tags_applied"] += len(new_tags)
    tag_dict["number_of_events_with_added_tags"] += 1


class EventCreateResource(resources.ResourceMixin, Resource):
    """Resource to create an annotation for an event."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.
        Handler for /api/v1/sketches/:sketch_id/event/create/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            An annotation in JSON (instance of flask.wrappers.Response)
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

        timeline_name = "Manual events"
        index_name_seed = "timesketch_{0:d}".format(sketch_id)

        date_string = form.get("date_string")
        if not date_string:
            date = datetime.datetime.utcnow().isoformat()
        else:
            # derive datetime from timestamp:
            try:
                date = dateutil.parser.parse(date_string)
            except (dateutil.parser.ParserError, OverflowError) as e:
                logger.error("Unable to convert date string", exc_info=True)
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Unable to add event, not able to convert the date "
                    "string. Was it properly formatted? Error: "
                    "{0!s}".format(e),
                )

        timestamp = int(time.mktime(date.utctimetuple())) * 1000000
        timestamp += date.microsecond

        event = {
            "datetime": date_string,
            "timestamp": timestamp,
            "timestamp_desc": form.get("timestamp_desc", "Event Happened"),
            "message": form.get("message", "No message string"),
        }

        attributes = form.get("attributes", {})
        if not isinstance(attributes, dict):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to add an event where the attributes are not a dict object.",
            )

        event.update(attributes)

        tag = form.get("tag", [])
        if not isinstance(tag, list):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to add an event where the tags are not a list of strings.",
            )

        if tag and any(not isinstance(x, str) for x in tag):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to add an event where the tags are not a list of strings.",
            )

        event["tag"] = tag

        # We do not need a human readable filename or
        # datastore index name, so we use UUIDs here.
        index_name = hashlib.md5(index_name_seed.encode()).hexdigest()
        if six.PY2:
            index_name = codecs.decode(index_name, "utf-8")

        # Try to create index
        timeline = None
        try:
            # Create the index in OpenSearch (unless it already exists)
            self.datastore.create_index(index_name=index_name)

            # Create the search index in the Timesketch database
            searchindex = SearchIndex.get_or_create(
                name=timeline_name,
                description="internal timeline for user-created events",
                user=current_user,
                index_name=index_name,
            )
            searchindex.grant_permission(permission="read", user=current_user)
            searchindex.grant_permission(permission="write", user=current_user)
            searchindex.grant_permission(permission="delete", user=current_user)
            searchindex.set_status("ready")
            db_session.add(searchindex)
            db_session.commit()

            if sketch and sketch.has_permission(current_user, "write"):
                self.datastore.import_event(index_name, event, flush_interval=1)

                timeline = Timeline.get_or_create(
                    name=searchindex.name,
                    description=searchindex.description,
                    sketch=sketch,
                    user=current_user,
                    searchindex=searchindex,
                )

                if timeline not in sketch.timelines:
                    sketch.timelines.append(timeline)

                timeline.set_status("ready")
                db_session.add(timeline)
                db_session.commit()

        # TODO: Can this be narrowed down, both in terms of the scope it
        # applies to, as well as not to catch a generic exception.
        except Exception as e:  # pylint: disable=broad-except
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Failed to add event ({0!s})".format(e),
            )

        # Return Timeline if it was created.
        # pylint: disable=no-else-return
        if timeline:
            return self.to_json(timeline, status_code=HTTP_STATUS_CODE_CREATED)

        return self.to_json(searchindex, status_code=HTTP_STATUS_CODE_CREATED)


class EventResource(resources.ResourceMixin, Resource):
    """Resource to get a single event from the datastore.

    HTTP Args:
        searchindex_id: The datastore searchindex id as string
        event_id: The datastore event id as string
    """

    def __init__(self):
        super().__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            "searchindex_id", type=six.text_type, required=True, location="args"
        )
        self.parser.add_argument(
            "event_id", type=six.text_type, required=True, location="args"
        )

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.
        Handler for /api/v1/sketches/:sketch_id/event/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            JSON of the datastore event
        """

        args = self.parser.parse_args()
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )

        searchindex_id = args.get("searchindex_id")
        searchindex = SearchIndex.query.filter_by(index_name=searchindex_id).first()
        if not searchindex:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Search index not found for this event.",
            )
        if searchindex.get_status.status == "deleted":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to query event on a closed search index.",
            )

        event_id = args.get("event_id")
        indices = [
            t.searchindex.index_name
            for t in sketch.timelines
            if t.get_status.status.lower() == "ready"
        ]

        # Check if the requested searchindex is part of the sketch
        if searchindex_id not in indices:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Search index ID ({0!s}) does not belong to the list "
                "of indices".format(searchindex_id),
            )

        result = self.datastore.get_event(searchindex_id, event_id)

        event = Event.query.filter_by(
            sketch=sketch, searchindex=searchindex, document_id=event_id
        ).first()

        # Comments for this event
        comments = []
        if event:
            for comment in event.comments:
                if not comment.user:
                    username = "System"
                else:
                    username = comment.user.username
                comment_dict = {
                    "id": comment.id,
                    "user": {
                        "username": username,
                    },
                    "created_at": comment.created_at,
                    "updated_at": comment.updated_at,
                    "comment": comment.comment,
                }
                comments.append(comment_dict)

        schema = {
            "meta": {"comments": sorted(comments, key=lambda d: d["created_at"])},
            "objects": result["_source"],
        }
        return jsonify(schema)


class EventAddAttributeResource(resources.ResourceMixin, Resource):
    """Resource to add attributes to events."""

    EVENT_FIELDS = ["_id", "_index", "attributes"]
    ATTRIBUTE_FIELDS = ["attr_name", "attr_value"]
    RESERVED_ATTRIBUTE_NAMES = [
        "datetime",
        "timestamp",
        "message",
        "timestamp_desc",
    ]

    MAX_EVENTS = 100000
    MAX_ATTRIBUTES = 10
    EVENT_CHUNK_SIZE = 1000

    def _parse_request(self, flask_request):
        """Validate and parse a POST request to add attributes.

        Args:
            flask_request (flask.Request): The unmodified request object.

        Returns:
            A dict with searchindex IDs as keys and the associated events as
                values.
        """
        if not flask_request.is_json:
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Request must be in JSON format.")
        events = flask_request.json.get("events")
        if not events:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Request must contain an events field.",
            )
        if not isinstance(events, list):
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Events field must be a list.")
        if len(events) > self.MAX_EVENTS:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                f"Request exceeds maximum events to process {self.MAX_EVENTS}",
            )

        events_by_index = {}
        for event in events:
            for field in self.EVENT_FIELDS:
                if field not in event:
                    abort(
                        HTTP_STATUS_CODE_BAD_REQUEST,
                        f"Event missing field {field}.",
                    )

            attributes = event.get("attributes")
            if not isinstance(attributes, list):
                abort(HTTP_STATUS_CODE_BAD_REQUEST, "Attributes must be a list.")
            if len(attributes) > self.MAX_ATTRIBUTES:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    f"Attributes for event exceeds maximum {self.MAX_ATTRIBUTES}",
                )
            for attribute in attributes:
                for field in self.ATTRIBUTE_FIELDS:
                    if field not in attribute:
                        abort(
                            HTTP_STATUS_CODE_BAD_REQUEST,
                            f"Attribute missing field {field}.",
                        )

            if event["_index"] not in events_by_index:
                events_by_index[event["_index"]] = []
            events_by_index[event["_index"]].append(event)

        return events_by_index

    @login_required
    def post(self, sketch_id):
        """Handles POST requests to the resource.

        Allows new attributes to be added to multiple events in one request.

        Args:
            sketch_id: Integer primary key for a sketch database model.

        Returns:
            A JSON instance of flask.wrappers.Response. Response metadata
                includes metrics on events modified, attributes added, chunks
                per index, number of errors and the last 10 errors.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")

        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                ("User does not have sufficient access rights to modify a sketch."),
            )

        datastore = self.datastore

        info_dict = {}
        info_dict["last_10_errors"] = []
        info_dict["events_modified"] = 0
        info_dict["attributes_added"] = 0

        events_by_index = self._parse_request(request)
        info_dict["chunks_per_index"] = {index: [] for index in list(events_by_index)}

        for index, events in events_by_index.items():
            chunks = []
            for i in range(0, len(events), self.EVENT_CHUNK_SIZE):
                chunks.append(events[i : i + self.EVENT_CHUNK_SIZE])
            info_dict["chunks_per_index"][index] = len(chunks)

            for chunk in chunks:
                should_list = [{"match": {"_id": event["_id"]}} for event in chunk]
                query_body = {"query": {"bool": {"should": should_list}}}
                # Adding a small buffer to make sure all results are captured.
                size = len(should_list) + 100
                query_body["size"] = size
                query_body["terminate_after"] = size

                # pylint: disable=unexpected-keyword-arg
                eventid_search = datastore.client.search(
                    body=json.dumps(query_body),
                    index=[index],
                    search_type="query_then_fetch",
                )
                # pylint: enable=unexpected-keyword-arg
                existing_events = eventid_search["hits"]["hits"]
                existing_events_dict = {
                    event["_id"]: event for event in existing_events
                }

                for request_event in chunk:
                    request_event_id = request_event["_id"]
                    if request_event_id not in existing_events_dict:
                        info_dict["errors"].append(
                            f"Event ID {request_event_id} not found."
                        )
                        continue

                    request_attributes = request_event["attributes"]
                    existing_attributes = existing_events_dict[request_event_id][
                        "_source"
                    ]
                    new_attributes = {}

                    for request_attribute in request_attributes:
                        request_attribute_name = request_attribute["attr_name"]
                        request_attribute_value = request_attribute["attr_value"]

                        if request_attribute_name in self.RESERVED_ATTRIBUTE_NAMES:
                            info_dict["last_10_errors"].append(
                                f"Cannot add '{request_attribute_name}' for "
                                f"event_id '{request_event_id}', name not "
                                f"allowed."
                            )
                        elif request_attribute_name.startswith("_"):
                            info_dict["last_10_errors"].append(
                                f"Attribute '{request_attribute_name}' for "
                                f"event_id '{request_event_id}' invalid, "
                                f"cannot start with '_'"
                            )
                        elif request_attribute_name in existing_attributes:
                            info_dict["last_10_errors"].append(
                                f"Attribute '{request_attribute_name}' already "
                                f"exists for event_id '{request_event_id}'."
                            )
                        else:
                            new_attributes[request_attribute_name] = (
                                request_attribute_value
                            )

                    if new_attributes:
                        datastore.import_event(
                            index_name=request_event["_index"],
                            event_id=request_event_id,
                            event=new_attributes,
                        )
                        info_dict["events_modified"] += 1
                        info_dict["attributes_added"] += len(new_attributes)

        datastore.flush_queued_events()
        info_dict["error_count"] = len(info_dict["last_10_errors"])
        # Only return last 10 errors to prevent overly large responses.
        info_dict["last_10_errors"] = info_dict["last_10_errors"][-10:]
        schema = {"meta": info_dict, "objects": []}
        response = jsonify(schema)
        response.status_code = HTTP_STATUS_CODE_OK
        return response


class EventTaggingResource(resources.ResourceMixin, Resource):
    """Resource to fetch and set tags to an event."""

    # The number of events to bulk together for each query.
    EVENT_CHUNK_SIZE = 1000

    # The maximum number of events to tag in a single request.
    MAX_EVENTS_TO_TAG = 100000

    # The size of the buffer before a bulk update in ES takes place.
    BUFFER_SIZE_FOR_ES_BULK_UPDATES = 10000

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            An annotation in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            msg = "No sketch found with this ID."
            abort(HTTP_STATUS_CODE_NOT_FOUND, msg)

        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                ("User does not have sufficient access rights to modify a sketch."),
            )

        form = request.json
        if not form:
            form = request.data

        tag_dict = {
            "events_processed_by_api": 0,
            "number_of_events_with_added_tags": 0,
            "tags_applied": 0,
        }
        datastore = self.datastore

        try:
            tags_to_add = json.loads(form.get("tag_string", ""))
        except json.JSONDecodeError as e:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to read the tags, with error: {0!s}".format(e),
            )

        if not isinstance(tags_to_add, list):
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Tags need to be a list")

        if not all(isinstance(x, str) for x in tags_to_add):
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Tags need to be a list of strings",
            )

        events = form.get("events", [])
        event_df = pd.DataFrame(events)

        for field in ["_id", "_index"]:
            if field not in event_df:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Events need to have a [{0:s}] field associated "
                    "to it.".format(field),
                )
            if any(event_df[field].isna()):
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "All events need to have a [{0:s}] field "
                    "set, it cannot have a non-value.".format(field),
                )

        # Remove any potential extra fields from the events.
        if "_type" in event_df:
            event_df = event_df[["_id", "_type", "_index"]]
        else:
            event_df = event_df[["_id", "_index"]]

        tag_df = pd.DataFrame()

        event_size = event_df.shape[0]
        if event_size > self.MAX_EVENTS_TO_TAG:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Cannot tag more than {0:d} events in a single "
                "request".format(self.MAX_EVENTS_TO_TAG),
            )

        tag_dict["number_of_events_passed_to_api"] = event_size

        errors = []

        verbose = form.get("verbose", False)
        if verbose:
            tag_dict["number_of_indices"] = len(event_df["_index"].unique())
            time_tag_gathering_start = time.time()

        for _index in event_df["_index"].unique():
            index_slice = event_df[event_df["_index"] == _index]
            index_size = index_slice.shape[0]

            if verbose:
                tag_dict.setdefault("index_count", {})
                tag_dict["index_count"][_index] = index_size

            if index_size <= self.EVENT_CHUNK_SIZE:
                chunks = 1
            else:
                chunks = math.ceil(index_size / self.EVENT_CHUNK_SIZE)

            tags = []
            for index_chunk in np.array_split(index_slice["_id"].unique(), chunks):
                should_list = [{"match": {"_id": x}} for x in index_chunk]
                query_body = {"query": {"bool": {"should": should_list}}}

                # Adding a small buffer to make sure all results are captured.
                size = len(should_list) + 100
                query_body["size"] = size
                query_body["terminate_after"] = size

                try:
                    # pylint: disable=unexpected-keyword-arg
                    if datastore.version.startswith("6"):
                        search = datastore.client.search(
                            body=json.dumps(query_body),
                            index=[_index],
                            _source_include=["tag"],
                            search_type="query_then_fetch",
                        )
                    else:
                        search = datastore.client.search(
                            body=json.dumps(query_body),
                            index=[_index],
                            _source_includes=["tag"],
                            search_type="query_then_fetch",
                        )

                except RequestError as e:
                    logger.error("Unable to query for events", exc_info=True)
                    errors.append("Unable to query for events, {0!s}".format(e))
                    abort(
                        HTTP_STATUS_CODE_BAD_REQUEST,
                        "Unable to query events, {0!s}".format(e),
                    )

                for result in search["hits"]["hits"]:
                    tag = result.get("_source", {}).get("tag", [])
                    if not tag:
                        continue
                    tags.append({"_id": result.get("_id"), "tag": tag})

            if not tags:
                continue
            tag_df = pd.concat([tag_df, pd.DataFrame(tags)])

        if tag_df.shape[0]:
            event_df = event_df.merge(tag_df, on="_id", how="left")

        if verbose:
            tag_dict["time_to_gather_tags"] = time.time() - time_tag_gathering_start
            tag_dict["number_of_events"] = len(events)

            if tag_df.shape[0]:
                tag_dict["number_of_events_in_tag_frame"] = tag_df.shape[0]

            if "tag" in event_df:
                current_tag_events = event_df[~event_df["tag"].isna()].shape[0]
                tag_dict["number_of_events_with_tags"] = current_tag_events
            else:
                tag_dict["number_of_events_with_tags"] = 0

            tag_dict["tags_to_add"] = tags_to_add
            time_tag_start = time.time()

        if event_size > datastore.DEFAULT_FLUSH_INTERVAL:
            flush_interval = self.BUFFER_SIZE_FOR_ES_BULK_UPDATES
        else:
            flush_interval = datastore.DEFAULT_FLUSH_INTERVAL
        _ = event_df.apply(
            _tag_event,
            axis=1,
            tag_dict=tag_dict,
            tags_to_add=tags_to_add,
            datastore=datastore,
            flush_interval=flush_interval,
        )
        datastore.flush_queued_events()

        if verbose:
            tag_dict["time_to_tag"] = time.time() - time_tag_start

        if errors:
            tag_dict["errors"] = errors

        schema = {"meta": tag_dict, "objects": []}
        response = jsonify(schema)
        response.status_code = HTTP_STATUS_CODE_OK
        return response


class EventAnnotationResource(resources.ResourceMixin, Resource):
    """Resource to create, update and delete an annotation for an event.

    HTTP Args (All optional. Used only for Delete request):
        searchindex_id: The datastore searchindex id as string
        event_id: The datastore event id as string
        annotation_type: The annotation type (comment,label) as string
        annotation_id: The annotation id as integer
        currentSearchNode_id: The search node id as string
    """

    def __init__(self):
        super().__init__()
        self.parser = reqparse.RequestParser()
        self.parser.add_argument(
            "searchindex_id", type=str, required=False, location="args"
        )
        self.parser.add_argument("event_id", type=str, required=False, location="args")
        self.parser.add_argument(
            "annotation_type", type=str, required=False, location="args"
        )
        self.parser.add_argument(
            "annotation_id", type=int, required=False, location="args"
        )
        self.parser.add_argument(
            "currentSearchNode_id", type=int, required=False, location="args"
        )

    def _get_sketch(self, sketch_id):
        """Helper function: Returns Sketch object givin a sketch id.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            Sketch object
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "write"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have write access controls on sketch.",
            )
        return sketch

    def _get_current_search_node(self, current_search_node_id, sketch):
        """Helper function: Returns Current Search Node object givin a search
            node id

        Args:
            current_search_node_id: search node id
                        sketch: Sketch object

        Returns:
            Search history object representing the current search node
        """
        current_search_node = SearchHistory.get_by_id(current_search_node_id)
        if not current_search_node:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "No search history found with this ID",
            )
        if not current_search_node.sketch == sketch:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Wrong sketch for this search history",
            )
        if not current_search_node.user == current_user:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Wrong user for this search history",
            )
        return current_search_node

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            An annotation in JSON (instance of flask.wrappers.Response)
        """
        form = forms.EventAnnotationForm.build(request)
        if not form.validate_on_submit():
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to validate form data.")

        annotations = []
        sketch = self._get_sketch(sketch_id)

        current_search_node = None
        _search_node_id = request.json.get("current_search_node_id", None)
        if _search_node_id:
            current_search_node = self._get_current_search_node(_search_node_id, sketch)

        indices = [
            t.searchindex.index_name
            for t in sketch.timelines
            if t.get_status.status.lower() == "ready"
        ]
        annotation_type = form.annotation_type.data
        events = form.events.raw_data

        for _event in events:
            searchindex_id = _event["_index"]
            searchindex = SearchIndex.query.filter_by(index_name=searchindex_id).first()
            event_id = _event["_id"]

            if searchindex_id not in indices:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Search index ID ({0!s}) does not belong to the list "
                    "of indices".format(searchindex_id),
                )

            # Get or create an event in the SQL database to have something
            # to attach the annotation to.
            event = Event.get_or_create(
                sketch=sketch, searchindex=searchindex, document_id=event_id
            )

            if current_search_node:
                current_search_node.events.append(event)

            # Add the annotation to the event object.
            if "comment" in annotation_type:
                annotation = Event.Comment(
                    comment=form.annotation.data, user=current_user
                )
                event.comments.append(annotation)
                self.datastore.set_label(
                    searchindex_id,
                    event_id,
                    sketch.id,
                    current_user.id,
                    "__ts_comment",
                    toggle=False,
                )
                if current_search_node:
                    current_search_node.add_label("__ts_comment")

            elif "label" in annotation_type:
                annotation = Event.Label.get_or_create(
                    label=form.annotation.data, user=current_user
                )
                if annotation not in event.labels:
                    event.labels.append(annotation)

                toggle = False
                if "__ts_star" in form.annotation.data:
                    toggle = True
                if "__ts_hidden" in form.annotation.data:
                    toggle = True
                if form.remove.data:
                    toggle = True

                self.datastore.set_label(
                    searchindex_id,
                    event_id,
                    sketch.id,
                    current_user.id,
                    form.annotation.data,
                    toggle=toggle,
                )

                if current_search_node:
                    search_node_label = "__ts_label"
                    if "__ts_star" in form.annotation.data:
                        search_node_label = "__ts_star"
                    current_search_node.add_label(search_node_label)
            else:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Annotation type needs to be either label or comment, "
                    "not {0!s}".format(annotation_type),
                )

            annotations.append(annotation)
            # Save the event to the database
            db_session.add(event)
            db_session.commit()

        return self.to_json(annotations, status_code=HTTP_STATUS_CODE_CREATED)

    @login_required
    def put(self, sketch_id):
        """Handles update request to annotations (currently only comments are
            supported).

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            The updated annotation object in JSON (instance of
            flask.wrappers.Response)
        """

        form = forms.EventAnnotationForm.build(request)
        if not form.validate_on_submit():
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Unable to validate form data.")

        updated_annotations = []
        sketch = self._get_sketch(sketch_id)

        indices = [
            t.searchindex.index_name
            for t in sketch.timelines
            if t.get_status.status.lower() == "ready"
        ]

        # Retrieving events list submitted in the request
        events = form.events.raw_data

        # Loop through all events supplied and update the annotation on each
        # event with the supplied annotation value.
        # Currently the UI does not support mass comments update, so typically
        # only one event will be in the event list
        for _event in events:
            searchindex_id = _event["_index"]
            searchindex = SearchIndex.query.filter_by(index_name=searchindex_id).first()
            event_id = _event["_id"]

            if searchindex_id not in indices:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Search index ID ({0!s}) does not belong to the list "
                    "of indices".format(searchindex_id),
                )

            # Retrieve the event from the SQL database based on the event_id
            # supplied in the request
            event = Event.query.filter_by(
                sketch=sketch, searchindex=searchindex, document_id=event_id
            ).first()

            if not event:
                abort(
                    HTTP_STATUS_CODE_NOT_FOUND,
                    "No event found with the id: " "{0!s}".format(event_id),
                )

            # Retrieve annotation type supplied in the request
            annotation_type = form.annotation_type.data
            # Retrieve the modified annotation supplied in the request
            annotation = form.annotation.data

            if "comment" in annotation_type:
                # Retrieve the comment attached to the event bases on the comment
                # id supplied in the request
                comment = event.get_comment(annotation["id"])
                if not comment:
                    abort(
                        HTTP_STATUS_CODE_NOT_FOUND,
                        "No comment found with "
                        "this id: {0!d}.".format(annotation["id"]),
                    )

                # Make sure the current user is the owner of the comment
                if comment.user != current_user:
                    abort(
                        HTTP_STATUS_CODE_FORBIDDEN,
                        "User is not owner of the comment.",
                    )

                # Update the comment with the new value
                annotation = event.update_comment(
                    annotation["id"], annotation["comment"]
                )

                if not annotation:
                    abort(
                        HTTP_STATUS_CODE_BAD_REQUEST,
                        "Update operation unsuccessful",
                    )

                updated_annotations.append(annotation)
            else:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Annotation type needs to be a comment, "
                    "not {0!s}".format(annotation_type),
                )

        return self.to_json(updated_annotations, status_code=HTTP_STATUS_CODE_OK)

    @login_required
    def delete(self, sketch_id):
        """Handles delete request of annotations (currently only comments are
            supported).

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            A HTTP 200 if the annotation was successfully deleted and HTTP 400
            otherwise
        """

        # Retrieve request arguments
        args = self.parser.parse_args()
        annotation_type = args.get("annotation_type")
        annotation_id = args.get("annotation_id")
        event_id = args.get("event_id")
        searchindex_id = args.get("searchindex_id")

        sketch = self._get_sketch(sketch_id)

        current_search_node = None
        _search_node_id = args.get("currentSearchNode_id")
        if _search_node_id:
            current_search_node = self._get_current_search_node(_search_node_id, sketch)
        searchindex = SearchIndex.query.filter_by(index_name=searchindex_id).first()

        # Retrieve the event from the SQL database based on the event_id
        # supplied in the request
        event = Event.query.filter_by(
            sketch=sketch, searchindex=searchindex, document_id=event_id
        ).first()

        if not event:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "No event found with the id: " "{0!s}".format(event_id),
            )

        if "comment" in annotation_type:
            # Retrieve the comment attached to the event bases on the comment
            # id supplied in the request
            comment = event.get_comment(annotation_id)
            if not comment:
                abort(
                    HTTP_STATUS_CODE_NOT_FOUND,
                    "No comment found with " "this id: {0!d}.".format(annotation_id),
                )

            # Make sure the current user is the owner of the comment
            if comment.user != current_user:
                abort(
                    HTTP_STATUS_CODE_FORBIDDEN,
                    "User is not owner of the comment.",
                )

            if event.remove_comment(annotation_id):
                # Remove label __ts_comment if the event has no more comments
                if len(event.comments) < 1:
                    self.datastore.set_label(
                        searchindex_id,
                        event_id,
                        sketch.id,
                        current_user.id,
                        "__ts_comment",
                        toggle=True,
                    )
                    if current_search_node:
                        current_search_node.remove_label("__ts_comment")

                return HTTP_STATUS_CODE_OK

        else:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Annotation type needs to be a comment, "
                "not {0!s}".format(annotation_type),
            )

        return (
            HTTP_STATUS_CODE_BAD_REQUEST,
            "Could not delete the annotation"
            " type {0!s} with the id {1!d}".format(annotation_type, annotation_id),
        )


class CountEventsResource(resources.ResourceMixin, Resource):
    """Resource to number of events for sketch timelines."""

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            Number of events in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID.")
        if not sketch.has_permission(current_user, "read"):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access controls on sketch.",
            )
        indices = [
            t.searchindex.index_name
            for t in sketch.active_timelines
            if t.get_status.status != "archived"
        ]
        count, bytes_on_disk = self.datastore.count(indices)
        meta = dict(count=count, bytes=bytes_on_disk)
        schema = dict(meta=meta, objects=[])
        return jsonify(schema)


class MarkEventsWithTimelineIdentifier(resources.ResourceMixin, Resource):
    """Resource to add a Timeline identifier to events within an index."""

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.
        Handler for /api/v1/sketches/:sketch_id/event/create/

        Args:
            sketch_id: Integer primary key for a sketch database model

        Returns:
            An annotation in JSON (instance of flask.wrappers.Response)
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

        searchindex_id = form.get("searchindex_id")
        searchindex_name = form.get("searchindex_name")

        if not (searchindex_id or searchindex_name):
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "No search index information supplied.",
            )

        searchindex = None
        if searchindex_name:
            searchindex = SearchIndex.query.filter_by(
                index_name=searchindex_name
            ).first()
        elif searchindex_id:
            searchindex = SearchIndex.get_by_id(searchindex_id)

        if not searchindex:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to find the Search index.",
            )

        if searchindex.get_status.status == "deleted":
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Unable to query event on a closed search index.",
            )

        timeline_id = form.get("timeline_id")
        if not timeline_id:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No timeline identifier supplied.")

        timeline = Timeline.get_by_id(timeline_id)
        if not timeline:
            abort(HTTP_STATUS_CODE_NOT_FOUND, "No Timeline found with this ID.")

        if timeline.sketch is None:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                f"The timeline {timeline_id} does not have an associated "
                "sketch, does it belong to a sketch?",
            )

        if timeline.sketch.id != sketch.id:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                "The sketch ID ({0:d}) does not match with the timeline "
                "sketch ID ({1:d})".format(sketch.id, timeline.sketch.id),
            )

        query_dsl = {
            "script": {
                "source": (
                    f"ctx._source.__ts_timeline_id={timeline_id};"
                    f"ctx._source.timesketch_label=[];"
                ),
                "lang": "painless",
            },
            "query": {
                "bool": {
                    "must_not": {
                        "exists": {
                            "field": "__ts_timeline_id",
                        }
                    }
                }
            },
        }
        # pylint: disable=unexpected-keyword-arg
        self.datastore.client.update_by_query(
            body=query_dsl,
            index=searchindex.index_name,
            conflicts="proceed",
            wait_for_completion=False,
        )

        # Update mappings - to make sure that we can label events.
        mapping_update = {
            "type": "nested",
            "properties": {
                "name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
                "sketch_id": {"type": "long"},
                "user_id": {"type": "long"},
            },
        }
        self.datastore.client.indices.put_mapping(
            body={"properties": {"timesketch_label": mapping_update}},
            index=searchindex.index_name,
        )

        return HTTP_STATUS_CODE_OK


class EventUnTagResource(resources.ResourceMixin, Resource):
    """Resource to add / remove a tag to an event."""

    # The maximum number of events to tag in a single request.
    MAX_EVENTS_TO_TAG = 500

    # The maximum number of tags in a single request.
    MAX_TAGS_PER_REQUEST = 500

    @login_required
    def post(self, sketch_id):
        """
        Remove tags (max 500) from a list of events (max 500).

        Args:
            sketch_id: Integer primary key for a sketch database model
            in request form:
                events: list of events to remove tags from with the following values:
                    _id: the event id (e.g. k8P1MYcBkeTGnypeeKJL)
                    _index: the searchindex name
                        (e.g. 56093e2566164c50bdf973643543571b)
                    searchindex_id: the searchindex id (e.g. 4) instead of
                        providing _index
                tags_to_remove: list of tags to remove from events


        Returns:
            HTTP_STATUS_CODE_OK if successful

        Raises:
            HTTP_STATUS_CODE_NOT_FOUND: if sketch or event does not exist
            HTTP_STATUS_CODE_BAD_REQUEST: if the request is malformed, e.g.
                events or tags are not lists or the number of events or tags
                exceeds the maximum allowed
            HTTP_STATUS_CODE_FORBIDDEN: if the user does not have write access
                to the sketch
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

        events = form.get("events", [])
        if not isinstance(events, list):
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Events need to be a list")

        if len(events) > self.MAX_EVENTS_TO_TAG:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Cannot untag more than {0:d} events in a single "
                "request".format(self.MAX_EVENTS_TO_TAG),
            )

        tags_to_remove = form.get("tags_to_remove", [])
        if not isinstance(tags_to_remove, list):
            abort(HTTP_STATUS_CODE_BAD_REQUEST, "Tags need to be a list")

        if len(tags_to_remove) > self.MAX_TAGS_PER_REQUEST:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "Cannot untag more than {0:d} tags in a single "
                "request".format(self.MAX_TAGS_PER_REQUEST),
            )

        datastore = self.datastore

        for _event in events:
            # every event entry can have a dedicated searchindex_id or searchindex_name
            searchindex_id = _event.get("searchindex_id", None)
            searchindex_name = _event.get("_index", None)

            if not (searchindex_id or searchindex_name):
                abort(
                    HTTP_STATUS_CODE_NOT_FOUND,
                    "No search index information supplied.",
                )

            searchindex = None
            # in both cases we are flexible, no matter what was supplied
            if searchindex_name:
                searchindex = SearchIndex.query.filter_by(
                    index_name=searchindex_name
                ).first()
            elif searchindex_id:
                searchindex = SearchIndex.get_by_id(searchindex_id)

            if not searchindex:
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Unable to find the Search index.",
                )

            if searchindex.get_status.status == "deleted":
                abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    "Unable to query event on a closed search index.",
                )

            result = self.datastore.get_event(searchindex.index_name, _event.get("_id"))
            if not result:
                logger.debug(
                    "Unable to find event %s in index %s to untag",
                    _event.get("_id"),
                    searchindex.index_name,
                )

            existing_tags = result.get("_source").get("tag", [])

            new_tags = list(set(existing_tags) - set(tags_to_remove))

            if existing_tags == new_tags:
                continue

            # write the new tags to the datastore
            datastore.import_event(
                index_name=searchindex.index_name,
                event_id=_event.get("_id"),
                event={"tag": new_tags},
                flush_interval=datastore.DEFAULT_FLUSH_INTERVAL,
            )

        datastore.flush_queued_events()

        return HTTP_STATUS_CODE_OK
