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
"""Commands for analyzing timelines."""

import click
import time
import sys

from timesketch_api_client import error


def run_analyzer(sketch, analyzer, timelines):
    for timeline in timelines:
        click.echo('Running analyzer [{}] on timeline [{}]: '.format(
            analyzer, timeline.name), nl=False)
        try:
            session = sketch.run_analyzer(
                analyzer_name=analyzer, timeline_id=timeline.id)
            while True:
                status = session.status.split()[2]
                # TODO: Do something with other statuses?
                if status == 'DONE':
                    click.echo(session.results)
                    break
                time.sleep(3)
        except error.UnableToRunAnalyzer:
            sys.exit(1)


@click.group('analyze')
def analysis_group():
    """Analyze your timelines."""
    pass


@analysis_group.command('run')
@click.option(
    '--analyzer', 'analyzer_name', required=True,
    help='The name of the analyzer to run.')
@click.option(
    '--timeline', 'timeline_id', required=True,
    help='The id of the timeline you want to analyze.')
@click.pass_context
def run(ctx, analyzer_name, timeline_id):
    """Run an analyzer on one or more timelines."""
    sketch = ctx.obj.sketch
    timelines = []
    if timeline_id == 'all':
        timelines = sketch.list_timelines()
    else:
        timeline = sketch.get_timeline(timeline_id=int(timeline_id))
        timelines.append(timeline)

    run_analyzer(sketch, analyzer_name, timelines)


@analysis_group.command('list')
@click.pass_context
def list_analyzers(ctx):
    """List all available analyzers."""
    sketch = ctx.obj.sketch
    for analyzer in sketch.list_available_analyzers():
        click.echo(analyzer)
