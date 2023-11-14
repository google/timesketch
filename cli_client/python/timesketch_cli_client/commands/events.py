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


@events_group.command("annotate")
@click.option("--timeline-id", type=int, required=True)
@click.option("--event-id", required=True, help="ID of the event.")
@click.option(
    "--tag",
    required=False,
    help="Comma separated list of Tags to add to the event.",
)
@click.option("--comment", required=False, help="Comment to add to the event.")
@click.pass_context
def annotate(ctx, timeline_id, event_id, tag, comment):
    """Annotate to an event.

    This can be used to add tags and comments to an event.

    If neither tag or comment are specified, the command will return the
    current annotations for the event.
    """
    sketch = ctx.obj.sketch
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


@events_group.command("add")
@click.option("--message", required=True, help="Message of the event.")
@click.option(
    "--date",
    required=True,
    help="Date of the event (ISO 8601). Example: 2023-03-08T10:59:24+00:00",
)
@click.option(
    "--attributes",
    required=False,
    help="Attributes of the event. Example: key1=value1,key2=value2",
)
@click.option(
    "--timestamp-desc",
    required=True,
    help="Timestamp description of the event.",
)
@click.pass_context
def add_event(ctx, message, date, attributes, timestamp_desc):
    """Add an event to the sketch."""
    sketch = ctx.obj.sketch
    output = ctx.obj.output_format

    attributes_dict = {}
    if attributes:
        attributes_comma_split = attributes.split(",")

        for attribute in attributes_comma_split:
            key, value = attribute.split("=")
            attributes_dict[key] = value
    try:
        return_value = sketch.add_event(
            message=message,
            date=date,
            timestamp_desc=timestamp_desc,
            attributes=attributes_dict,
        )
    except ValueError as e:
        click.echo(f"Problem adding event to sketch: {e}")
        sys.exit(1)

    # TODO (jaegeral): Add more details to the output (e.g. event id, which
    # is currently not passed back by the API).
    if output == "json":
        click.echo(f"{return_value}")
    else:
        click.echo(f"Event added to sketch: {sketch.name}")


@events_group.command("remove_tag")
@click.option("--timeline-id", type=int, required=True)
@click.option("--event-id", required=True, help="ID of the event.")
@click.option(
    "--tag",
    required=False,
    help="Tag to remove from the event.",
)
@click.pass_context
def tag_mod(ctx, timeline_id, event_id, tag):
    """Remove a Tag from a event.

    This can be used to remove a tag from an event.

    If no tag is specified, the command will return the
    current tags for the event.

    Args:
        ctx: Click context object.
        timeline_id: The ID of the timeline.
        event_id: The ID of the event.
        tag: The tag to remove from the event.

    Returns:
        HTTP response from the API server.

    Raises:
        KeyError: If the event does not exist.
    """
    sketch = ctx.obj.sketch
    timeline = sketch.get_timeline(timeline_id=timeline_id)
    if not timeline:
        click.echo("No such timeline.")
        return

    if tag:
        # if tag is a string with commas, make it a list
        if "," in tag:
            tags = tag.split(",")
            return_value = sketch.untag_events([event_id], timeline.index_name, tags)
        else:
            return_value = sketch.untag_event(event_id, timeline.index_name, tag)
            click.echo(return_value)
    else:  # just get the event
        try:
            return_value = sketch.get_event(event_id, timeline.index_name)
            if return_value is None:
                click.echo("No such event.")
                sys.exit(1)
        except KeyError:
            click.echo("No such event.")
            sys.exit(1)
