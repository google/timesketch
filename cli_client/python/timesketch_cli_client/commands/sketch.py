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

import time
import json
import click
import pandas as pd

from timesketch_cli_client.commands import attribute as attribute_command
from timesketch_api_client import search


@click.group("sketch")
def sketch_group():
    """Manage sketch."""


# Add the attribute command group to the sketch command group.
sketch_group.add_command(attribute_command.attribute_group)


@sketch_group.command("list", help="List all sketches.")
@click.pass_context
def list_sketches(ctx):
    """List all sketches."""
    api_client = ctx.obj.api
    output = ctx.obj.output_format
    sketches = []

    for sketch in api_client.list_sketches():
        sketches.append({"id": sketch.id, "name": sketch.name})

    sketch_panda = pd.DataFrame(sketches, columns=["id", "name"])
    if output == "json":
        click.echo(sketch_panda.to_json(orient="records", indent=4))
    elif output == "text":
        click.echo(f"{sketch_panda.to_string(index=False)}")
    else:
        click.echo(f"Output format {output} not implemented.")
        ctx.exit(1)


@sketch_group.command(
    "describe",
    help="Describe the active sketch",
)
@click.pass_context
def describe_sketch(ctx):
    """Describe the active sketch.
    Attributes only in JSON output format."""
    sketch = ctx.obj.sketch
    output = ctx.obj.output_format

    if output == "json":
        click.echo(json.dumps(sketch.__dict__, indent=4, sort_keys=True, default=str))
        return
    if output == "text":
        click.echo(f"Name: {sketch.name}")
        click.echo(f"Description: {sketch.description}")
        click.echo(f"Status: {sketch.status}")
    else:
        click.echo(f"Output format {output} not implemented.")
        ctx.exit(1)


@sketch_group.command("create", help="Create a new sketch [text].")
@click.option("--name", required=True, help="Name of the sketch.")
@click.option(
    "--description",
    required=False,
    help="Description of the sketch (optional).",
)
@click.pass_context
def create_sketch(ctx, name, description):
    """Create a new sketch.

    Args:
        name: Name of the sketch.
        description: Description of the sketch (optional).
    """
    api_client = ctx.obj.api
    if not description:
        description = name
    sketch = api_client.create_sketch(name=name, description=description)
    click.echo(f"Sketch created: {sketch.name}")


@sketch_group.command("export", help="Export a sketch")
@click.option("--filename", required=True, help="Filename to export to.")
@click.pass_context
def export_sketch(ctx, filename):
    """Export a sketch to a file.

    Args:
        filename: Filename to create
    """
    sketch = ctx.obj.sketch
    click.echo("Executing export . . . ")
    click.echo("Depending on the sketch size, this can take a while")
    # start counting the time the export took
    start_time = time.time()
    try:
        search_obj = search.Search(sketch=sketch)

        click.echo(f"Number of events in that sketch: {search_obj.expected_size}")

        search_obj.to_file(filename)
        # Using the sketch.export function could be an alternative here
        # TODO: https://github.com/google/timesketch/issues/2344
        end_time = time.time()
        click.echo(f"Export took {end_time - start_time} seconds")
        click.echo("Finish")
    except ValueError as e:
        click.echo(f"Error: {e}")
        ctx.exit(1)


@sketch_group.command("archive", help="Archive a sketch")
@click.pass_context
def archive_sketch(ctx):
    """Archive a sketch."""
    sketch = ctx.obj.sketch
    # if sketch is already archived error
    if sketch.is_archived():
        click.echo("Error Sketch is already archived")
        ctx.exit(1)

    # check if user has permissions
    if not sketch.can_archive():
        click.echo("User can not archive this sketch")
        ctx.exit(1)

    sketch.archive()
    click.echo("Sketch archived")


@sketch_group.command("unarchive", help="Unarchive a sketch")
@click.pass_context
def unarchive_sketch(ctx):
    """Unarchive a sketch."""
    sketch = ctx.obj.sketch
    # if sketch is not archived error
    if not sketch.is_archived():
        click.echo("Error Sketch is not archived")
        ctx.exit(1)
    if sketch.is_archived():
        sketch.unarchive()
        click.echo("Sketch unarchived")


@sketch_group.command("add_label", help="Add a label to a sketch")
@click.option("--label", required=True, help="Name of label to add.")
@click.pass_context
def add_label(ctx, label):
    """Add a label to a sketch."""
    sketch = ctx.obj.sketch
    sketch.add_sketch_label(label)
    click.echo("Label added")


@sketch_group.command("list_label", help="List labels of sketch")
@click.pass_context
def list_label(ctx):
    """List labels of a sketch."""
    sketch = ctx.obj.sketch
    click.echo(sketch.labels)


@sketch_group.command("remove_label", help="Remove a label from a sketch")
@click.option("--label", required=True, help="Name of label to remove.")
@click.pass_context
def remove_label(ctx, label):
    """Remove a label from a sketch."""
    sketch = ctx.obj.sketch
    sketch.remove_sketch_label(label)
    click.echo("Label removed.")
