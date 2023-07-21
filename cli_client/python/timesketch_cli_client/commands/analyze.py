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
"""Commands for analyzing timelines."""
import sys
import time

import json
import click

from timesketch_api_client import error


@click.group("analyze")
def analysis_group():
    """Analyze timelines."""


# TODO (berggren) Add --timeline-name as well, to select timeline based on name
# instead of ID.
@analysis_group.command("run")
@click.option(
    "--analyzer",
    "analyzer_name",
    required=True,
    help="The name of the analyzer to run.",
)
@click.option(
    "--timeline",
    "timeline_id",
    required=True,
    help="The id of the timeline you want to analyze.",
)
@click.pass_context
def run_analyzer(ctx, analyzer_name, timeline_id):
    """Run an analyzer on one or more timelines.

    Args:
        ctx: Click CLI context object.
        analyzer_name: Name of the analyzer to run.
        timeline_id: Timeline ID of the timeline to analyze.
    """
    sketch = ctx.obj.sketch
    timelines = []
    if timeline_id == "all":
        timelines = sketch.list_timelines()
    else:
        timeline = sketch.get_timeline(timeline_id=int(timeline_id))
        timelines.append(timeline)

    for timeline in timelines:
        try:
            # TODO: Add support for running multiple analyzers.
            # TODO: Make progress pretty
            sessions = timeline.run_analyzer(analyzer_name, ignore_previous=True)
            session_statuses = sessions[0].status_dict
            total_tasks = len(session_statuses.values())

            for analyzer, _ in session_statuses.items():
                click.echo(f"Running analyzer [{analyzer}] on [{timeline.name}]:")

            while True:
                # Count all analysis tasks that has the status DONE
                completed_tasks = len(
                    [x[0] for x in sessions[0].status_dict.values() if x[0] == "DONE"]
                )
                if completed_tasks == total_tasks:
                    click.echo("\nResults")
                    click.echo(sessions[0].results)
                    break
                click.echo(".", nl=False)
                time.sleep(3)
        except error.UnableToRunAnalyzer as e:
            click.echo(f"Unable to run analyzer: {e}")
            sys.exit(1)


@analysis_group.command("list")
@click.pass_context
def list_analyzers(ctx):
    """List all available analyzers.

    Args:
        ctx: Click CLI context object.
        output-format: Output format to use. Available values:
            'json','text' or 'tabular'
    """
    sketch = ctx.obj.sketch
    output = ctx.obj.output_format
    # Show header row if output is tabular
    if output == "tabular":
        click.echo("Name\tDisplay Name\tIs Multi")

    analyzers = sketch.list_available_analyzers()
    if output == "json":
        click.echo(f"{analyzers}")
        return

    for analyzer in analyzers:
        if output == "tabular":
            click.echo(
                f"{analyzer.get('name')}\t"
                f"{analyzer.get('display_name')}\t"
                f"{analyzer.get('is_multi')}"
            )
            continue
        click.echo(analyzer.get("name"))


@analysis_group.command(
    "results",
    help="Show the results of an analyzer run on a specific timeline.",
)
@click.option(
    "--analyzer",
    "analyzer_name",
    required=True,
    help="The name of the analyzer that was run.",
)
@click.option(
    "--timeline",
    "timeline_id",
    required=True,
    help="The id of the timeline that was analyzed.",
)
# boolean flag show_dependent
@click.option(
    "--show-dependent",
    "show_dependent",
    required=False,
    default=False,
    is_flag=True,
    help="Show the results of an analyzer run dependent from the original one.",
)
@click.pass_context
def analyzer_results(ctx, analyzer_name, timeline_id, show_dependent):
    """Show the results of an analyzer run on one or more timelines.

    Args:
        ctx: Click CLI context object.
        analyzer_name: Name of the analyzer that was run.
        timeline_id: Timeline ID of the timeline to analyze.
        show_dependent: Show dependent analyzers. (default: False)
            using output_format json will always include the dependent analyzers
    """
    sketch = ctx.obj.sketch
    output = ctx.obj.output_format

    if output not in ("json", "text"):
        click.echo(f"Unsupported output format: [{output}] use [json / text]")
        sys.exit(1)

    timelines = []
    if timeline_id == "all":
        timelines = sketch.list_timelines()
    else:
        timeline = sketch.get_timeline(timeline_id=int(timeline_id))
        timelines.append(timeline)

    for timeline in timelines:
        try:
            sketch_analyzer_results = sketch.get_analyzer_status()
            if output == "json":
                click.echo(
                    json.dumps(
                        sketch_analyzer_results,
                        indent=4,
                        sort_keys=True,
                        default=str,
                    )
                )
            else:
                click.echo(
                    f"Results for analyzer [{analyzer_name}] on [{timeline.name}]:"
                )
                for analyzer in sketch_analyzer_results:
                    if analyzer.get("timeline_id") == int(timeline_id):
                        # find analyzer results using the verbose schema
                        try:
                            # the following will only work for verbose schema
                            analyzer_json = json.loads(analyzer.get("results"))
                            status = analyzer_json.get("result_status")
                            result_priority = analyzer_json.get("result_priority")
                            result_summary = analyzer_json.get("result_summary")
                        except json.decoder.JSONDecodeError:
                            # set values for non verbose
                            status = analyzer.get("status")
                            result_priority = analyzer.get("result_priority")
                            result_summary = analyzer.get("results")

                        if analyzer.get("analyzer") == analyzer_name:
                            click.echo(
                                f"{status} - {result_priority} - {result_summary}"
                            )
                        else:
                            # TODO(jaegeral) consider sorting to show the root
                            # analyzer first
                            if show_dependent:
                                click.echo(
                                    f"Dependent: {status} - {result_priority} \
                                          - {result_summary}"
                                )
        except Exception as e:  # pylint: disable=broad-except
            click.echo(
                f"Unable to get results for analyzer [{analyzer_name}]  \
                    on [{timeline.name}]: {e}"
            )
            sys.exit(1)
