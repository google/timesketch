# Copyright 2026 Google Inc. All rights reserved.
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
"""Timesketch API Client LogStore implementation aligned with reference."""

import asyncio
import datetime
import logging
import math
from typing import Any, Iterable, Optional

# pylint: disable=import-error
from sec_gemini.logs_mcp.common import logstore as ls

# pylint: enable=import-error
from timesketch_api_client import client as ts_client
from timesketch_api_client import search

import plaso_types

logger = logging.getLogger("timesketch.byot.logstore")

EPOCH_START = datetime.datetime(1970, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)


def _escape_opensearch_query(k: str) -> str:
    """Escapes OpenSearch reserved characters including backslashes."""
    # Backslash must be escaped first
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


def _multi_field_clause(keyword: str, negate: bool = False) -> str:
    """Builds a substring match query across message, tags, and timestamp_desc."""
    escaped = _escape_opensearch_query(keyword)
    fields = [
        "message.keyword",
        "tag",
        "yara_match",
        "timestamp_desc",
    ]
    match_clause = " OR ".join(f"{field}:*{escaped}*" for field in fields)
    if negate:
        return f"NOT ({match_clause})"
    return f"({match_clause})"


def _parse_datetime(val) -> datetime.datetime:
    """Safely parses a cell value as a datetime object, returning Epoch 0 on failure."""
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return EPOCH_START
    if isinstance(val, datetime.datetime):
        return val
    try:
        clean_val = str(val).replace("Z", "+00:00")
        return datetime.datetime.fromisoformat(clean_val)
    except ValueError:
        return EPOCH_START


