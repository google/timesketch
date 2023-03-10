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
import yaml


@click.group("events")
def events_group():
    """Manage event."""


@events_group.command("annotate")
@click.option("--timeline-id", type=int, required=True)
@click.option("--event-id", required=True, help="ID of the event.")
@click.option(
    "--tags",
    required=False,
    help="Comma seperated list of Tags to add to the event.",
)
@click.option("--comments", required=False, help="Comment to add to the event.")
@click.option(
    "--output-format",
    "output",
    required=False,
    help="Set output format (overrides global setting)",
)
@click.pass_context
def annotate(ctx, timeline_id, event_id, tags, comments, output):
    """Annotate to an event.

    This can be used to add tags and comments to an event.

    If neither tags or comments are specified, the command will return the
    current annotations for the event.
    """
    sketch = ctx.obj.sketch
    # if no output format is specified, use the global one
    if not output:
        output = ctx.obj.output_format
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

    if comments:
        comment_list = comments.split(",")
        for comment in comment_list:
            sketch.comment_event(event_id, timeline.index_name, comment)

    if tags:
        tags_list = tags.split(",")
        sketch.tag_events(events, tags_list)

    return_value = sketch.get_event(event_id, timeline.index_name)

    if output == "json":
        click.echo(return_value)
    else:
        click.echo(yaml.dump(return_value))
    sys.exit(0)
