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
from __future__ import unicode_literals

from collections import Counter
import copy
import codecs
import json
import logging
import socket
from uuid import uuid4
import six

from dateutil import parser, relativedelta
from opensearchpy import OpenSearch
from opensearchpy.exceptions import ConnectionTimeout
from opensearchpy.exceptions import NotFoundError
from opensearchpy.exceptions import RequestError

# pylint: disable=redefined-builtin
from opensearchpy.exceptions import ConnectionError

from flask import abort
from flask import current_app
import prometheus_client

from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.definitions import METRICS_NAMESPACE


# Setup logging
es_logger = logging.getLogger("timesketch.opensearch")
es_logger.setLevel(logging.WARNING)

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


class OpenSearchDataStore(object):
    """Implements the datastore."""

    DEFAULT_SIZE = 100
    DEFAULT_FLUSH_INTERVAL = 1000
    DEFAULT_LIMIT = DEFAULT_SIZE  # Max events to return
    DEFAULT_FROM = 0
    DEFAULT_STREAM_LIMIT = 5000  # Max events to return when streaming results

    DEFAULT_FLUSH_RETRY_LIMIT = 3  # Max retries for flushing the queue.
    DEFAULT_EVENT_IMPORT_TIMEOUT = 180  # Timeout value in seconds for importing events.

    def __init__(self, host="127.0.0.1", port=9200):
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

    @staticmethod
    def _build_labels_query(sketch_id, labels):
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
    def _build_query_dsl(query_dsl, timeline_ids):
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
            es_logger.error(
                "Attempting to pass in timelines to a query DSL, but the "
                "passed timelines are not a list."
            )
            return query_dsl

        if not all([isinstance(x, int) for x in timeline_ids]):
            es_logger.error("All timeline IDs need to be an integer.")
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
    def _convert_to_time_range(interval):
        """Convert an interval timestamp into start and end dates.

        Args:
            interval: Time frame representation

        Returns:
            Start timestamp in string format.
            End timestamp in string format.
        """
        # return ('2018-12-05T00:00:00', '2018-12-05T23:59:59')
        TS_FORMAT = "%Y-%m-%dT%H:%M:%S"
        get_digits = lambda s: int("".join(filter(str.isdigit, s)))
        get_alpha = lambda s: "".join(filter(str.isalpha, s))

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
        sketch_id,
        query_string,
        query_filter,
        query_dsl=None,
        aggregations=None,
        timeline_ids=None,
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
                    range_filter = lambda start, end: {
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
        sketch_id,
        query_string,
        query_filter,
        query_dsl,
        indices,
        count=False,
        aggregations=None,
        return_fields=None,
        enable_scroll=False,
        timeline_ids=None,
    ):
        """Search OpenSearch. This will take a query string from the UI
        together with a filter definition. Based on this it will execute the
        search request on OpenSearch and get result back.

        Args:
            sketch_id: Integer of sketch primary key
            query_string: Query string
            query_filter: Dictionary containing filters to apply
            query_dsl: Dictionary containing OpenSearch DSL query
            indices: List of indices to query
            count: Boolean indicating if we should only return result count
            aggregations: Dict of OpenSearch aggregations
            return_fields: List of fields to return
            enable_scroll: If OpenSearch scroll API should be used
            timeline_ids: Optional list of IDs of Timeline objects that should
                be queried as part of the search.

        Returns:
            Set of event documents in JSON format
        """
        scroll_timeout = None
        if enable_scroll:
            scroll_timeout = "1m"  # Default to 1 minute scroll timeout

        # Exit early if we have no indices to query
        if not indices:
            return {"hits": {"hits": [], "total": 0}, "took": 0}

        # Make sure that the list of index names is uniq.
        indices = list(set(indices))

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
                es_logger.error(
                    "Unable to count due to an index not found: {0:s}".format(
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
        except RequestError as e:
            root_cause = e.info.get("error", {}).get("root_cause")
            if root_cause:
                error_items = []
                for cause in root_cause:
                    error_items.append(
                        "[{0:s}] {1:s}".format(
                            cause.get("type", ""), cause.get("reason", "")
                        )
                    )
                cause = ", ".join(error_items)
            else:
                cause = str(e)

            es_logger.error(
                "Unable to run search query: {0:s}".format(cause), exc_info=True
            )
            raise ValueError(cause) from e

        METRICS["search_requests"].labels(type="single").inc()
        return _search_result

    # pylint: disable=too-many-arguments
    def search_stream(
        self,
        sketch_id=None,
        query_string=None,
        query_filter=None,
        query_dsl=None,
        indices=None,
        return_fields=None,
        enable_scroll=True,
        timeline_ids=None,
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

        Returns:
            Generator of event documents in JSON format
        """
        # Make sure that the list of index names is uniq.
        indices = list(set(indices))

        METRICS["search_requests"].labels(type="stream").inc()

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

        for event in result["hits"]["hits"]:
            yield event

        while scroll_size > 0:
            # pylint: disable=unexpected-keyword-arg
            result = self.client.scroll(scroll_id=scroll_id, scroll="5m")
            scroll_id = result["_scroll_id"]
            scroll_size = len(result["hits"]["hits"])
            for event in result["hits"]["hits"]:
                yield event

    def get_filter_labels(self, sketch_id, indices):
        """Aggregate labels for a sketch.

        Args:
            sketch_id: The Sketch ID
            indices: List of indices to aggregate on

        Returns:
            List with label names.
        """
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
            es_logger.error(
                "Unable to find the index/indices: {0:s}".format(",".join(indices))
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
    def get_event(self, searchindex_id, event_id):
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
            abort(HTTP_STATUS_CODE_NOT_FOUND)

    def count(self, indices):
        """Count number of documents.

        Args:
            indices: List of indices.

        Returns:
            Tuple containing number of documents and size on disk.
        """
        if not indices:
            return 0, 0

        # Make sure that the list of index names is uniq.
        indices = list(set(indices))

        try:
            es_stats = self.client.indices.stats(index=indices, metric="docs, store")

        except NotFoundError:
            es_logger.error("Unable to count indices (index not found)")
            return 0, 0

        except RequestError:
            es_logger.error("Unable to count indices (request error)", exc_info=True)
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
        searchindex_id,
        event_id,
        sketch_id,
        user_id,
        label,
        toggle=False,
        remove=False,
        single_update=True,
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
            return dict(
                source=script["source"], lang=script["lang"], params=script["params"]
            )

        doc = self.client.get(index=searchindex_id, id=event_id)
        try:
            doc["_source"]["timesketch_label"]
        except KeyError:
            doc = {"doc": {"timesketch_label": []}}
            self.client.update(index=searchindex_id, id=event_id, body=doc)

        self.client.update(index=searchindex_id, id=event_id, body=update_body)

        return None

    def create_index(self, index_name=uuid4().hex, mappings=None):
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
                raise RuntimeError("Unable to connect to Timesketch backend.") from e
            except RequestError:
                index_exists = self.client.indices.exists(index_name)
                es_logger.warning(
                    "Attempting to create an index that already exists "
                    "({0:s} - {1:s})".format(index_name, str(index_exists))
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
                    "Unable to connect to Timesketch backend: {}".format(e)
                ) from e

    def import_event(
        self,
        index_name,
        event=None,
        event_id=None,
        flush_interval=None,
        timeline_id=None,
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
                if not isinstance(k, six.text_type):
                    k = codecs.decode(k, "utf8")

                # Make sure we have decoded strings in the event dict.
                if isinstance(v, six.binary_type):
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
                es_logger.error(
                    "Unable to add events, reached recount max.", exc_info=True
                )
                return {}

            es_logger.error(
                "Unable to add events (retry {0:d}/{1:d})".format(
                    retry_count, self.DEFAULT_FLUSH_RETRY_LIMIT
                )
            )
            return self.flush_queued_events(retry_count + 1)

        errors_in_upload = results.get("errors", False)
        return_dict["errors_in_upload"] = errors_in_upload

        if errors_in_upload:
            items = results.get("items", [])
            return_dict["errors"] = []

            es_logger.error("Errors while attempting to upload events.")
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

                caused_reason = caused_by.get("reason", "Unkown Detailed Reason")

                error_counter[error.get("type")] += 1
                detail_msg = "{0:s}/{1:s}".format(
                    caused_by.get("type", "Unknown Detailed Type"),
                    " ".join(caused_reason.split()[:5]),
                )
                error_detail_counter[detail_msg] += 1

                error_msg = "<{0:s}> {1:s} [{2:s}/{3:s}]".format(
                    error.get("type", "Unknown Type"),
                    error.get("reason", "No reason given"),
                    caused_by.get("type", "Unknown Type"),
                    caused_reason,
                )
                error_list.append(error_msg)
                try:
                    es_logger.error(
                        "Unable to upload document: {0:s} to index {1:s} - "
                        "[{2:d}] {3:s}".format(
                            doc_id, index_name, status_code, error_msg
                        )
                    )
                # We need to catch all exceptions here, since this is a crucial
                # call that we do not want to break operation.
                except Exception:  # pylint: disable=broad-except
                    es_logger.error(
                        "Unable to upload document, and unable to log the "
                        "error itself.",
                        exc_info=True,
                    )

        return_dict["error_container"] = self._error_container

        self.import_events = []
        return return_dict
