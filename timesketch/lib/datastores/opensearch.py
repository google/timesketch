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
"""OpenSearch datastore."""

from collections import Counter
import copy
import codecs
import json
import logging
import socket
import time
import queue
import threading
from uuid import uuid4
from typing import Generator, List, Dict, Optional, Any, Union

from dateutil import parser, relativedelta
from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionTimeout
from opensearchpy.exceptions import NotFoundError
from opensearchpy.exceptions import RequestError
from opensearchpy.exceptions import TransportError

# pylint: disable=redefined-builtin
from opensearchpy.exceptions import ConnectionError

from flask import abort
from flask import current_app
import prometheus_client

from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import METRICS_NAMESPACE
from timesketch.lib import errors


# Setup logging
os_logger = logging.getLogger("timesketch.opensearch")
os_logger.setLevel(logging.WARNING)

# Metrics definitions
METRICS = {
    "search_requests": prometheus_client.Counter(
        "search_requests",
        "Number of search requests per type (e.g all, stream etc)",
        ["type"],
        namespace=METRICS_NAMESPACE,
    ),
    "search_filter_type": prometheus_client.Counter(
        "search_filter_type",
        "Number of filters per type (e.g term, label etc)",
        ["type"],
        namespace=METRICS_NAMESPACE,
    ),
    "search_filter_label": prometheus_client.Counter(
        "search_filter_label",
        "Number of filters per label (e.g __ts_star etc)",
        ["label"],
        namespace=METRICS_NAMESPACE,
    ),
    "search_get_event": prometheus_client.Counter(
        "search_get_event",
        "Number of times a single event is requested",
        namespace=METRICS_NAMESPACE,
    ),
}

# OpenSearch scripts
UPDATE_LABEL_SCRIPT = """
if (ctx._source.timesketch_label == null) {
    ctx._source.timesketch_label = new ArrayList()
}
if (params.remove == true) {
    ctx._source.timesketch_label.removeIf(label -> label.name == params.timesketch_label.name && label.sketch_id == params.timesketch_label.sketch_id);
} else {
    if( ! ctx._source.timesketch_label.contains (params.timesketch_label)) {
        ctx._source.timesketch_label.add(params.timesketch_label)
    }
}
"""

TOGGLE_LABEL_SCRIPT = """
if (ctx._source.timesketch_label == null) {
    ctx._source.timesketch_label = new ArrayList()
}
boolean removedLabel = ctx._source.timesketch_label.removeIf(label -> label.name == params.timesketch_label.name && label.sketch_id == params.timesketch_label.sketch_id);
if (!removedLabel) {
    ctx._source.timesketch_label.add(params.timesketch_label)
}
"""

# Default sort order for PIT exports if not specified, ensuring stable pagination.
# _doc is generally recommended for performance with slicing.
_DEFAULT_PIT_SORT_CRITERIA = [{"_id": "asc"}]


