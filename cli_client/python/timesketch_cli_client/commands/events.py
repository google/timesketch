# Copyright 2023 Google Inc. All rights reserved.
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
"""Commands for events."""

import sys
import click


@click.group("events")
def events_group():
    """Manage event."""


@events_group.command("remove_tag")
@click.option("--timeline-id", type=int, required=True)
@click.option("--event-id", required=True, help="ID of the event.")
@click.option(
    "--tag",
    required=True,
    help="Comma separated list of Tags to remove from the event.",
)
@click.pass_context
def remove_tag(ctx, timeline_id, event_id, tag):
    """Remove a tag from an event."""
    sketch = ctx.obj.sketch
    timeline = sketch.get_timeline(timeline_id=timeline_id)
    if not timeline:
        click.echo("No such timeline.")
        return

    events = [
        {
            "_id": event_id,
            "_index": timeline.index_name,
            "_type": "generic_event",
        }
    ]

    tags = tag.split(",")
    sketch.untag_events(events, tags)


@events_group.command("annotate")
@click.option("--timeline-id", type=int, required=True)
@click.option("--event-id", required=True, help="ID of the event.")
@click.option(
    "--tag",
    required=False,
    help="Comma separated list of Tags to add to the event.",
)
@click.option("--comment", required=False, help="Comment to add to the event.")
# TODO(jaegeral): Make this part of the root command as we do with sketch-id
@click.option(
    "--output-format",
    "output",
    required=False,
    help="Set output format (overrides global setting).",
)
@click.pass_context
def annotate(ctx, timeline_id, event_id, tag, comment, output):
    """Annotate to an event.

    This can be used to add tags and comments to an event.

    If neither tag or comment are specified, the command will return the
    current annotations for the event.
    """
    sketch = ctx.obj.sketch
    # If no output format is specified, use the global one.
    if not output:
        output = ctx.obj.output_format
    timeline = sketch.get_timeline(timeline_id=timeline_id)
    if not timeline:
        click.echo("No such timeline.")
        return

    if not tag and not comment:
        click.echo("No tag or comment specified.")
        return

    events = [
        {
            "_id": event_id,
            "_index": timeline.index_name,
            "_type": "generic_event",
        }
    ]

    if comment:
        comments = comment.split(",")
        for _commment in comments:
            sketch.comment_event(event_id, timeline.index_name, _commment)

    if tag:
        tags = tag.split(",")
        sketch.tag_events(events, tags)

    try:
        return_value = sketch.get_event(event_id, timeline.index_name)
        if return_value is None:
            click.echo("No such event.")
            sys.exit(1)
    except KeyError:
        click.echo("No such event.")
        sys.exit(1)

    # TODO: At the moment json is only really supported here. Add more options
    # as needed (like YAML).
    click.echo(return_value)
