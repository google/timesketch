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
"""This module holds methods and classes to export events."""

import io
import json
import logging

import pandas as pd

from timesketch.api.v1 import utils
from timesketch.lib import utils as lib_utils
from timesketch.lib.stories import api_fetcher as story_api_fetcher

logger = logging.getLogger("timesketch.api_exporter")


def export_aggregation(aggregation, sketch, zip_file):
    """Export an aggregation from a sketch and write it to a ZIP file.

    Args:
        aggregation (timesketch.models.sketch.Aggregation): an aggregation
            object.
        sketch (timesketch.models.sketch.Sketch): a sketch object.
        zip_file (ZipFile): a zip file handle that can be used to write
            content to.
    """
    name = f"{aggregation.id:04d}_{aggregation.name:s}"
    parameters = json.loads(aggregation.parameters)
    result_obj, meta = utils.run_aggregator(
        sketch.id,
        aggregator_name=aggregation.agg_type,
        aggregator_parameters=parameters,
    )

    zip_file.writestr(f"aggregations/{name:s}.meta", data=json.dumps(meta))

    html = result_obj.to_chart(
        chart_name=meta.get("chart_type"),
        chart_title=aggregation.name,
        color=meta.get("chart_color"),
        interactive=True,
        as_html=True,
    )
    zip_file.writestr(f"aggregations/{name:s}.html", data=html)

    string_io = io.StringIO()
    data_frame = result_obj.to_pandas()
    data_frame.to_csv(string_io, index=False)
    string_io.seek(0)
    zip_file.writestr(f"aggregations/{name:s}.csv", data=string_io.read())


def export_aggregation_group(group, sketch, zip_file):
    """Export an aggregation group from a sketch and write it to a ZIP file.

    Args:
        group (timesketch.models.sketch.AggregationGroup): an aggregation
            group object.
        sketch (timesketch.models.sketch.Sketch): a sketch object.
        zip_file (ZipFile): a zip file handle that can be used to write
            content to.
    """
    name = f"{group.id:04d}_{group.name:s}"
    chart, _, meta = utils.run_aggregator_group(group, sketch_id=sketch.id)

    zip_file.writestr(f"aggregation_groups/{name:s}.meta", json.dumps(meta))
    zip_file.writestr(f"aggregation_groups/{name:s}.html", chart.to_html())


def export_story(story, sketch, story_exporter, zip_file):
    """Export a story from a sketch into a ZIP file.

    Args:
        story (timesketch.models.sketch.Story): a story object.
        sketch (timesketch.models.sketch.Sketch): a sketch object.
        story_exporter (timesketch.lib.stories.StoryExporter): an instance of
            a story exporter that can be used to export story content.
        zip_file (ZipFile): a zip file handle that can be used to write
            content to.
    """
    with story_exporter() as exporter:
        data_fetcher = story_api_fetcher.ApiDataFetcher()
        data_fetcher.set_sketch_id(sketch.id)

        exporter.set_data_fetcher(data_fetcher)
        exporter.from_string(story.content)
        exporter.set_creation_date(story.created_at.isoformat())
        if story.user:
            author = story.user.username
        else:
            author = "System"
        exporter.set_author(author)
        exporter.set_title(story.title)

        zip_file.writestr(
            f"stories/{story.id:04d}_{story.title:s}.html",
            data=exporter.export_story(),
        )


def query_to_filehandle(
    query_string="",
    query_dsl="",
    query_filter=None,
    sketch=None,
    datastore=None,
    indices=None,
    timeline_ids=None,
    return_fields=None,
    output_format="csv",
):
    """Query the datastore and return back a file object with the results.

    This function takes a query string or DSL, queries the datastore
    and fetches all the events and stores them in a file-like object
    which gets returned back.

    Args:
        query_string (str): OpenSearch query string.
        query_dsl (str): OpenSearch query DSL as JSON string.
        query_filter (dict): Filter for the query as a dict.
        sketch (timesketch.models.sketch.Sketch): a sketch object.
        datastore (opensearch.OpenSearchDataStore): the datastore object.
        indices (list): List of indices to query
        timeline_ids (list): Optional list of IDs of Timeline objects that
            should be queried as part of the search.
        return_fields (list): List of fields to return
        output_format (str): The format to return (csv or jsonl).

    Returns:
        file-like object in the requested format with the results.
    """
    # Ignoring the size limits to reduce the amount of queries
    # needed to get all the data.
    query_filter["terminate_after"] = 10000
    query_filter["size"] = 10000

    if "from" in query_filter:
        del query_filter["from"]

    result = datastore.search(
        sketch_id=sketch.id,
        query_string=query_string,
        query_filter=query_filter,
        query_dsl=query_dsl,
        enable_scroll=True,
        timeline_ids=timeline_ids,
        return_fields=return_fields,
        indices=indices,
    )

    scroll_id = result.get("_scroll_id", "")
    if not scroll_id:
        return query_results_to_filehandle(result, sketch, output_format=output_format)

    total_count = result.get("hits", {}).get("total", {}).get("value", 0)
    data_frame = lib_utils.query_results_to_dataframe(result, sketch)
    event_count = len(result["hits"]["hits"])

    while event_count < total_count:
        # pylint: disable=unexpected-keyword-arg
        result = datastore.client.scroll(scroll_id=scroll_id, scroll="1m")
        hits = result["hits"]["hits"]
        if not hits:
            # We break here to avoid an infinite loop if OpenSearch returns
            # no more hits, even if we haven't reached the total_count yet.
            # This can happen if the scroll session expires or if there's
            # a mismatch in the reported total count.
            logger.debug(
                "Sketch %d: Scroll returned no hits, breaking loop. "
                "Fetched %d of %d expected events.",
                sketch.id, event_count, total_count
            )
            break

        add_frame = lib_utils.query_results_to_dataframe(result, sketch)
        if add_frame.shape[0]:
            data_frame = pd.concat([data_frame, add_frame], sort=False)
            event_count += len(hits)
        else:
            logger.warning(
                "Sketch %d: Data Frame returned from a search operation was "
                "empty, count %d out of %d total. Query is: "
                '"%s"',
                sketch.id,
                event_count,
                total_count,
                query_string or query_dsl,
            )
            # Increment event_count to avoid infinite loop
            event_count += len(hits)
            continue

    fh = io.StringIO()
    if output_format.lower() == "jsonl":
        data_frame.to_json(fh, orient="records", lines=True)
    else:
        data_frame.to_csv(fh, index=False)
    fh.seek(0)
    return fh


def query_results_to_filehandle(result, sketch, output_format="csv"):
    """Returns a data frame from a OpenSearch query result dict.

    Args:
        result (dict): a dict that contains the response from a
            OpenSearch datastore search.
        sketch (timesketch.models.sketch.Sketch): a sketch object.
        output_format (str): The format to return (csv or jsonl).

    Returns:
        file-like object in the requested format with the results.
    """
    fh = io.StringIO()
    data_frame = lib_utils.query_results_to_dataframe(result, sketch)
    if output_format.lower() == "jsonl":
        data_frame.to_json(fh, orient="records", lines=True)
    else:
        data_frame.to_csv(fh, index=False)
    fh.seek(0)
    return fh