class TimesketchLogStore(ls.LogStore):
    """Adapter implementing the Arcadia LogStore format backed by Timesketch API."""

    def __init__(self, api: ts_client.TimesketchApi, sketch_id: int):
        self.api = api
        self.sketch_id = sketch_id

    async def describe_logs(self) -> ls.LogDescriptions:
        """Discovers Timesketch data types and computes daily histograms."""
        return await asyncio.to_thread(self._describe_logs_sync)

    def _describe_logs_sync(self) -> ls.LogDescriptions:
        """Synchronously discovers log types and aggregates histograms.

        Returns:
            LogDescriptions: Discovered data types and volume information.
        """
        logger.info("[%d] Discovering sketch log types...", self.sketch_id)
        try:
            sketch = self.api.get_sketch(self.sketch_id)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("Failed to get sketch %d", self.sketch_id)
            return ls.LogDescriptions(
                status=ls.ResultStatus.ERROR,
                descriptions=[],
                error_messages=[f"Failed to get sketch {self.sketch_id}: {str(e)}"],
            )

        # Discover unique data types using run_aggregator
        try:
            type_res = sketch.run_aggregator(
                aggregator_name="field_bucket",
                aggregator_parameters={"field": "data_type", "limit": 1000},
            )
            objects = type_res.data.get("objects")
            buckets = []
            if objects and isinstance(objects, list) and objects[0]:
                buckets = objects[0].get("field_bucket", {}).get("buckets", [])
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("Failed to discover unique log types")
            return ls.LogDescriptions(
                status=ls.ResultStatus.ERROR,
                descriptions=[],
                error_messages=[f"Failed to discover unique log types: {str(e)}"],
            )

        descriptions = []
        for b in buckets:
            dt = b["data_type"]

            # Query for the earliest event (min time) for this data type
            min_search = search.Search(sketch=sketch)
            min_search.query_string = f'data_type:"{dt}"'
            min_search.max_entries = 1
            min_search.return_fields = "datetime"
            min_search.order_ascending()
            min_df = min_search.table

            start_str = "1970-01-01T00:00:00Z"
            if not min_df.empty:
                min_val = min_df.iloc[0].get("datetime")
                if min_val:
                    min_time = _parse_datetime(min_val)
                    min_bounded = (min_time - datetime.timedelta(days=1)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    start_str = min_bounded.strftime("%Y-%m-%dT%H:%M:%SZ")

            # Query for the latest event (max time) for this data type
            max_search = search.Search(sketch=sketch)
            max_search.query_string = f'data_type:"{dt}"'
            max_search.max_entries = 1
            max_search.return_fields = "datetime"
            max_search.order_descending()
            max_df = max_search.table

            end_str = "2099-01-01T00:00:00Z"
            if not max_df.empty:
                max_val = max_df.iloc[0].get("datetime")
                if max_val:
                    max_time = _parse_datetime(max_val)
                    max_bounded = (max_time + datetime.timedelta(days=1)).replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                    end_str = max_bounded.strftime("%Y-%m-%dT%H:%M:%SZ")

            search_obj = search.Search(sketch=sketch)
            search_obj.query_string = f'data_type:"{dt}"'
            search_obj.max_entries = 5
            search_obj.return_fields = (
                "datetime,message,_id,timestamp_desc,tag,yara_match"
            )
            search_obj.order_descending()
            results_df = search_obj.table

            examples = []
            for _, row in results_df.iterrows():
                msg = row.get("message", "")
                tags_val = row.get("tag", [])
                if isinstance(tags_val, list):
                    tags_list = tags_val
                elif tags_val:
                    tags_list = [tags_val]
                else:
                    tags_list = []

                yara_val = row.get("yara_match", [])
                if isinstance(yara_val, list):
                    yara_list = yara_val
                elif yara_val:
                    yara_list = [yara_val]
                else:
                    yara_list = []

                merged_tags = sorted(
                    list(
                        set(
                            str(t)
                            for t in tags_list + yara_list
                            if t and str(t).lower() != "n/a"
                        )
                    )
                )
                enrich = ", ".join(merged_tags) if merged_tags else None

                examples.append(
                    ls.LogRecordResult(
                        record_id=str(row.get("_id", "")),
                        log_type=dt,
                        timestamp=_parse_datetime(row.get("datetime")),
                        timestamp_desc=str(row.get("timestamp_desc", "null")),
                        message=str(msg),
                        enrichment=enrich,
                    )
                )

            day_counts = []
            error_suffix = ""
            try:
                aggregator_params = {
                    "field": "data_type",
                    "field_query_string": dt,
                    "supported_intervals": "day",
                    "supported_charts": "table",
                    "start_time": start_str,
                    "end_time": end_str,
                }
                agg_obj = sketch.run_aggregator(
                    aggregator_name="date_histogram",
                    aggregator_parameters=aggregator_params,
                )
                raw_objects = agg_obj.resource_data.get("objects", [])
                if raw_objects:
                    agg_data = raw_objects[0].get("date_histogram", {})
                    hist_buckets = agg_data.get("buckets", [])

                    if hist_buckets and isinstance(hist_buckets[0], list):
                        hist_buckets = hist_buckets[0]

                    for row in hist_buckets:
                        d_raw = row.get("datetime") or row.get("key_as_string")
                        if d_raw:
                            d_str = str(d_raw)[:10]
                            c_val = int(row.get("count") or row.get("doc_count") or 0)
                            if c_val > 0:
                                day_counts.append((d_str, c_val))
            except Exception:  # pylint: disable=broad-exception-caught
                logger.exception("Failed to run date histogram aggregation for %s", dt)
                error_suffix = " ERROR: Failed to compute date histogram."

            dt_desc = plaso_types.PLASO_DATA_TYPE_DESCRIPTIONS.get(
                dt, f"Timesketch log source for {dt}"
            )
            if error_suffix:
                dt_desc += error_suffix

            descriptions.append(
                ls.LogDescription(
                    log_type=dt,
                    description=dt_desc,
                    per_day_counts=day_counts,
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
        at_or_after: Optional[datetime.datetime],
        at_or_before: Optional[datetime.datetime],
        contains_at_least_one_of: Optional[Iterable[str]] = None,
        must_contain_all_of: Optional[Iterable[str]] = None,
        must_not_contain_any_of: Optional[Iterable[str]] = None,
        order_by: ls.Order = ls.Order.CHRONOLOGICAL,
        exclude_log_type: Optional[Any] = None,  # pylint: disable=unused-argument
    ) -> ls.SearchResult:
        """Executes a search mapped directly to OpenSearch query strings."""
        return await asyncio.to_thread(
            self._search_logs_sync,
            log_type=log_type,
            limit=limit,
            at_or_after=at_or_after,
            at_or_before=at_or_before,
            contains_at_least_one_of=contains_at_least_one_of,
            must_contain_all_of=must_contain_all_of,
            must_not_contain_any_of=must_not_contain_any_of,
            order_by=order_by,
        )

    def _search_logs_sync(
        self,
        log_type: Optional[str],
        limit: int,
        at_or_after: Optional[datetime.datetime],
        at_or_before: Optional[datetime.datetime],
        contains_at_least_one_of: Optional[Iterable[str]] = None,
        must_contain_all_of: Optional[Iterable[str]] = None,
        must_not_contain_any_of: Optional[Iterable[str]] = None,
        order_by: ls.Order = ls.Order.CHRONOLOGICAL,
    ) -> ls.SearchResult:
        """Synchronously searches logs in Timesketch using specific filters.

        Args:
            log_type: The log source type string.
            limit: Maximum count of results.
            at_or_after: Lower bound timestamp.
            at_or_before: Upper bound timestamp.
            contains_at_least_one_of: Match any of these keywords.
            must_contain_all_of: Match all of these keywords.
            must_not_contain_any_of: Exclude these keywords.
            order_by: Order enum value.

        Returns:
            SearchResult: Result object matching search criteria.
        """
        sketch = self.api.get_sketch(self.sketch_id)

        terms = []
        if log_type:
            terms.append(f'data_type:"{log_type}"')

        if must_contain_all_of:
            for keyword in must_contain_all_of:
                terms.append(_multi_field_clause(keyword))

        if contains_at_least_one_of:
            or_terms = [_multi_field_clause(k) for k in contains_at_least_one_of]
            terms.append("(" + " OR ".join(or_terms) + ")")

        if must_not_contain_any_of:
            for keyword in must_not_contain_any_of:
                terms.append(_multi_field_clause(keyword, negate=True))

        if at_or_after or at_or_before:
            start_str = at_or_after.isoformat() if at_or_after else "*"
            end_str = at_or_before.isoformat() if at_or_before else "*"
            terms.append(f"datetime:[{start_str} TO {end_str}]")

        query_str = " AND ".join(terms) if terms else "*"
        logger.info("[%d] Searching Timesketch logs: ( %s )", self.sketch_id, query_str)

        search_obj = search.Search(sketch=sketch)
        search_obj.query_string = query_str
        search_obj.max_entries = min(limit, 1000)

        hash_fields = [
            "hash",
            "sha256_hash",
            "sha256",
            "sha1_hash",
            "sha1",
            "md5_hash",
            "md5",
        ]
        base_fields = [
            "datetime",
            "message",
            "_id",
            "timestamp_desc",
            "tag",
            "yara_match",
        ]
        search_obj.return_fields = ",".join(base_fields + hash_fields)

        if order_by == ls.Order.REVERSE_CHRONOLOGICAL:
            search_obj.order_descending()
        elif order_by == ls.Order.CHRONOLOGICAL:
            search_obj.order_ascending()

        results_df = search_obj.table

        res = []
        for _, row in results_df.iterrows():
            msg = str(row.get("message", ""))

            found_hashes = []
            for field_name in hash_fields:
                val = row.get(field_name)
                if val and str(val).strip() and str(val).lower() != "n/a":
                    found_hashes.append(f"{field_name}={val}")

            if found_hashes:
                hash_ctx = ", ".join(found_hashes)
                msg = f"[{hash_ctx}] {msg}"

            tags_val = row.get("tag", [])
            if isinstance(tags_val, list):
                tags_list = tags_val
            elif tags_val:
                tags_list = [tags_val]
            else:
                tags_list = []

            yara_val = row.get("yara_match", [])
            if isinstance(yara_val, list):
                yara_list = yara_val
            elif yara_val:
                yara_list = [yara_val]
            else:
                yara_list = []

            merged_tags = sorted(
                list(
                    set(
                        str(t)
                        for t in tags_list + yara_list
                        if t and str(t).lower() != "n/a"
                    )
                )
            )
            enrich = ", ".join(merged_tags) if merged_tags else None

            res.append(
                ls.LogRecordResult(
                    record_id=str(row.get("_id", "")),
                    log_type=str(row.get("data_type", "none")),
                    timestamp=_parse_datetime(row.get("datetime")),
                    timestamp_desc=str(row.get("timestamp_desc", "null")),
                    message=msg,
                    enrichment=enrich,
                )
            )

        return ls.SearchResult(status=ls.ResultStatus.SUCCESS, results=res)


class DynamicLogStoreMap(dict):
    """Dynamic dict subclass returning TimesketchLogStore per sketch/ticket ID."""

    def __init__(self, api: ts_client.TimesketchApi):
        self.api = api
        super().__init__()

    def __contains__(self, key: Any) -> bool:
        return True

    def __getitem__(self, key: Any) -> TimesketchLogStore:
        try:
            sketch_id = int(key)
        except (ValueError, TypeError) as exc:
            raise KeyError(f"Invalid sketch_id format: {key}") from exc
        return TimesketchLogStore(self.api, sketch_id)
