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


@click.group("sketch")
def sketch_group():
    """Manage sketch."""


@sketch_group.command("list", help="List all sketches. [text,json]")
@click.pass_context
def list_sketches(ctx):
    """List all sketches."""
    api_client = ctx.obj.api
    output = ctx.obj.output_format
    d = []

    for sketch in api_client.list_sketches():
        d.append({"id": sketch.id, "name": sketch.name})

    sketch_panda = pd.DataFrame(d, columns=["id", "name"])
    if output == "json":
        click.echo(sketch_panda.to_json(orient="records", indent=4))
    elif output == "text":
        click.echo(f"{sketch_panda.to_string(index=False)}")
    else:
        click.echo(f"Output format {output} not implemented.")
        ctx.exit(1)


@sketch_group.command(
    "describe",
    help="Describe the active sketch [text,json]. Attributes are only included in JSON output format.",
)
@click.pass_context
def describe_sketch(ctx):
    """Show info about the active sketch."""
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


@sketch_group.command("attributes", help="List all attributes [text,json].")
@click.pass_context
def list_attributes(ctx):
    """List all attributes."""
    sketch = ctx.obj.sketch

    attributes = sketch.attributes
    if not attributes:
        click.echo("No attributes found.")
        ctx.exit(1)
    if ctx.obj.output_format == "json":
        click.echo(json.dumps(attributes, sort_keys=True, default=str))
        return
    elif ctx.obj.output_format == "text":
        for k, v in attributes.items():
            click.echo(f"Name: {k}: Ontology: {v['ontology']} Value: {v['value']}")
    else:  # format not implemented use json or text instead
        click.echo(
            f"Output format {ctx.obj.output_format} not implemented. Use json or text instead."
        )


@sketch_group.command(
    "remove_attribute", help="Remove an attribute from a Sketch [text]."
)
@click.option("--name", required=True, help="Name of the attribute.")
@click.option("--ontology", required=True, help="Ontology of the attribute.")
@click.pass_context
def remove_attribute(ctx, name, ontology):
    """Remove an attribute from a sketch.

    Args:
        name: Name of the attribute.
        ontology: Ontology of the attribute.
    """
    sketch = ctx.obj.sketch
    if ctx.obj.output_format != "text":
        click.echo(
            f"Output format {ctx.obj.output_format} not implemented. Use text instead."
        )
        ctx.exit(1)
    if sketch.remove_attribute(name, ontology):
        click.echo(f"Attribute removed: Name: {name} Ontology: {ontology}")
    else:
        click.echo(f"Attribute not found: Name: {name} Ontology: {ontology}")
        ctx.exit(1)


@sketch_group.command("add_attribute", help="Add an attribute to a Sketch [text].")
@click.option("--name", required=True, help="Name of the attribute.")
@click.option("--ontology", required=True, help="Ontology of the attribute.")
@click.option("--value", required=True, help="Value of the attribute.")
@click.pass_context
def add_attribute(ctx, name, ontology, value):
    """Add an attribute to a sketch.

    Args:
        name: Name of the attribute.
        ontology: Ontology of the attribute.
        value: Value of the attribute.

    Example:
        timesketch --sketch 2 sketch add_attribute
            --name ticket_id --ontology text --value 12345

    """
    sketch = ctx.obj.sketch
    if ctx.obj.output_format != "text":
        click.echo(
            f"Output format {ctx.obj.output_format} not implemented. Use text instead."
        )
        ctx.exit(1)
    sketch.add_attribute(name, ontology, value)
    click.echo("Attribute added:")
    click.echo(f"Name: {name}")
    click.echo(f"Ontology: {ontology}")
    click.echo(f"Value: {value}")


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
