# Copyright 2025 Google Inc. All rights reserved.
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
"""Timesketch OpenSearch LogStore MCP integration."""

import argparse
import json
import logging
from datetime import datetime, timezone
from typing import Any, Iterable, Optional
from flask import current_app

from sec_gemini.logs_mcp.common import logstore as ls
from sec_gemini.logs_mcp.backends.sqlite.sqlite import _localize_in_utc_if_naive

from timesketch.models import db_session
from timesketch.models.user import User
from timesketch.models.sketch import Sketch, Timeline, Analysis
from timesketch.models.sigma import SigmaRule
from timesketch.models.annotations import Comment, Label, Status
from timesketch.models.acl import AccessControlEntry
from timesketch.lib.datastores.opensearch import OpenSearchDataStore
from timesketch.lib.llms.providers.plaso_types import PLASO_DATA_TYPE_DESCRIPTIONS

logger = logging.getLogger("timesketch.llm.mcp")


def _escape_query_term(k: str) -> str:
    """Escapes Lucene query syntax characters including wildcards."""
    k = k.replace("\\", "\\\\")
    for char in [
        "+",
        "-",
        "=",
        "&&",
        "||",
        ">",
        "<",
        "!",
        "(",
        ")",
        "{",
        "}",
        "[",
        "]",
        "^",
        '"',
        "~",
        "*",
        "?",
        ":",
        "/",
        " ",
    ]:
        k = k.replace(char, f"\\{char}")
    return k


def _build_keyword_clause(kw: str) -> dict:
    r"""Builds an OpenSearch query clause for a keyword search term.

    To satisfy the LogStore substring match contract, we use a hybrid query:
    1. A wildcard query on the non-tokenized message.keyword field to support
       arbitrary mid-word substring matching (e.g. "ystem32\cmd" matching
       "System32\cmd.exe"). Note: message.keyword has ignore_above: 256 limit
       and will not match logs over 256 characters.
    2. A phrase_prefix or wildcard query string on analyzed text fields as a
       robust fallback for long messages. Note: phrase_prefix only allows the
       last token in the sequence to match as a prefix (e.g. "System32\cmd.ex"
       will match "cmd.exe"), but does not support matching partial prefixes of
       middle tokens (e.g. "ystem32\cmd" will fail on analyzed text fields).
    """
    escaped_raw = _escape_query_term(kw)
    wildcard_clause = {
        "wildcard": {
            "message.keyword": {
                "value": f"*{escaped_raw}*",
                "case_insensitive": True,
            }
        }
    }

    if any(c in kw for c in ("/", "\\", ":", " ")):
        analyzed_clause = {
            "multi_match": {
                "query": kw,
                "type": "phrase_prefix",
                "fields": ["message", "tag", "yara_match", "timestamp_desc"],
            }
        }
    else:
        kw_query = f"*{escaped_raw}*" if kw else ""
        analyzed_clause = {
            "query_string": {
                "query": kw_query,
                "default_operator": "AND",
                "fields": ["message", "tag", "yara_match", "timestamp_desc"],
            }
        }

    return {
        "bool": {
            "should": [analyzed_clause, wildcard_clause],
            "minimum_should_match": 1,
        }
    }


