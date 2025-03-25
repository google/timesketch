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
"""Commands for sketch attributes."""

import json
import click


@click.group("attributes", help="Manage attributes of a sketch.")
def attribute_group():
    """Manage attributes of a sketch.
    This group is nested in the sketch group."""


@attribute_group.command("list", help="List all attributes.")
@click.pass_context
def list_attributes(ctx: click.Context):
    """Lists all attributes associated with the current sketch.

    Retrieves and displays a list of attributes from the current sketch.
    The output format is determined by the context's 'output_format' setting.
    Supported output formats are 'json' and 'text'.

    Args:
        ctx (click.Context): The Click context object, containing the sketch and
        output format.

    Outputs:
        JSON: If the output format is 'json', the attributes are printed as a
        JSON object.
        Text: If the output format is 'text' (or an unsupported format), the
        attributes are printed in a human-readable format, showing the name,
        ontology, and value of each attribute.
        Error message: if no attributes are found, or an unsupported output
        type is selected.

    Example:
        attribute list  # Lists all attributes for the current sketch.
    """
    sketch = ctx.obj.sketch
    output = ctx.obj.output_format
    attributes = sketch.attributes
    if not attributes:
        click.echo("No attributes found.")
        ctx.exit(1)
    if output == "json":
        click.echo(json.dumps(attributes, indent=4, sort_keys=True, default=str))
    elif output == "text":
        for k, v in attributes.items():
            click.echo(f"Name: {k}: Ontology: {v['ontology']} Value: {v['value']}")
    else:  # format not implemented use json or text instead
        click.echo(f"Output format {output} not implemented.")


@attribute_group.command("remove", help="Remove an attribute from a Sketch.")
@click.option("--name", required=True, help="Name of the attribute.")
@click.option("--ontology", required=True, help="Ontology of the attribute.")
@click.pass_context
def remove_attribute(ctx: click.Context, name: str, ontology: str):
    """Removes an attribute from the current sketch.

    Removes the attribute specified by its name and ontology from the sketch.
    The output format is forced to 'text' for this command.

    Args:
        ctx (click.Context): The Click context object, containing the sketch.
        name (str): The name of the attribute to remove.
        ontology (str): The ontology of the attribute to remove.

    Errors:
        * If the specified attribute is not found in the sketch.
        * If an unsupported output format is used.

    Outputs:
        Text: A message indicating whether the attribute was successfully
        removed or not.

    Example:
        attribute remove --name "malware_fam" --ontology "threat_intelligence"
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


@attribute_group.command("add", help="Add an attribute to a Sketch.")
@click.option("--name", required=True, help="Name of the attribute.")
@click.option("--ontology", required=True, help="Ontology of the attribute.")
@click.option("--value", required=True, help="Value of the attribute.")
@click.pass_context
def add_attribute(ctx: click.Context, name: str, ontology: str, value: str):
    """Adds an attribute to the current sketch.

    Adds an attribute with the specified name, ontology, and value to the sketch.
    The output format is forced to 'text' for this command.

    Args:
        ctx (click.Context): The Click context object, containing the sketch.
        name (str): The name of the attribute to add.
        ontology (str): The ontology of the attribute to add.
        value (str): The value of the attribute to add.

    Outputs:
        Text: A message confirming the attribute was added, including its name,
        ontology, and value.

    Example:
        attribute add --name ticket_id --ontology text --value 12345
    """
    sketch = ctx.obj.sketch
    if ctx.obj.output_format != "text":
        click.echo(f"Output format {ctx.obj.output_format} not implemented.")
        ctx.exit(1)
    sketch.add_attribute(name=name, value=value, ontology=ontology)
    click.echo("Attribute added:")
    click.echo(f"Name: {name}")
    click.echo(f"Ontology: {ontology}")
    click.echo(f"Value: {value}")
