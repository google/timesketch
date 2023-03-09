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
"""Commands for timelines."""

import click


@click.group("timelines")
def timelines_group():
    """Manage timelines."""


@timelines_group.command("list")
@click.pass_context
def list_timelines(ctx):
    """List all timelines in the sketch.

    Args:
        ctx: Click CLI context object.
    """
    sketch = ctx.obj.sketch
    for timeline in sketch.list_timelines():
        click.echo(f"{timeline.id} {timeline.name}")


@timelines_group.command("describe")
@click.argument("timeline_id", type=int, required=False)
@click.pass_context
def describe_timeline(ctx, timeline_id):
    """Show details for a timeline.

    Args:
        ctx: Click CLI context object.
        timeline_id: Timeline ID from argument.
    """
    sketch = ctx.obj.sketch
    # TODO (berggren): Add more details to the output, e.g. the data_sources
    timeline = sketch.get_timeline(timeline_id=timeline_id)
    if not timeline:
        click.echo("No such timeline")
        return
    click.echo(f"Name: {timeline.name}")
    click.echo(f"Index: {timeline.index_name}")


@timelines_group.command("event-add-tags")
@click.argument("timeline_id", type=int, required=False)
@click.option("--event_id", required=True, help="ID of the event.")
@click.option(
    "--tags",
    required=True,
    help="Comma seperated list of Tags to add to the event.",
)
@click.option(
    "--output-format",
    "output",
    required=False,
    help="Set output format (overrides global setting)",
)
@click.pass_context
def event_add_tags(ctx, timeline_id, event_id, tags, output):
    """Add tags to an event."""
    sketch = ctx.obj.sketch
    timeline = sketch.get_timeline(timeline_id=timeline_id)
    if not timeline:
        click.echo("No such timeline")
        return
    events = [
        {
            "_id": event_id,
            "_index": timeline.index_name,
            "_type": "generic_event",
        }
    ]
    tags_list = tags.split(",")
    return_value = sketch.tag_events(events, tags_list)
    if output == "json":
        click.echo(return_value)
    else:
        click.echo(f"Tags {tags_list} added to event {event_id}")
