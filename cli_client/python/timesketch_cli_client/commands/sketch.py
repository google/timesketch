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
"""Commands for sketches."""

import click


@click.group("sketch")
def sketch_group():
    """Manage sketch."""


@sketch_group.command("list")
@click.pass_context
def list_sketches(ctx):
    """List all sketches."""
    api_client = ctx.obj.api
    for sketch in api_client.list_sketches():
        click.echo(f"{sketch.id} {sketch.name}")


@sketch_group.command("describe")
@click.pass_context
def describe_sketch(ctx):
    """Show info about the active sketch."""
    sketch = ctx.obj.sketch
    # TODO (berggren): Add more details to the output.
    click.echo(f"Name: {sketch.name}")
    click.echo(f"Description: {sketch.description}")


@sketch_group.command("create")
@click.option("--name", required=True, help="Name of the sketch.")
@click.option(
    "--description",
    required=False,
    help="Description of the sketch (optional)",
)
@click.pass_context
def create_sketch(ctx, name, description):
    """Create a new sketch."""
    api_client = ctx.obj.api
    if not description:
        description = name
    sketch = api_client.create_sketch(name=name, description=description)
    click.echo(f"Sketch created: {sketch.name}")


@sketch_group.command("add_event")
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
    "--timestamp_desc",
    required=True,
    help="Timestamp description of the event.",
)
@click.pass_context
def add_event(ctx, message, date, attributes, timestamp_desc):
    """Add an event to the sketch."""
    sketch = ctx.obj.sketch

    if attributes:
        attributes_comma_split = attributes.split(",")
        attributes_dict = {}
        for attribute in attributes_comma_split:
            key, value = attribute.split("=")
            attributes_dict[key] = value
    if not attributes_dict:
        attributes_dict = {}
    sketch.add_event(
        message=message,
        date=date,
        timestamp_desc=timestamp_desc,
        attributes=attributes_dict,
    )
    # TODO (jaegeral): Add more details to the output (e.g. event id, which
    # is currently not passed back by the API).
    click.echo(f"Event added to sketch: {sketch.name}")
