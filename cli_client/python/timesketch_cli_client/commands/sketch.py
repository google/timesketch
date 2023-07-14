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


@sketch_group.command(
    "describe", help="Describe the active sketch. Attributes are not included."
)
@click.pass_context
def describe_sketch(ctx):
    """Show info about the active sketch."""
    sketch = ctx.obj.sketch
    output = ctx.obj.output_format

    if output == "json":
        click.echo(sketch.__dict__)
        return
    click.echo(f"Name: {sketch.name}")
    click.echo(f"Description: {sketch.description}")
    click.echo(f"Status: {sketch.status}")


@sketch_group.command("attributes")
@click.pass_context
def list_attributes(ctx):
    """List all attributes."""
    sketch = ctx.obj.sketch

    attributes = sketch.attributes
    click.echo(attributes)


@sketch_group.command("remove_attribute")
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
    sketch.remove_attribute(name, ontology)
    click.echo(f"Attribute removed: {name} {ontology}")


@sketch_group.command("add_attribute")
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
    sketch.add_attribute(name, ontology, value)
    click.echo(f"Attribute added: {name} {ontology} {value}")


@sketch_group.command("create")
@click.option("--name", required=True, help="Name of the sketch.")
@click.option(
    "--description",
    required=False,
    help="Description of the sketch (optional).",
)
@click.pass_context
def create_sketch(ctx, name, description):
    """Create a new sketch."""
    api_client = ctx.obj.api
    if not description:
        description = name
    sketch = api_client.create_sketch(name=name, description=description)
    click.echo(f"Sketch created: {sketch.name}")
