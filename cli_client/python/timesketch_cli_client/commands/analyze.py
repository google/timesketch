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

import click

from timesketch_api_client import error


@click.group('analyze')
def analysis_group():
    """Analyze timelines."""


# TODO (berggren) Add --timeline-name as well, to select timeline based on name
# instead of ID.
@analysis_group.command('run')
@click.option(
    '--analyzer', 'analyzer_name', required=True,
    help='The name of the analyzer to run.')
@click.option(
    '--timeline', 'timeline_id', required=True,
    help='The id of the timeline you want to analyze.')
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
    if timeline_id == 'all':
        timelines = sketch.list_timelines()
    else:
        timeline = sketch.get_timeline(timeline_id=int(timeline_id))
        timelines.append(timeline)

    for timeline in timelines:
        try:
            # TODO: Add support for running multiple analyzers.
            # TODO: Make progress pretty
            sessions = timeline.run_analyzer(
                analyzer_name, ignore_previous=True)
            session_statuses = sessions[0].status_dict
            total_tasks = len(session_statuses.values())

            for analyzer, _ in session_statuses.items():
                click.echo(
                    f'Running analyzer [{analyzer}] on [{timeline.name}]:')

            while True:
                # Count all analysis tasks that has the status DONE
                completed_tasks = len(
                    [
                        x[0] for x in sessions[0].status_dict.values()
                        if x[0] == 'DONE'
                    ]
                )
                if completed_tasks == total_tasks:
                    click.echo('\nResults')
                    click.echo(sessions[0].results)
                    break
                click.echo('.', nl=False)
                time.sleep(3)
        except error.UnableToRunAnalyzer as e:
            click.echo(f'Unable to run analyzer: {e}')
            sys.exit(1)


@analysis_group.command('list')
@click.pass_context
def list_analyzers(ctx):
    """List all available analyzers.

    Args:
        ctx: Click CLI context object.
    """
    sketch = ctx.obj.sketch
    for analyzer in sketch.list_available_analyzers():
        click.echo(analyzer)
