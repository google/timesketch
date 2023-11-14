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

import json
import click
import pandas as pd

from timesketch_cli_client.commands import attribute as attribute_command


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
