# Copyright 2021 Google Inc. All rights reserved.
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
"""Commands for searching Timesketch data."""

import json
import sys

from typing import Tuple, Optional
import click
from tabulate import tabulate

from timesketch_api_client import search


def format_output(
    search_obj: search.Search,
    output_format: str,
    show_headers: bool,
    show_internal_columns: bool,
):
    """Formats search results from a search object into a specified output format.

    Converts search results from an API Search object into a pandas DataFrame
    and then formats it according to the provided output format,
    header visibility, and internal column visibility.
    Supported output formats are 'text', 'csv', 'json', 'jsonl', and 'tabular'.

    Args:
        search_obj (search.Search): The API Search object containing search results.
        output_format (str): The desired output format
            ('text', 'csv', 'json', 'jsonl', or 'tabular').
        show_headers (bool): If True, includes headers in the output.
        show_internal_columns (bool): If True, includes internal columns in the output.

    Returns:
        The formatted search results as a string, or None if an error occurs.

        Returns None if the search_obj.to_pandas() returns an empty data frame.

    Raises:
        ImportError: If the 'tabulate' library is not installed and 'tabular'
        format is selected.

    Example:
        format_output(search_object, "csv", True, False)
    """
    dataframe = search_obj.to_pandas()

    # Label is being set regardless of return_fields. Remove if it is not in
    # the list of requested fields.
    if "label" not in search_obj.return_fields:
        dataframe = dataframe.drop(columns=["label"], errors="ignore")

    if not show_internal_columns:
        # Remove internal OpenSearch columns
        dataframe = dataframe.drop(
            columns=["__ts_timeline_id", "_id", "_index", "_source", "_type"],
            errors="ignore",
        )

    result = None
    if output_format == "text":
        result = dataframe.to_string(index=False, header=show_headers)
    elif output_format == "csv":
        result = dataframe.to_csv(index=False, header=show_headers)
    elif output_format == "json":
        result = dataframe.to_json(orient="records", lines=False)
    elif output_format == "jsonl":
        result = dataframe.to_json(orient="records", lines=True)
    elif output_format == "tabular":
        if show_headers:
            result = tabulate(
                dataframe, headers="keys", tablefmt="psql", showindex=False
            )
        else:
            result = tabulate(dataframe, tablefmt="psql", showindex=False)

    return result


def describe_query(search_obj: search.Search):
    """Displays details of a search query and its associated filter.

    Prints the query string, return fields, and formatted filter associated
    with a search object.

    Args:
        search_obj (search.Search): The search object to describe.

    Outputs:
        Text: The query string, return fields, and a formatted JSON
        representation of the query filter.

    Example:
        describe_query(my_search_object)  # Prints details of the search object.
    """
    filter_pretty = json.dumps(search_obj.query_filter, indent=2)
    click.echo(f"Query string: {search_obj.query_string}")
    click.echo(f"Return fields: {search_obj.return_fields}")
    click.echo(f"Filter: {filter_pretty}")