class OpenSearchDataStore:
    """Implements the datastore."""

    DEFAULT_SIZE = 100
    DEFAULT_FLUSH_INTERVAL = 1000
    DEFAULT_LIMIT = DEFAULT_SIZE  # Max events to return
    DEFAULT_FROM = 0
    DEFAULT_STREAM_LIMIT = 5000  # Max events to return when streaming results

    DEFAULT_FLUSH_RETRY_LIMIT = 3  # Max retries for flushing the queue.
    DEFAULT_EVENT_IMPORT_TIMEOUT = 180  # Timeout value in seconds for importing events.

    DEFAULT_INDEX_WAIT_TIMEOUT = 10  # Seconds to wait for an index to become ready
    DEFAULT_MINIMUM_HEALTH = (
        "yellow"  # Minimum health status required ('yellow' or 'green')
    )

    def __init__(self, host="127.0.0.1", port=9200, **kwargs):
        """Create a OpenSearch client."""
        super().__init__()
        self._error_container = {}

        self.user = current_app.config.get("OPENSEARCH_USER", "user")
        self.password = current_app.config.get("OPENSEARCH_PASSWORD", "pass")
        self.ssl = current_app.config.get("OPENSEARCH_SSL", False)
        self.verify = current_app.config.get("OPENSEARCH_VERIFY_CERTS", True)
        self.timeout = current_app.config.get("OPENSEARCH_TIMEOUT", 10)

        parameters = {}
        if self.ssl:
            parameters["use_ssl"] = self.ssl
            parameters["verify_certs"] = self.verify

        if self.user and self.password:
            parameters["http_auth"] = (self.user, self.password)
        if self.timeout:
            parameters["timeout"] = self.timeout

        # Add and overwrite parameters provided by the initialization caller.
        parameters.update(kwargs)

        self.client = OpenSearch([{"host": host, "port": port}], **parameters)

        # Number of events to queue up when bulk inserting events.
        self.flush_interval = current_app.config.get(
            "OPENSEARCH_FLUSH_INTERVAL", self.DEFAULT_FLUSH_INTERVAL
        )
        self.import_counter = Counter()
        self.import_events = []
        self.version = self.client.info().get("version").get("number")
        self._request_timeout = current_app.config.get(
            "TIMEOUT_FOR_EVENT_IMPORT", self.DEFAULT_EVENT_IMPORT_TIMEOUT
        )
        self.index_timeout = current_app.config.get(
            "OPENSEARCH_INDEX_TIMEOUT", self.DEFAULT_INDEX_WAIT_TIMEOUT
        )
        self.min_health = current_app.config.get(
            "OPENSEARCH_MINIMUM_HEALTH", self.DEFAULT_MINIMUM_HEALTH
        )

    def _wait_for_index(
        self, index_name: str, timeout_seconds: Optional[int] = None
    ) -> bool:
        """Waits for a specific index to reach at least yellow status.

        Args:
            index_name: The name of the index to wait for.
            timeout_seconds: How long to wait in seconds. Defaults to config setting.

        Returns:
            True if the index became ready within the timeout, False otherwise.
        """
        if timeout_seconds is None:
            timeout_seconds = self.index_timeout

        os_logger.debug(
            "Waiting up to %ds for index '%s' to reach status '%s'...",
            timeout_seconds,
            index_name,
            self.min_health,
        )

        try:
            # wait_for_status will block until the status is met or timeout occurs.
            # pylint: disable=unexpected-keyword-arg
            self.client.cluster.health(
                index=index_name,
                wait_for_status=self.min_health,
                timeout=timeout_seconds,
                level="indices",
            )
            os_logger.debug("Index '%s' is ready.", index_name)
            return True
        except ConnectionTimeout:
            os_logger.error(
                "Timeout (%ds) waiting for index '%s' to reach status '%s'.",
                timeout_seconds,
                index_name,
                self.min_health,
                exc_info=False,  # Keep log cleaner on expected timeouts
            )
            return False
        except NotFoundError:
            os_logger.error(
                "Index '%s' not found while waiting for readiness.", index_name
            )
            return False
        except TransportError as e:
            # Handle other potential transport errors during the health check
            os_logger.error(
                "Error checking health for index '%s': %s",
                index_name,
                str(e),
                exc_info=True,
            )
            return False
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Catch unexpected errors
            os_logger.error(
                "Unexpected error waiting for index '%s': %s",
                index_name,
                str(e),
                exc_info=True,
            )
            return False

    @staticmethod
    def _build_labels_query(sketch_id: int, labels: list):
        """Build OpenSearch query for Timesketch labels.

        Args:
            sketch_id: Integer of sketch primary key.
            labels: List of label names.

        Returns:
            OpenSearch query as a dictionary.
        """
        label_query = {"bool": {"must": []}}

        for label in labels:
            # Increase metrics counter per label
            METRICS["search_filter_label"].labels(label=label).inc()
            nested_query = {
                "nested": {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"timesketch_label.name.keyword": label}},
                                {"term": {"timesketch_label.sketch_id": sketch_id}},
                            ]
                        }
                    },
                    "path": "timesketch_label",
                }
            }
            label_query["bool"]["must"].append(nested_query)
        return label_query

    @staticmethod
    def _build_events_query(events):
        """Build OpenSearch query for one or more document ids.

        Args:
            events: List of OpenSearch document IDs.

        Returns:
            OpenSearch query as a dictionary.
        """
        events_list = [event["event_id"] for event in events]
        query_dict = {"query": {"ids": {"values": events_list}}}
        return query_dict

    @staticmethod
    def _build_query_dsl(query_dsl: dict, timeline_ids: Union[int, list, None]):
        """Build OpenSearch Search DSL query by adding in timeline filtering.

        Args:
            query_dsl: A dict with the current query_dsl
            timeline_ids: Either a list of timeline IDs (int) or None.

        Returns:
            OpenSearch query DSL as a dictionary.
        """
        if not timeline_ids:
            return query_dsl

        if not isinstance(timeline_ids, (list, tuple)):
            os_logger.error(
                "Attempting to pass in timelines to a query DSL, but the "
                "passed timelines are not a list."
            )
            return query_dsl

        if not all(isinstance(x, int) for x in timeline_ids):
            os_logger.error("All timeline IDs need to be an integer.")
            return query_dsl

        old_query = query_dsl.get("query")
        if not old_query:
            return query_dsl

        query_dsl["query"] = {
            "bool": {
                "must": [],
                "should": [
                    {
                        "bool": {
                            "must": old_query,
                            "must_not": [
                                {
                                    "exists": {"field": "__ts_timeline_id"},
                                }
                            ],
                        }
                    },
                    {
                        "bool": {
                            "must": [
                                {"terms": {"__ts_timeline_id": timeline_ids}},
                                old_query,
                            ],
                            "must_not": [],
                            "filter": [{"exists": {"field": "__ts_timeline_id"}}],
                        }
                    },
                ],
                "must_not": [],
                "filter": [],
            }
        }
        return query_dsl

    @staticmethod
    def _convert_to_time_range(interval: str):
        """Convert an interval timestamp into start and end dates.

        Args:
            interval: Time frame representation

        Returns:
            Start timestamp in string format.
            End timestamp in string format.
        """
        # return ('2018-12-05T00:00:00', '2018-12-05T23:59:59')
        TS_FORMAT = "%Y-%m-%dT%H:%M:%S"
        get_digits = lambda s: int(  # pylint: disable=unnecessary-lambda-assignment
            "".join(filter(str.isdigit, s))
        )
        get_alpha = lambda s: "".join(  # pylint: disable=unnecessary-lambda-assignment
            filter(str.isalpha, s)
        )

        ts_parts = interval.split(" ")
        # The start date could be 1 or 2 first items
        start = " ".join(ts_parts[0 : len(ts_parts) - 2])
        minus = get_digits(ts_parts[-2])
        plus = get_digits(ts_parts[-1])
        interval = get_alpha(ts_parts[-1])

        start_ts = parser.parse(start)

        rd = relativedelta.relativedelta
        if interval == "s":
            start_range = start_ts - rd(seconds=minus)
            end_range = start_ts + rd(seconds=plus)
        elif interval == "m":
            start_range = start_ts - rd(minutes=minus)
            end_range = start_ts + rd(minutes=plus)
        elif interval == "h":
            start_range = start_ts - rd(hours=minus)
            end_range = start_ts + rd(hours=plus)
        elif interval == "d":
            start_range = start_ts - rd(days=minus)
            end_range = start_ts + rd(days=plus)
        else:
            raise RuntimeError("Unable to parse the timestamp: " + str(interval))

        return start_range.strftime(TS_FORMAT), end_range.strftime(TS_FORMAT)

    def build_query(
        self,
        sketch_id: int,
        query_string: str,
        query_filter: Dict,
        query_dsl: Optional[Dict] = None,
        aggregations: Optional[Dict] = None,
        timeline_ids: Optional[list] = None,
    ):
        """Build OpenSearch DSL query.

        Args:
            sketch_id: Integer of sketch primary key
            query_string: Query string
            query_filter: Dictionary containing filters to apply
            query_dsl: Dictionary containing OpenSearch DSL query
            aggregations: Dict of OpenSearch aggregations
            timeline_ids: Optional list of IDs of Timeline objects that should
                be queried as part of the search.

        Returns:
            OpenSearch DSL query as a dictionary
        """

        if query_dsl:
            if not isinstance(query_dsl, dict):
                query_dsl = json.loads(query_dsl)

            if not query_dsl:
                query_dsl = {}

            if query_filter:
                # Pagination
                if query_filter.get("from", None):
                    query_dsl["from"] = query_filter["from"]

                # Number of events to return
                if query_filter.get("size", None):
                    query_dsl["size"] = query_filter["size"]

            if aggregations:
                # post_filter happens after aggregation so we need to move the
                # filter to the query instead.
                if query_dsl.get("post_filter", None):
                    query_dsl["query"]["bool"]["filter"] = query_dsl["post_filter"]
                    query_dsl.pop("post_filter", None)
                query_dsl["aggregations"] = aggregations

            # Make sure we are sorting.
            if not query_dsl.get("sort", None):
                query_dsl["sort"] = {"datetime": query_filter.get("order", "asc")}

            return self._build_query_dsl(query_dsl, timeline_ids)

        if query_filter.get("events", None):
            events = query_filter["events"]
            return self._build_events_query(events)

        query_dsl = {"query": {"bool": {"must": [], "must_not": [], "filter": []}}}

        special_char_query = None
        if query_string:
            query_parts = query_string.split(":", 1)
            if len(query_parts) == 2:
                field_name, query_value = query_parts

                # Special Character Check
                if set(query_value) <= set('.+-=_&|><!(){}[]^"~?:\\/'):
                    # Construct the term query directly using the .keyword
                    special_char_query = {
                        "term": {f"{field_name}.keyword": query_value}
                    }
                    query_string = ""

        if query_string:
            query_dsl["query"]["bool"]["must"].append(
                {"query_string": {"query": query_string, "default_operator": "AND"}}
            )

        if special_char_query:
            query_dsl["query"]["bool"]["must"].append(special_char_query)

        # New UI filters
        if query_filter.get("chips", None):
            labels = []
            must_filters = query_dsl["query"]["bool"]["must"]
            must_not_filters = query_dsl["query"]["bool"]["must_not"]
            datetime_ranges = {"bool": {"should": [], "minimum_should_match": 1}}

            for chip in query_filter["chips"]:
                # Exclude chips that the user disabled
                if not chip.get("active", True):
                    continue

                # Increase metrics per chip type
                METRICS["search_filter_type"].labels(type=chip["type"]).inc()
                if chip["type"] == "label":
                    labels.append(chip["value"])

                elif chip["type"] == "term":
                    if isinstance(chip["value"], str):
                        term_filter = {
                            "match_phrase": {
                                "{}.keyword".format(chip["field"]): {
                                    "query": "{}".format(chip["value"])
                                }
                            }
                        }
                    else:
                        term_filter = {
                            "match_phrase": {
                                "{}".format(chip["field"]): {
                                    "query": "{}".format(chip["value"])
                                }
                            }
                        }

                    if chip["operator"] == "must":
                        must_filters.append(term_filter)

                    elif chip["operator"] == "must_not":
                        must_not_filters.append(term_filter)

                elif chip["type"].startswith("datetime"):
                    range_filter = lambda start, end: {  # pylint: disable=unnecessary-lambda-assignment
                        "range": {"datetime": {"gte": start, "lte": end}}
                    }
                    if chip["type"] == "datetime_range":
                        start, end = chip["value"].split(",")
                    elif chip["type"] == "datetime_interval":
                        start, end = self._convert_to_time_range(chip["value"])
                    else:
                        continue
                    datetime_ranges["bool"]["should"].append(range_filter(start, end))

            label_filter = self._build_labels_query(sketch_id, labels)
            must_filters.append(label_filter)
            must_filters.append(datetime_ranges)

        # Pagination
        if query_filter.get("from", None):
            query_dsl["from"] = query_filter["from"]

        # Number of events to return
        if query_filter.get("size", None):
            query_dsl["size"] = query_filter["size"]

        # Make sure we are sorting.
        if not query_dsl.get("sort", None):
            query_dsl["sort"] = {"datetime": query_filter.get("order", "asc")}

        # Add any pre defined aggregations
        if aggregations:
            # post_filter happens after aggregation so we need to move the
            # filter to the query instead.
            if query_dsl.get("post_filter", None):
                query_dsl["query"]["bool"]["filter"] = query_dsl["post_filter"]
                query_dsl.pop("post_filter", None)
            query_dsl["aggregations"] = aggregations

        # TODO: Simplify this when we don't have to support both timelines
        # that have __ts_timeline_id set and those that don't.
        # (query_string AND timeline_id NOT EXISTS) OR (
        #       query_string AND timeline_id in LIST)
        if timeline_ids and isinstance(timeline_ids, (list, tuple)):
            must_filters_pre = copy.copy(query_dsl["query"]["bool"]["must"])
            must_not_filters_pre = copy.copy(query_dsl["query"]["bool"]["must_not"])

            must_filters_post = copy.copy(query_dsl["query"]["bool"]["must"])
            must_not_filters_post = copy.copy(query_dsl["query"]["bool"]["must_not"])

            must_not_filters_pre.append(
                {
                    "exists": {"field": "__ts_timeline_id"},
                }
            )

            must_filters_post.append({"terms": {"__ts_timeline_id": timeline_ids}})

            query_dsl["query"] = {
                "bool": {
                    "must": [],
                    "should": [
                        {
                            "bool": {
                                "must": must_filters_pre,
                                "must_not": must_not_filters_pre,
                            }
                        },
                        {
                            "bool": {
                                "must": must_filters_post,
                                "must_not": must_not_filters_post,
                                "filter": [{"exists": {"field": "__ts_timeline_id"}}],
                            }
                        },
                    ],
                    "must_not": [],
                    "filter": [],
                }
            }

        return query_dsl

    # pylint: disable=too-many-arguments
    def search(
        self,
        sketch_id: int,
        indices: list,
        query_string: str = "",
        query_filter: Optional[Dict] = None,
        count: bool = False,
        query_dsl: Optional[Dict] = None,
        aggregations: Optional[Dict] = None,
        return_fields: Optional[list] = None,
        enable_scroll: bool = False,
        timeline_ids: Optional[list] = None,
    ) -> Union[Dict, int]:
        """Executes a search query against OpenSearch indices.

        This method constructs and sends a search request to OpenSearch based
        on the provided query string, filters, and optional DSL. It handles
        different search scenarios, including counting results, fetching specific
        fields, and enabling scrolling for large result sets.

        Args:
            sketch_id: The ID of the sketch the search is performed within. Used
                for building label filters.
            indices: A list of OpenSearch index names to query.
            query_string: The query string to search for (e.g., "hostname:evil.com").
                Defaults to an empty string.
            query_filter: An optional dictionary containing filters to apply to
                the search results. Common keys include 'from' (pagination start),
                'size' (number of results), 'events' (list of specific event IDs),
                and 'chips' (list of UI filter chips). Defaults to None.
            count: If True, only return the total number of documents matching
                the query instead of the documents themselves. Defaults to False.
            query_dsl: An optional dictionary representing the full OpenSearch
                Search DSL query body. If provided, this overrides the
                `query_string` and `query_filter` for the main query part,
                but `query_filter` is still used for pagination/size. Defaults to None.
            aggregations: An optional dictionary containing OpenSearch aggregation
                definitions to include in the search request. Defaults to None.
            return_fields: An optional list of fields to include in the returned
                documents. If None, all fields are returned. Defaults to None.
            enable_scroll: If True, enables the OpenSearch scroll API for
                retrieving large result sets. Defaults to False.
            timeline_ids: Optional list of IDs of Timeline objects that should
                be queried as part of the search.

        Returns:
            A dictionary containing the raw response from the OpenSearch search
            API. The structure typically includes 'hits' (containing 'hits' list
            of documents and 'total' count) and 'took' (time taken). If `count`
            is True, returns an integer representing the total count.

        Raises:
            ValueError: If there is a RequestError or TransportError from
                OpenSearch during the search execution, indicating an issue
                with the query or connection.
        """
        scroll_timeout = None
        if enable_scroll:
            scroll_timeout = "1m"  # Default to 1 minute scroll timeout

        # Exit early if we have no indices to query
        if not indices:
            return {"hits": {"hits": [], "total": 0}, "took": 0}

        # Make sure that the list of index names is uniq.
        indices = list(set(indices))

        if query_filter is None:
            query_filter = {}

        # Check if we have specific events to fetch and get indices.
        if query_filter.get("events", None):
            indices = {
                event["index"]
                for event in query_filter["events"]
                if event["index"] in indices
            }

        query_dsl = self.build_query(
            sketch_id=sketch_id,
            query_string=query_string,
            query_filter=query_filter,
            query_dsl=query_dsl,
            aggregations=aggregations,
            timeline_ids=timeline_ids,
        )

        # Default search type for OpenSearch is query_then_fetch.
        search_type = "query_then_fetch"

        # Only return how many documents matches the query.
        if count:
            if "sort" in query_dsl:
                del query_dsl["sort"]
            try:
                count_result = self.client.count(body=query_dsl, index=list(indices))
            except NotFoundError:
                os_logger.error(
                    "Unable to count due to an index not found: {:s}".format(
                        ",".join(indices)
                    )
                )
                return 0
            METRICS["search_requests"].labels(type="count").inc()
            return count_result.get("count", 0)

        if not return_fields:
            # Suppress the lint error because opensearchpy adds parameters
            # to the function with a decorator and this makes pylint sad.
            # pylint: disable=unexpected-keyword-arg
            return self.client.search(
                body=query_dsl,
                index=list(indices),
                search_type=search_type,
                scroll=scroll_timeout,
            )

        # The argument " _source_include" changed to "_source_includes" in
        # ES version 7. This check add support for both version 6 and 7 clients.
        # pylint: disable=unexpected-keyword-arg
        try:
            if self.version.startswith("6"):
                _search_result = self.client.search(
                    body=query_dsl,
                    index=list(indices),
                    search_type=search_type,
                    _source_include=return_fields,
                    scroll=scroll_timeout,
                )
            else:
                _search_result = self.client.search(
                    body=query_dsl,
                    index=list(indices),
                    search_type=search_type,
                    _source_includes=return_fields,
                    scroll=scroll_timeout,
                )
        except (RequestError, TransportError) as e:
            root_cause = e.info.get("error", {}).get("root_cause")
            if root_cause:
                error_items = []
                for cause in root_cause:
                    error_items.append(
                        "[{:s}] {:s}".format(
                            cause.get("type", ""), cause.get("reason", "")
                        )
                    )
                cause = ", ".join(error_items)
            else:
                cause = str(e)

            os_logger.error(
                "Unable to run search query. Error: %s. "
                "Sketch ID: %s. Indices: %s. ",
                cause,
                sketch_id,
                indices,
                exc_info=True,
            )
            user_friendly_message = (
                f"There was an issue with your search query: {cause}. "
                "Please review your query syntax and try again."
            )
            raise ValueError(user_friendly_message) from e

        METRICS["search_requests"].labels(type="single").inc()
        return _search_result

    # pylint: disable=too-many-arguments

    def search_stream(
        self,
        sketch_id: int,
        indices: list,
        query_string: str = "",
        query_filter: Optional[Dict] = None,
        query_dsl: Optional[Dict] = None,
        return_fields: Optional[list] = None,
        enable_scroll: bool = True,
        timeline_ids: Optional[list] = None,
    ):
        """Search OpenSearch. This will take a query string from the UI
        together with a filter definition. Based on this it will execute the
        search request on OpenSearch and get result back.

        Args :
            sketch_id: Integer of sketch primary key
            query_string: Query string
            query_filter: Dictionary containing filters to apply
            query_dsl: Dictionary containing OpenSearch DSL query
            indices: List of indices to query
            return_fields: List of fields to return
            enable_scroll: Boolean determining whether scrolling is enabled.
            timeline_ids: Optional list of IDs of Timeline objects that should
                be queried as part of the search.

        Yields:
            Generator of event documents in JSON format
        """
        # Make sure that the list of index names is uniq.
        indices = list(set(indices))

        METRICS["search_requests"].labels(type="stream").inc()

        if query_filter is None:
            query_filter = {}

        if not query_filter.get("size"):
            query_filter["size"] = self.DEFAULT_STREAM_LIMIT

        if not query_filter.get("terminate_after"):
            query_filter["terminate_after"] = self.DEFAULT_STREAM_LIMIT

        result = self.search(
            sketch_id=sketch_id,
            query_string=query_string,
            query_dsl=query_dsl,
            query_filter=query_filter,
            indices=indices,
            return_fields=return_fields,
            enable_scroll=enable_scroll,
            timeline_ids=timeline_ids,
        )

        if enable_scroll:
            scroll_id = result["_scroll_id"]
            scroll_size = result["hits"]["total"]
        else:
            scroll_id = None
            scroll_size = 0

        # Elasticsearch version 7.x returns total hits as a dictionary.
        # TODO: Refactor when version 6.x has been deprecated.
        if isinstance(scroll_size, dict):
            scroll_size = scroll_size.get("value", 0)

        yield from result["hits"]["hits"]

        while scroll_size > 0:
            # pylint: disable=unexpected-keyword-arg
            result = self.client.scroll(scroll_id=scroll_id, scroll="5m")
            scroll_id = result["_scroll_id"]
            scroll_size = len(result["hits"]["hits"])
            yield from result["hits"]["hits"]

    def get_filter_labels(self, sketch_id: int, indices: list):
        """Aggregate labels for a sketch.

        Args:
            sketch_id: The Sketch ID
            indices: List of indices to aggregate on

        Returns:
            List with label names.
        """
        # If no indices are provided, return an empty list. This indicates
        # there are no labels to aggregate within the specified sketch.
        # Returning early prevents querying OpenSearch with an empty
        # index list, which would default to querying all indices ("_all")
        # and could potentially cause performance issues or errors.
        if not indices:
            return []

        # This is a workaround to return all labels by setting the max buckets
        # to something big. If a sketch has more than this amount of labels
        # the list will be incomplete but it should be uncommon to have >10k
        # labels in a sketch.
        max_labels = 10000

        # pylint: disable=line-too-long
        aggregation = {
            "aggs": {
                "nested": {
                    "nested": {"path": "timesketch_label"},
                    "aggs": {
                        "inner": {
                            "filter": {
                                "bool": {
                                    "must": [
                                        {
                                            "term": {
                                                "timesketch_label.sketch_id": sketch_id
                                            }
                                        }
                                    ]
                                }
                            },
                            "aggs": {
                                "labels": {
                                    "terms": {
                                        "size": max_labels,
                                        "field": "timesketch_label.name.keyword",
                                    }
                                }
                            },
                        }
                    },
                }
            }
        }

        # Make sure that the list of index names is uniq.
        indices = list(set(indices))

        labels = []
        # pylint: disable=unexpected-keyword-arg
        try:
            result = self.client.search(index=indices, body=aggregation, size=0)
        except NotFoundError:
            os_logger.error(
                "Unable to find the index/indices: {:s}".format(",".join(indices))
            )
            return labels

        buckets = (
            result.get("aggregations", {})
            .get("nested", {})
            .get("inner", {})
            .get("labels", {})
            .get("buckets", [])
        )

        for bucket in buckets:
            new_bucket = {}
            new_bucket["label"] = bucket.pop("key")
            new_bucket["count"] = bucket.pop("doc_count")
            labels.append(new_bucket)
        return labels

    # pylint: disable=inconsistent-return-statements
    def get_event(self, searchindex_id: str, event_id: str):
        """Get one event from the datastore.

        Args:
            searchindex_id: String of OpenSearch index id
            event_id: String of OpenSearch event id

        Returns:
            Event document in JSON format
        """
        METRICS["search_get_event"].inc()

        try:
            # Suppress the lint error because opensearchpy adds parameters
            # to the function with a decorator and this makes pylint sad.
            # pylint: disable=unexpected-keyword-arg
            if self.version.startswith("6"):
                event = self.client.get(
                    index=searchindex_id,
                    id=event_id,
                    _source_exclude=["timesketch_label"],
                )
            else:
                event = self.client.get(
                    index=searchindex_id,
                    id=event_id,
                    _source_excludes=["timesketch_label"],
                )

            return event

        except NotFoundError:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND,
                f"Event '{event_id}' not found in index '{searchindex_id}'.",
            )

    def count(self, indices: list):
        """Count number of documents.

        Args:
            indices: List of indices.

        Returns:
            Tuple containing number of documents and size on disk.
        """
        # Make sure that the list of index names is uniq.
        indices = list(set(indices))

        try:
            es_stats = self.client.indices.stats(index=indices, metric="docs, store")

        except NotFoundError:
            os_logger.error("Unable to count indices (index not found)")
            return 0, 0

        except RequestError:
            os_logger.error("Unable to count indices (request error)", exc_info=True)
            return 0, 0

        doc_count_total = (
            es_stats.get("_all", {})
            .get("primaries", {})
            .get("docs", {})
            .get("count", 0)
        )
        doc_bytes_total = (
            es_stats.get("_all", {})
            .get("primaries", {})
            .get("store", {})
            .get("size_in_bytes", 0)
        )

        return doc_count_total, doc_bytes_total

    def set_label(
        self,
        searchindex_id: str,
        event_id: str,
        sketch_id: int,
        user_id: int,
        label: str,
        toggle: bool = False,
        remove: bool = False,
        single_update: bool = True,
    ):
        """Set label on event in the datastore.

        Args:
            searchindex_id: String of OpenSearch index id
            event_id: String of OpenSearch event id
            sketch_id: Integer of sketch primary key
            user_id: Integer of user primary key
            label: String with the name of the label
            remove: Optional boolean value if the label should be removed
            toggle: Optional boolean value if the label should be toggled
            single_update: Boolean if the label should be indexed immediately.

        Returns:
            Dict with updated document body, or None if this is a single update.
        """
        # OpenSearch painless script.
        update_body = {
            "script": {
                "lang": "painless",
                "source": UPDATE_LABEL_SCRIPT,
                "params": {
                    "timesketch_label": {
                        "name": str(label),
                        "user_id": user_id,
                        "sketch_id": sketch_id,
                    },
                    remove: remove,
                },
            }
        }

        if toggle:
            update_body["script"]["source"] = TOGGLE_LABEL_SCRIPT

        if not single_update:
            script = update_body["script"]
            return {
                "source": script["source"],
                "lang": script["lang"],
                "params": script["params"],
            }

        doc = self.client.get(index=searchindex_id, id=event_id)
        try:
            doc["_source"]["timesketch_label"]
        except KeyError:
            doc = {"doc": {"timesketch_label": []}}
            self.client.update(index=searchindex_id, id=event_id, body=doc)

        self.client.update(index=searchindex_id, id=event_id, body=update_body)

        return None

    def create_index(
        self, index_name: str = uuid4().hex, mappings: Optional[Dict] = None
    ):
        """Create index with Timesketch settings.

        Args:
            index_name: Name of the index. Default is a generated UUID.
            mappings: Optional dict with the document mapping for OpenSearch.

        Returns:
            Index name in string format.
            Document type in string format.
        """
        if mappings:
            _document_mapping = mappings
        else:
            _document_mapping = {
                "properties": {
                    "timesketch_label": {"type": "nested"},
                    "datetime": {"type": "date"},
                }
            }

        if not self.client.indices.exists(index_name):
            try:
                self.client.indices.create(
                    index=index_name, body={"mappings": _document_mapping}
                )
            except ConnectionError as e:
                raise errors.DatastoreConnectionError(
                    "Unable to connect to Timesketch backend when creating "
                    f"index [{index_name}]."
                ) from e
            except RequestError:
                index_exists = self.client.indices.exists(index_name)
                os_logger.warning(
                    "Attempting to create an index that already exists "
                    "({:s} - {:s})".format(index_name, str(index_exists))
                )
            # Wait for the index to become ready
            if not self._wait_for_index(index_name):
                raise errors.IndexNotReadyError(
                    f"Index '{index_name}' was created but did not become ready "
                    f"within the timeout period of {self.DEFAULT_INDEX_WAIT_TIMEOUT}s."
                )

        return index_name

    def delete_index(self, index_name):
        """Delete OpenSearch index.

        Args:
            index_name: Name of the index to delete.
        """
        if self.client.indices.exists(index_name):
            try:
                self.client.indices.delete(index=index_name)
            except ConnectionError as e:
                raise RuntimeError(
                    f"Unable to connect to Timesketch backend: {e}"
                ) from e

    def import_event(
        self,
        index_name: str,
        event: Optional[Dict] = None,
        event_id: Optional[str] = None,
        flush_interval: Optional[int] = None,
        timeline_id: Optional[int] = None,
    ):
        """Add event to OpenSearch.

        Args:
            index_name: Name of the index in OpenSearch
            event: Event dictionary
            event_id: Event OpenSearch ID
            flush_interval: Number of events to queue up before indexing
            timeline_id: Optional ID number of a Timeline object this event
                belongs to. If supplied an additional field will be added to
                the store indicating the timeline this belongs to.
        """
        if event:
            for k, v in event.items():
                if not isinstance(k, str):
                    k = codecs.decode(k, "utf8")

                # Make sure we have decoded strings in the event dict.
                if isinstance(v, bytes):
                    v = codecs.decode(v, "utf8")

                event[k] = v

            # Header needed by OpenSearch when bulk inserting.
            header = {
                "index": {
                    "_index": index_name,
                }
            }
            update_header = {"update": {"_index": index_name, "_id": event_id}}

            if event_id:
                # Event has "lang" defined if there is a script used for import.
                if event.get("lang"):
                    event = {"script": event}
                else:
                    event = {"doc": event}
                header = update_header

            if timeline_id:
                event["__ts_timeline_id"] = timeline_id

            self.import_events.append(header)
            self.import_events.append(event)
            self.import_counter["events"] += 1

            if not flush_interval:
                flush_interval = self.flush_interval

            if self.import_counter["events"] % int(flush_interval) == 0:
                _ = self.flush_queued_events()
                self.import_events = []
        else:
            # Import the remaining events in the queue.
            if self.import_events:
                _ = self.flush_queued_events()

        return self.import_counter["events"]

    def flush_queued_events(self, retry_count=0):
        """Flush all queued events.

        Returns:
            dict: A dict object that contains the number of events
                that were sent to OpenSearch as well as information
                on whether there were any errors, and what the
                details of these errors if any.
            retry_count: optional int indicating whether this is a retry.
        """
        if not self.import_events:
            return {}

        return_dict = {
            "number_of_events": len(self.import_events) / 2,
            "total_events": self.import_counter["events"],
        }

        try:
            # pylint: disable=unexpected-keyword-arg
            results = self.client.bulk(
                body=self.import_events, timeout=self._request_timeout
            )
        except (ConnectionTimeout, socket.timeout):
            if retry_count >= self.DEFAULT_FLUSH_RETRY_LIMIT:
                os_logger.error(
                    "Unable to add events, reached recount max.", exc_info=True
                )
                return {}

            os_logger.error(
                "Unable to add events (retry {:d}/{:d})".format(
                    retry_count, self.DEFAULT_FLUSH_RETRY_LIMIT
                )
            )
            return self.flush_queued_events(retry_count + 1)

        errors_in_upload = results.get("errors", False)
        return_dict["errors_in_upload"] = errors_in_upload

        if errors_in_upload:
            items = results.get("items", [])
            return_dict["errors"] = []

            os_logger.error("Errors while attempting to upload events.")
            for item in items:
                index = item.get("index", {})
                index_name = index.get("_index", "N/A")

                _ = self._error_container.setdefault(
                    index_name, {"errors": [], "types": Counter(), "details": Counter()}
                )

                error_counter = self._error_container[index_name]["types"]
                error_detail_counter = self._error_container[index_name]["details"]
                error_list = self._error_container[index_name]["errors"]

                error = index.get("error", {})
                status_code = index.get("status", 0)
                doc_id = index.get("_id", "(unable to get doc id)")
                caused_by = error.get("caused_by", {})

                caused_reason = caused_by.get("reason", "Unknown Detailed Reason")

                error_counter[error.get("type")] += 1
                detail_msg = "{:s}/{:s}".format(
                    caused_by.get("type", "Unknown Detailed Type"),
                    " ".join(caused_reason.split()[:5]),
                )
                error_detail_counter[detail_msg] += 1

                error_msg = "<{:s}> {:s} [{:s}/{:s}]".format(
                    error.get("type", "Unknown Type"),
                    error.get("reason", "No reason given"),
                    caused_by.get("type", "Unknown Type"),
                    caused_reason,
                )
                error_list.append(error_msg)
                try:
                    os_logger.error(
                        "Unable to upload document: {:s} to index {:s} - "
                        "[{:d}] {:s}".format(doc_id, index_name, status_code, error_msg)
                    )
                # We need to catch all exceptions here, since this is a crucial
                # call that we do not want to break operation.
                except Exception:  # pylint: disable=broad-except
                    os_logger.error(
                        "Unable to upload document, and unable to log the "
                        "error itself.",
                        exc_info=True,
                    )

        return_dict["error_container"] = self._error_container

        self.import_events = []
        return return_dict

    def _export_slice_worker_pit(
        self,
        slice_id: int,
        num_slices: int,
        index_list: List[str],
        query_body: Dict[str, Any],
        current_sort_criteria: List[Dict[str, Any]],
        current_page_size: int,
        current_pit_keep_alive: str,
        output_queue: queue.Queue,
        stop_event: threading.Event,
        worker_request_timeout: int,
    ):
        """
        Worker function for a single slice in a PIT export.
        Fetches documents for its assigned slice and puts them onto the output_queue.
        """
        # Slice ID is 0-indexed, so display as 1-indexed for logs
        log_slice_id = slice_id + 1
        es_logger.info("[PIT Slice %s/%s] Starting export.", log_slice_id, num_slices)
        pit_id = None
        total_docs_in_slice = 0

        try:
            pit_response = self.client.create_pit( # pylint: disable=unexpected-keyword-arg
                index=index_list, keep_alive=current_pit_keep_alive
            )
            pit_id = pit_response["pit_id"]
            es_logger.info(
                "[PIT Slice %s/%s] Created PIT ID: %s",
                log_slice_id,
                num_slices,
                pit_id,
            )

            search_after_params = None
            while not stop_event.is_set():
                query = {
                    **query_body,
                    "size": current_page_size,
                    "sort": current_sort_criteria,
                    "pit": {"id": pit_id, "keep_alive": current_pit_keep_alive},
                    "slice": {"id": slice_id, "max": num_slices},
                }

                if search_after_params:
                    query["search_after"] = search_after_params

                try:
                    response = self.client.search( # pylint: disable=unexpected-keyword-arg
                        body=query, request_timeout=worker_request_timeout
                    )
                except RequestError as re:
                    es_logger.error(
                        "[PIT Slice %s/%s] RequestError: %s. "
                        "PIT might have expired or query issue.",
                        log_slice_id,
                        num_slices,
                        str(re),
                    )
                    break
                except ConnectionTimeout:
                    es_logger.warning(
                        "[PIT Slice %s/%s] Connection timeout during search. "
                        "Stopping slice.",
                        log_slice_id,
                        num_slices,
                    )
                    break
                except Exception as e:  # pylint: disable=broad-exception-caught
                    es_logger.error(
                        "[PIT Slice %s/%s] Error during search: %s",
                        log_slice_id,
                        num_slices,
                        str(e),
                        exc_info=True,
                    )
                    # Signal other threads and main to stop due to unexpected error
                    stop_event.set()
                    break

                hits = response.get("hits", {}).get("hits", [])
                if not hits:
                    es_logger.info(
                        "[PIT Slice %s/%s] No more documents.", log_slice_id, num_slices
                    )
                    break

                for hit in hits:
                    if stop_event.is_set():
                        break
                    if "_source" in hit:
                        event_data_to_export = {
                            **hit["_source"],
                            "_id": hit.get("_id"),
                            "_index": hit.get("_index"),
                        }
                        # Try to put item onto the queue with timeout
                        # This loop handles backpressure if the queue is full.
                        while not stop_event.is_set():
                            try:
                                output_queue.put(
                                    event_data_to_export, timeout=1
                                )  # Short timeout for responsiveness
                                break  # Item put successfully
                            except queue.Full:
                                # Queue is full, wait a bit and retry.
                                # stop_event is checked at the start of this inner loop.
                                time.sleep(0.1)  # Avoid busy-waiting
                            except Exception as e_q: # pylint: disable=broad-exception-caught
                                log_msg = (
                                    "[PIT Slice %s/%s] Error putting to queue: %s"
                                )
                                es_logger.error(
                                    log_msg,
                                    log_slice_id, num_slices,
                                    str(e_q),
                                    exc_info=True,
                                )
                                # Critical error with queue, signal stop
                                stop_event.set()
                                break  # Break from inner for hit in hits loop
                        if stop_event.is_set():
                            break  # Break from outer for hit in hits loop

                if stop_event.is_set():
                     # Break from while True if stop_event was set during item
                     # processing
                    break

                total_docs_in_slice += len(hits)
                es_logger.info(
                    (
                        "[PIT Slice %s/%s] Retrieved %s docs. "
                        "Total for slice: %s. Queue size: ~%s"
                    ),
                    log_slice_id,
                    num_slices,
                    len(hits),
                    total_docs_in_slice,
                    output_queue.qsize(),
                )
                search_after_params = hits[-1].get("sort")
                if (
                    search_after_params is None and hits
                ):  # Check hits because if no hits, search_after_params is not needed
                    es_logger.error(
                        (
                            "[PIT Slice %s/%s] 'sort' field missing in last hit. "
                            "Cannot continue with search_after."
                        ),
                        log_slice_id,
                        num_slices,
                    )
                    stop_event.set()
                    break

        except NotFoundError:
            es_logger.warning(
                "[PIT Slice %s/%s] PIT ID %s not found or expired, "
                "or an index in the list was not found.",
                log_slice_id,
                num_slices,
                pit_id if pit_id else "N/A",
            )
            stop_event.set()  # Signal issue
        except Exception as e: # pylint: disable=broad-exception-caught
            es_logger.error(
                "[PIT Slice %s/%s] An unexpected error occurred: %s",
                log_slice_id,
                num_slices,
                str(e),
                exc_info=True,
            )
            stop_event.set()  # Signal failure
        finally:
            if pit_id:
                try:
                    self.client.delete_pit(body={"pit_id": [pit_id]})
                    es_logger.info(
                        "[PIT Slice %s/%s] Deleted PIT ID: %s",
                        log_slice_id,
                        num_slices,
                        pit_id,
                    )
                except Exception as e: # pylint: disable=broad-exception-caught
                    log_msg = (
                        "[PIT Slice %s/%s] Error deleting PIT ID %s: %s"
                    )
                    es_logger.error(
                        log_msg,
                        log_slice_id, num_slices, pit_id,
                        str(e),
                        exc_info=True,
                    )

            es_logger.info(
                "[PIT Slice %s/%s] Finished. Processed %s documents.",
                log_slice_id,
                num_slices,
                total_docs_in_slice,
            )
            # Signal this worker is done by putting a sentinel, even if an error
            # occurred (unless queue itself failed)
            try:
                output_queue.put(
                    None, timeout=5
                )  # Short timeout, main thread should be consuming
            except queue.Full:
                es_logger.error(
                    "[PIT Slice %s/%s] Failed to put sentinel: Queue full.",
                    log_slice_id,
                    num_slices,
                )
            except Exception as e_s: # pylint: disable=broad-exception-caught
                es_logger.error(
                    "[PIT Slice %s/%s] Failed to put sentinel: %s",
                    log_slice_id,
                    num_slices,
                    str(e_s),
                )

    def export_events_pit(
        self,
        indices_for_pit: List[str],
        base_query_body: Dict[str, Any],
        sort_criteria: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 10000,
        pit_keep_alive: str = "5m",
        num_slices: int = 4,
        request_timeout_per_slice: Optional[int] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Exports events from specified indices using PIT, search_after, and slicing.

        This method is designed for efficient bulk export of large datasets.
        It yields individual event dictionaries, including '_id' and '_index'.

        Args:
            indices_for_pit: List of index names to query.
            base_query_body: The base OpenSearch query body (must not include
                             size, sort, pit, or slice clauses). Can include
                             "_source" to specify fields to return.
            sort_criteria: The sort criteria for search_after.
                           If None, defaults to `[{"_id": "asc"}]`.
                           Must include a unique tie-breaker field (e.g. _id)
                           for stable results across pages.
            page_size: Number of documents per request per slice. Default: 10k
            pit_keep_alive: Keep-alive duration for the Point-In-Time context.
            num_slices: Number of parallel slices to use for the export.
                        Default can be set via app config OPENSEARCH_PIT_NUM_SLICES.
            request_timeout_per_slice: Optional timeout in seconds for individual
                                       OpenSearch search requests within each slice.
                                       Defaults to self.timeout + 20s buffer.

        Yields:
            Dict: Individual event documents (including _id and _index from the hit).

        Raises:
            ValueError: If indices_for_pit is empty or num_slices is invalid.
            errors.DataStoreQueryError: For critical issues during the export.
        """
        if not indices_for_pit:
            raise ValueError("indices_for_pit cannot be empty.")
        if not 1 <= num_slices <= 1024:  # OpenSearch constraint for slices
            raise ValueError("num_slices must be between 1 and 1024.")

        effective_sort_criteria = sort_criteria or _DEFAULT_PIT_SORT_CRITERIA
        worker_timeout = request_timeout_per_slice or (
            self.timeout + 20
        )  # Use configured or default+buffer

        # Adjust num_slices from app config if not provided or if a default is desired.
        # Example:
        # num_slices =
        # num_slices orcurrent_app.config.get('OPENSEARCH_PIT_NUM_SLICES', 5)
        # For now, using the argument directly or its default.

        # Max queue size: buffer for items from all slices for a couple of rounds.
        queue_buffer_factor = 4  # How many "full rounds" of data to buffer
        queue_max_items = page_size * num_slices * queue_buffer_factor
        results_queue: queue.Queue = queue.Queue(maxsize=queue_max_items)

        threads: List[threading.Thread] = []
        stop_event = threading.Event()

        es_logger.info(
            "Starting PIT export from indices: %s with %s slices, page_size: %s.",
            ", ".join(indices_for_pit),
            num_slices,
            page_size,
        )

        active_workers = num_slices

        try:
            for i in range(num_slices):
                thread = threading.Thread(
                    target=self._export_slice_worker_pit,
                    args=( #  type: ignore
                        i,
                        num_slices,
                        # Ensure deep copy for safety
                        indices_for_pit,
                        copy.deepcopy(base_query_body),  # Ensure deep copy for safety
                        effective_sort_criteria,
                        page_size,
                        pit_keep_alive,
                        results_queue,
                        stop_event,
                        worker_timeout,
                    ),
                    # Allows main thread to exit even if workers hang
                    # (though join is preferred)
                    daemon=True,
                )
                threads.append(thread)
                thread.start()

            while active_workers > 0:
                if stop_event.is_set() and results_queue.empty():
                    es_logger.warning(
                        "PIT export stopping early: error signaled "
                        "and queue is empty."
                    ) # yapf: disable
                    break
                try:
                    item = results_queue.get(timeout=0.5)  # Timeout to check stop_event
                    if item is None:  # Sentinel from a finished worker
                        active_workers -= 1
                        results_queue.task_done()
                        es_logger.info(
                            "Worker finished, %s active workers remaining.",
                            active_workers,
                        )
                        continue

                    yield item
                    results_queue.task_done()

                except queue.Empty:
                    # Queue is empty, check if all worker threads have actually exited
                    # This is a secondary check; active_workers decrementing is primary
                    if not any(t.is_alive() for t in threads) and active_workers > 0:
                        es_logger.warning(
                            (
                                "All PIT worker threads seem to have exited but %s "
                                "sentinel(s) not received. Draining queue."
                            ),
                            active_workers,
                        ) # yapf: disable
                        active_workers = 0  # Force loop exit after this drain attempt
                        break  # Break to final drain loop
                except Exception as e_yield: # pylint: disable=broad-exception-caught
                    es_logger.error(
                        "Error yielding item from PIT export queue: %s",
                        str(e_yield),
                        exc_info=True,
                    )
                    stop_event.set()  # Signal workers to stop

            # Final drain of the queue in case of early exit or stragglers
            es_logger.info("Draining any remaining items from the queue.")
            while True:
                try:
                    item = results_queue.get_nowait()
                    if item is None:
                        results_queue.task_done()
                        # Could decrement a counter if tracking sentinels precisely here
                        continue
                    yield item
                    results_queue.task_done()
                except queue.Empty:
                    break  # Queue is confirmed empty

        except Exception as e:
            es_logger.error(
                "Unhandled exception during PIT export setup or yield loop: %s",
                str(e),
                exc_info=True,
            )
            stop_event.set()
            raise errors.DataStoreQueryError(f"PIT Export failed: {str(e)}") from e
        finally:
            es_logger.info(
                "PIT export: Signaling any remaining worker threads to stop."
            )
            stop_event.set()

            for i, thread in enumerate(threads):
                if thread.is_alive():
                    es_logger.info(
                        "PIT export: Waiting for worker thread %s to join.",
                        i + 1
                    )
                    thread.join(timeout=10)  # Give threads a chance to clean up PIT
                    if thread.is_alive():
                        es_logger.warning(
                            (
                                "PIT export: Worker thread %s did not exit "
                                "cleanly after timeout."
                            ),
                            i + 1,
                        )

            # Ensure the queue is fully processed by task_done calls if not
            # using .join() on queue. However, with daemon threads and explicit
            # joining, this might be less critical but good for completeness if
            # there's any doubt.
            if results_queue.unfinished_tasks > 0:
                es_logger.warning(
                    (
                        "PIT export: Queue has %s unfinished tasks. "
                        "This might indicate an issue."
                    ),
                    results_queue.unfinished_tasks,
                )

            es_logger.info("PIT export process cleanup finished.")