class OpenSearchLogStore(ls.LogStore):
    """OpenSearch-backed LogStore implementation for Timesketch."""

    def __init__(self, sketch_id: Optional[int] = None):
        if sketch_id is None:
            parser = argparse.ArgumentParser()
            parser.add_argument("--sketch_id", type=int, required=True)
            args, _ = parser.parse_known_args()
            sketch_id = args.sketch_id
        self.sketch_id = sketch_id
        from timesketch.app import create_app
        self.app = create_app()

    async def describe_logs(self) -> ls.LogDescriptions:
        with self.app.app_context():
            datastore = OpenSearchDataStore()
            sketch_db = db_session.query(Sketch).get(self.sketch_id)
            if not sketch_db:
                return ls.LogDescriptions(
                    status=ls.ResultStatus.ERROR,
                    descriptions=[],
                    error_messages=[f"Sketch {self.sketch_id} not found"],
                )
            active_timelines = list(sketch_db.active_timelines)
            if not active_timelines:
                return ls.LogDescriptions(
                    status=ls.ResultStatus.SUCCESS, descriptions=[]
                )
            indices = [tl.searchindex.index_name for tl in active_timelines]

            try:
                agg_res = datastore.client.search(
                    index=indices,
                    body={
                        "size": 0,
                        "aggs": {
                            "unique_types": {
                                "terms": {
                                    "field": "data_type.keyword",
                                    "size": 1000,
                                }
                            }
                        },
                    },
                )
                buckets = (
                    agg_res.get("aggregations", {})
                    .get("unique_types", {})
                    .get("buckets", [])
                )
                data_types = [b.get("key") for b in buckets if b.get("key")]
            except Exception as e:  # pylint: disable=broad-except
                return ls.LogDescriptions(
                    status=ls.ResultStatus.ERROR,
                    descriptions=[],
                    error_messages=[f"Failed to query unique log types: {str(e)}"],
                )

            descriptions = []
            for dt in data_types:
                examples = []
                try:
                    res = datastore.client.search(
                        index=indices,
                        body={
                            "query": {"term": {"data_type.keyword": dt}},
                            "size": 5,
                        },
                    )
                    hits = res.get("hits", {}).get("hits", [])
                    for hit in hits:
                        src = hit.get("_source", {})
                        dt_val = src.get("datetime")
                        if dt_val:
                            dt_parsed = datetime.fromisoformat(
                                dt_val.replace("Z", "+00:00")
                            )
                        else:
                            dt_parsed = datetime.fromtimestamp(0, timezone.utc)

                        tags = src.get("tag", [])
                        if isinstance(tags, str):
                            tags = [tags]
                        elif not tags:
                            tags = []
                        yara = src.get("yara_match", [])
                        if isinstance(yara, str):
                            yara = [yara]
                        elif not yara:
                            yara = []
                        merged_tags = sorted(list(set(tags + yara)))

                        examples.append(
                            ls.LogRecordResult(
                                record_id=hit.get("_id"),
                                log_type=dt,
                                timestamp=dt_parsed,
                                timestamp_desc=src.get("timestamp_desc"),
                                message=src.get("message", ""),
                                enrichment=json.dumps(merged_tags),
                            )
                        )
                except Exception:  # pylint: disable=broad-except
                    pass

                daily_counts = []
                try:
                    hist_body = {
                        "size": 0,
                        "query": {"term": {"data_type.keyword": dt}},
                        "aggs": {
                            "by_day": {
                                "date_histogram": {
                                    "field": "datetime",
                                    "calendar_interval": "day",
                                    "format": "yyyy-MM-dd",
                                }
                            }
                        },
                    }
                    hist_res = datastore.client.search(index=indices, body=hist_body)
                    buckets = (
                        hist_res.get("aggregations", {})
                        .get("by_day", {})
                        .get("buckets", [])
                    )
                    for b in buckets:
                        daily_counts.append(
                            (b.get("key_as_string"), b.get("doc_count", 0))
                        )
                except Exception:  # pylint: disable=broad-except
                    pass

                readable_desc = PLASO_DATA_TYPE_DESCRIPTIONS.get(
                    dt, f"Plaso logs of type '{dt}'"
                )
                descriptions.append(
                    ls.LogDescription(
                        log_type=dt,
                        description=readable_desc,
                        per_day_counts=daily_counts,
                        examples=examples,
                    )
                )

            return ls.LogDescriptions(
                status=ls.ResultStatus.SUCCESS, descriptions=descriptions
            )

    async def search_logs(
        self,
        log_type: Optional[Any],
        limit: int,
        at_or_after: Optional[datetime],
        at_or_before: Optional[datetime],
        contains_at_least_one_of: Optional[Iterable[str]],
        must_contain_all_of: Optional[Iterable[str]],
        must_not_contain_any_of: Optional[Iterable[str]],
        order_by: ls.Order,
        exclude_log_type: Optional[Any] = None,
    ) -> ls.SearchResult:
        try:
            with self.app.app_context():
                datastore = OpenSearchDataStore()
                sketch_db = db_session.query(Sketch).get(self.sketch_id)
                if not sketch_db:
                    return ls.SearchResult(
                        status=ls.ResultStatus.ERROR,
                        results=[],
                        error_messages=[f"Sketch {self.sketch_id} not found"],
                    )
                active_timelines = list(sketch_db.active_timelines)

                if log_type:
                    log_types_list = (
                        [log_type] if isinstance(log_type, str) else log_type
                    )
                    active_timelines = [
                        tl for tl in active_timelines if tl.name in log_types_list
                    ]

                if exclude_log_type:
                    exclude_types_list = (
                        [exclude_log_type]
                        if isinstance(exclude_log_type, str)
                        else exclude_log_type
                    )
                    active_timelines = [
                        tl
                        for tl in active_timelines
                        if tl.name not in exclude_types_list
                    ]

                if not active_timelines:
                    return ls.SearchResult(status=ls.ResultStatus.SUCCESS, results=[])

                indices = [tl.searchindex.index_name for tl in active_timelines]
                timeline_ids = [str(tl.id) for tl in active_timelines]

                must_clauses = [{"terms": {"__ts_timeline_id": timeline_ids}}]
                must_not_clauses = []

                if must_contain_all_of:
                    for kw in must_contain_all_of:
                        must_clauses.append(_build_keyword_clause(kw))

                if contains_at_least_one_of:
                    should_clauses = []
                    for kw in contains_at_least_one_of:
                        should_clauses.append(_build_keyword_clause(kw))
                    must_clauses.append(
                        {
                            "bool": {
                                "should": should_clauses,
                                "minimum_should_match": 1,
                            }
                        }
                    )

                if must_not_contain_any_of:
                    for kw in must_not_contain_any_of:
                        must_not_clauses.append(_build_keyword_clause(kw))

                range_query = {}
                if at_or_after:
                    at_or_after = _localize_in_utc_if_naive(at_or_after)
                    range_query["gte"] = at_or_after.isoformat()
                if at_or_before:
                    at_or_before = _localize_in_utc_if_naive(at_or_before)
                    range_query["lte"] = at_or_before.isoformat()
                if range_query:
                    must_clauses.append({"range": {"datetime": range_query}})

                body = {
                    "query": {
                        "bool": {
                            "must": must_clauses,
                            "must_not": must_not_clauses,
                        }
                    },
                    "size": limit,
                }

                if order_by == ls.Order.CHRONOLOGICAL:
                    body["sort"] = [{"datetime": {"order": "asc"}}]
                elif order_by == ls.Order.REVERSE_CHRONOLOGICAL:
                    body["sort"] = [{"datetime": {"order": "desc"}}]

                try:
                    res = datastore.client.search(index=indices, body=body)
                    hits = res.get("hits", {}).get("hits", [])
                    records = []
                    for hit in hits:
                        src = hit.get("_source", {})
                        dt = src.get("datetime")
                        if dt:
                            dt_parsed = datetime.fromisoformat(
                                dt.replace("Z", "+00:00")
                            )
                        else:
                            dt_parsed = datetime.fromtimestamp(0, timezone.utc)
                        tags = src.get("tag", [])
                        if isinstance(tags, str):
                            tags = [tags]
                        elif not tags:
                            tags = []
                        yara = src.get("yara_match", [])
                        if isinstance(yara, str):
                            yara = [yara]
                        elif not yara:
                            yara = []
                        merged_tags = sorted(list(set(tags + yara)))
                        records.append(
                            ls.LogRecordResult(
                                record_id=hit.get("_id"),
                                log_type=src.get("data_type"),
                                timestamp=dt_parsed,
                                timestamp_desc=src.get("timestamp_desc"),
                                message=src.get("message", ""),
                                enrichment=json.dumps(merged_tags),
                            )
                        )
                    return ls.SearchResult(
                        status=ls.ResultStatus.SUCCESS, results=records
                    )
                except Exception as e:  # pylint: disable=broad-except
                    return ls.SearchResult(
                        status=ls.ResultStatus.ERROR,
                        results=[],
                        error_messages=[str(e)],
                    )
        except Exception:
            logger.exception("Fatal error in OpenSearchLogStore.search_logs")
            raise