@click.command("search")
@click.option(
    "--query",
    "-q",
    default="*",
    help="Search query in OpenSearch query string format",
)
@click.option(
    "--time",
    "times",
    multiple=True,
    help="Datetime filter (e.g. 2020-01-01T12:00)",
)
@click.option(
    "--time-range",
    "time_ranges",
    multiple=True,
    nargs=2,
    help="Datetime range filter (e.g: 2020-01-01 2020-02-01)",
)
@click.option("--label", "labels", multiple=True, help="Filter events with label")
@click.option(
    "--header/--no-header",
    default=True,
    help="Toggle header information (default is to show)",
)
@click.option(
    "--return-fields",
    "return_fields",
    default="",
    help="What event fields to show",
)
@click.option(
    "--order",
    default="asc",
    help="Order the output (asc/desc) based on the time field",
)
@click.option(
    "--limit",
    type=int,
    default=40,
    help="Limit amount of events to show (default: 40)",
)
@click.option("--saved-search", type=int, help="Query and filter from saved search")
@click.option(
    "--describe",
    is_flag=True,
    default=False,
    help="Show the query and filter then exit",
)
@click.option(
    "--show-internal-columns",
    is_flag=True,
    default=False,
    help="Show all columns including Timesketch internal ones",
)
@click.pass_context
# pylint: disable=too-many-arguments
def search_group(
    ctx: click.Context,
    query: str,
    times: Tuple[str, ...] = (),
    time_ranges: Tuple[Tuple[str, str], ...] = (),
    labels: Tuple[str, ...] = (),
    header: bool = True,
    return_fields: str = "",
    order: str = "asc",
    limit: int = 40,
    saved_search: Optional[int] = None,
    describe: bool = False,
    show_internal_columns: bool = False,
):
    """Searches and explores events within a Timesketch sketch.

    Executes a search query against a Timesketch sketch, applying various
    filters and formatting the output.
    Supports queries using OpenSearch query string syntax, date/time filtering,
    label filtering, and saved searches.
    The output can be formatted as text, CSV, JSON, JSONL, or tabular,
    depending on the context's 'output_format' setting.

    Args:
        ctx (click.Context): The Click context object,
            containing the sketch and output format.
        query (str): The search query in OpenSearch query string format
            (default: "*").
        times (Tuple[str, ...]): Datetime filters (e.g., "2020-01-01T12:00").
        time_ranges (Tuple[Tuple[str, str], ...]): Datetime range filters
            (e.g., ("2020-01-01", "2020-02-01")).
        labels (Tuple[str, ...]): Filters events with the specified labels.
        header (bool): Toggles header information in the output (default: True).
        return_fields (str): Specifies which event fields to show.
        order (str): Orders the output ("asc" or "desc") based on the time field
            (default: "asc").
        limit (int): Limits the number of events to show (default: 40).
        saved_search (Optional[int]): Uses a saved search query and filters by its ID.
        describe (bool): Shows the query and filter details and then exits.
        show_internal_columns (bool): Shows all columns, including Timesketch
            internal ones.

    Raises:
        * If an error occurs during date parsing or if a saved search is not found.
        * If an error occurs during date parsing.

    Outputs:
        Formatted search results in the specified output format
            (text, CSV, JSON, JSONL, or tabular).
        If '--describe' is used, query details are printed instead.

    Example:
        search --query "mal" --time-range "2023-01-01" "2023-01-31" --limit 10
        search --saved-search 123 --describe
    """
    sketch = ctx.obj.sketch
    output_format = ctx.obj.output_format
    search_obj = search.Search(sketch=sketch)

    new_line = True
    if output_format == "csv":
        new_line = False

    # Construct query from saved search and return early.
    if saved_search:
        search_obj.from_saved(saved_search)
        if limit:
            search_obj.max_entries = limit
        if describe:
            describe_query(search_obj)
            return
        click.echo(
            format_output(search_obj, output_format, header, show_internal_columns),
            nl=new_line,
        )
        return

    # Construct the query from flags.
    # TODO (berggren): Add support for query DSL.
    search_obj.query_string = query

    if return_fields:
        search_obj.return_fields = return_fields

    if limit:
        search_obj.max_entries = limit

    if order == "asc":
        search_obj.order_ascending()
    elif order == "desc":
        search_obj.order_descending()

    # TODO: Add term chips.
    if time_ranges:
        for time_range in time_ranges:
            try:
                range_chip = search.DateRangeChip()
                range_chip.add_start_time(time_range[0])
                range_chip.add_end_time(time_range[1])
                search_obj.add_chip(range_chip)
            except ValueError:
                click.echo("Error parsing date (make sure it is ISO formatted)")
                sys.exit(1)

    # TODO (berggren): This should support dates like 2021-02-12 and then
    # convert to ISO format.
    if times:
        for time in times:
            try:
                range_chip = search.DateRangeChip()
                range_chip.add_start_time(time)
                range_chip.add_end_time(time)
                search_obj.add_chip(range_chip)
            except ValueError:
                click.echo("Error parsing date (make sure it is ISO formatted)")
                sys.exit(1)

    if labels:
        for label in labels:
            label_chip = search.LabelChip()
            if label == "star":
                label_chip.use_star_label()
            elif label == "comment":
                label_chip.use_comment_label()
            else:
                label_chip.label = label
            search_obj.add_chip(label_chip)

    if describe:
        describe_query(search_obj)
        return

    click.echo(
        format_output(search_obj, output_format, header, show_internal_columns),
        nl=new_line,
    )


@click.group("saved-searches")
def saved_searches_group():
    """Managed saved searches."""


@saved_searches_group.command("list")
@click.pass_context
def list_saved_searches(ctx: click.Context):
    """Lists all saved searches within the current sketch.

    Retrieves and displays a list of saved searches from the sketch, showing
    their IDs and names.

    Args:
        ctx (click.Context): The Click context object, containing the sketch.

    Outputs:
        Text: A list of saved searches, with each line showing the search ID and name.

    Example:
        saved-searches list  # Lists all saved searches in the current sketch.
    """
    sketch = ctx.obj.sketch
    for saved_search in sketch.list_saved_searches():
        click.echo(f"{saved_search.id} {saved_search.name}")


@saved_searches_group.command("describe")
@click.argument("search_id", type=int, required=True)
@click.pass_context
def describe_saved_search(ctx: click.Context, search_id: int):
    """Displays details of a specific saved search.

    Retrieves and displays the query string and filter details of a saved search,
    identified by its ID.

    Args:
        ctx (click.Context): The Click context object, containing the sketch.
        search_id (int): The ID of the saved search to describe.

    Raises:
        click.ClickException: If the specified saved search ID does not exist.

    Outputs:
        Text: The query string and formatted JSON representation of the query
        filter for the saved search.

    Example:
        saved-searches describe 123  # Describes the saved search with ID 123.
    """
    sketch = ctx.obj.sketch
    # TODO (berggren): Add support for saved search name.
    saved_search = sketch.get_saved_search(search_id=search_id)
    if not saved_search:
        click.echo("No such saved search")
        return
    filter_pretty = json.dumps(saved_search.query_filter, indent=2)
    click.echo(f"query_string: {saved_search.query_string}")
    click.echo(f"query_filter: {filter_pretty}")
