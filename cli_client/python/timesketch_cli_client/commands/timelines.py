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
"""Commands for timelines."""

import click


@click.group('timelines')
def timelines_group():
    """Manage your timelines."""
    pass


@timelines_group.command('list')
@click.pass_context
def list_timelines(ctx):
    """List all timelines in the sketch.

    Args:
        ctx: Click CLI context object.
    """
    sketch = ctx.obj.sketch
    for timeline in sketch.list_timelines():
        click.echo('{} {}'.format(timeline.id, timeline.name))


@timelines_group.command('describe')
@click.argument('timeline_id', type=int, required=False)
@click.pass_context
def describe_timeline(ctx, timeline_id):
    """Show details for a timeline.

    Args:
        ctx: Click CLI context object.
        timeline_id: Timeline ID from argument.
    """
    sketch = ctx.obj.sketch
    timeline = sketch.get_timeline(timeline_id=timeline_id)
    if not timeline:
        click.echo('No such timeline')
        return
    click.echo('Name: {}'.format(timeline.name))
    click.echo('Index: {}'.format(timeline.index_name))
