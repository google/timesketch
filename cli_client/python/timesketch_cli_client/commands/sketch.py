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
from typing import Optional
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
def list_sketches(ctx: click.Context):
    """List all sketches from the API.

    Retrieves a list of sketches from the API associated with the given context.
    The output is formatted based on the 'output_format' setting within the
    context's object.
    Supported output formats are 'json' and 'text'.

    Args:
        ctx (click.Context): The Click context object, containing the API
        client and output format.

    Raises:
        click.exceptions.Exit: If an unsupported output format is specified.

    Outputs:
        JSON: If the output format is 'json', a JSON representation is printed.
        Text: If the output format is 'text', a formatted table is printed.
        Error message: If an unsupported output format is specified
    """
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
def describe_sketch(ctx: click.Context) -> None:
    """Displays details of the active sketch.

    Displays the name, description, and status of the active sketch.
    If the output format is 'json', all sketch attributes are displayed.

    Args:
        ctx (click.Context): The Click context object, containing the sketch
        and output format.

    Raises:
        * If an unsupported output format is specified.

    Outputs:
        Text: The name, description, and status of the sketch.
        JSON: All attributes of the sketch object.
        Error message: if the output format is not text or json.

    Example:
        sketch describe  # Displays details of the active sketch.
    """
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
def create_sketch(
    ctx: click.Context, name: str, description: Optional[str] = None
) -> None:
    """Creates a new sketch.

    Creates a new Timesketch sketch with the specified name and optional description.

    Args:
        ctx (click.Context): The Click context object, containing the API client.
        name (str): The name of the new sketch.
        description (Optional[str]): The description of the new sketch
            (defaults to the name if not provided).

    Outputs:
        Text: A message confirming the sketch creation and its name.

    Example:
        sketch create --name "My New Sketch" --description "Analysis of incident X"
    """
    api_client = ctx.obj.api
    if not description:
        description = name
    sketch = api_client.create_sketch(name=name, description=description)
    click.echo(f"Sketch created: {sketch.name}")


@sketch_group.command("export", help="Export a sketch")
@click.option("--filename", required=True, help="Filename to export to.")
@click.pass_context
def export_sketch(ctx: click.Context, filename: str) -> None:
    """Export a sketch to a file.

    Exports all events within the active sketch to a specified file.
    The export process can take a significant amount of time depending on the
    sketch size.

    Args:
        ctx (click.Context): The Click context object, containing the sketch.
        filename (str): The name of the file to export the sketch data to.

    Raises:
        click.exceptions.Exit: If a ValueError occurs during the export process.

    Outputs:
        Text: Messages indicating the start, progress, and completion of the
            export process, including the time taken.
        Error message: If a ValueError occurs during export.
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
def archive_sketch(ctx: click.Context) -> None:
    """Archive a sketch.

    Archives the active sketch, making it read-only and preventing further
    modifications.

    Args:
        ctx (click.Context): The Click context object, containing the sketch.

    Raises:
        click.exceptions.Exit: If the sketch is already archived or the user
        lacks permissions to archive it.

    Outputs:
        Text: A message indicating whether the sketch was successfully archived.
        Error message: If the sketch is already archived or the user lacks permissions.
    """
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
def unarchive_sketch(ctx: click.Context) -> None:
    """Unarchive a sketch.

    Unarchives a previously archived sketch, allowing modifications to be made again.

    Args:
        ctx (click.Context): The Click context object, containing the sketch.

    Raises:
        click.exceptions.Exit: If the sketch is not archived.

    Outputs:
        Text: A message indicating whether the sketch was successfully unarchived.
        Error message: If the sketch is not archived.
    """
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
def add_label(ctx: click.Context, label: str) -> None:
    """Add a label to a sketch.

    Adds a specified label to the active sketch. Labels can be used to
    categorize and organize sketches.

    Args:
        ctx (click.Context): The Click context object, containing the sketch.
        label (str): The label to add.

    Outputs:
        Text: A message indicating that the label was added.
    """
    sketch = ctx.obj.sketch
    sketch.add_sketch_label(label)
    click.echo("Label added")


@sketch_group.command("list_label", help="List labels of sketch")
@click.pass_context
def list_label(ctx: click.Context) -> None:
    """List labels of a sketch.

    Lists all labels currently associated with the active sketch.

    Args:
        ctx (click.Context): The Click context object, containing the sketch.

    Outputs:
        Text: A list of labels associated with the sketch.
    """
    sketch = ctx.obj.sketch
    click.echo(sketch.labels)


@sketch_group.command("remove_label", help="Remove a label from a sketch")
@click.option("--label", required=True, help="Name of label to remove.")
@click.pass_context
def remove_label(ctx: click.Context, label: str) -> None:
    """Remove a label from a sketch.

    Removes a specified label from the active sketch.

    Args:
        ctx (click.Context): The Click context object, containing the sketch.
        label (str): The label to remove.

    Outputs:
        Text: A message indicating that the label was removed.
    """
    sketch = ctx.obj.sketch
    sketch.remove_sketch_label(label)
    click.echo("Label removed.")
