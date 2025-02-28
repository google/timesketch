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


@sketch_group.command(
    "delete", help="Delete a sketch, default will only mark the sketch as deleted"
)
@click.option(
    "--force_delete",
    required=False,
    is_flag=True,
    help="Only execute the deletion if this is set.",
)
@click.option(
    "--delete_metadata",
    required=False,
    is_flag=True,
    help="Delete metadata associated with the sketch.",
)
@click.pass_context
def delete_sketch(ctx, force_delete, delete_metadata):
    """Delete a sketch.

    By default, a sketch will not be deleted. To execute the deletion provide the
    flag --execute.

    To also delete the metadata to a sketch, provide the flag --delete_metadata.

    Args:
        execute: Only execute the deletion if this is set.
        delete_metadata: Delete metadata associated with the sketch.
    """
    sketch = ctx.obj.sketch

    # check if sketch exists
    if not sketch:
        click.echo("Error Sketch does not exist")
        ctx.exit(1)

    # if sketch is archived, exit
    if sketch.is_archived():
        click.echo("Error Sketch is archived")
        ctx.exit(1)

    # Dryrun:
    click.echo("Would delete the following things")
    click.echo(
        f"Sketch: {sketch.id} {sketch.name} {sketch.description} {sketch.status} Labels: {sketch.labels}"  # pylint: disable=line-too-long
    )

    for timeline in sketch.list_timelines():
        click.echo(
            f"  Timeline: {timeline.id} {timeline.name} {timeline.description} {timeline.status}"  # pylint: disable=line-too-long
        )

    # for story in sketch.stories:
    #    click.echo(
    #        f"  Story: {story.id} {story.title} {story.description} {story.status} {story.created_at} {story.updated_at}" # pylint: disable=line-too-long
    #    )

    if force_delete:
        click.echo("Will delete for real")
        # breakpoint()
        # sketch.delete()
        sketch.z_delete(force_delete=force_delete)
        click.echo("Sketch deleted")
