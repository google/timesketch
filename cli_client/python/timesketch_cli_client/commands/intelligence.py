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
"""Commands for interacting with intelligence within a Sketch."""

import sys
import json
from typing import Optional, Literal
import click


@click.group("intelligence")
def intelligence_group():
    """Manage intelligence within a sketch."""


@intelligence_group.command("list")
@click.option(
    "--header/--no-header",
    default=True,
    help="Include header in output. (default is to show header))",
)
@click.option(
    "--columns",
    default="ioc,type",
    help="Comma separated list of columns to show. (default: ioc,type)",
)
@click.pass_context
def list_intelligence(
    ctx: click.Context, header: Optional[bool], columns: Optional[str] = None
):
    """List all intelligence.

    Args:
        ctx (click.Context) (required): Click context object.
        header (bool) (optional): Include header in output. (default is to show header)
        columns (str) (optional): Comma separated list of columns to show.
            (default: ioc,type)
                Other options: externalURI, tags
    """

    if not columns:
        columns = "ioc,type"

    columns = columns.split(",")

    output = ctx.obj.output_format
    sketch = ctx.obj.sketch
    try:
        intelligence = sketch.get_intelligence_attribute()
    except ValueError as e:
        click.echo(e)
        sys.exit(1)

    if not intelligence:
        click.echo("No intelligence found.")
        ctx.exit(1)
    if output == "json":
        click.echo(json.dumps(intelligence, indent=4, sort_keys=True))
    elif output == "text":
        if header:
            click.echo("\t".join(columns))
        for entry in intelligence:
            row = []
            for column in columns:
                if column == "tags":
                    row.append(",".join(entry.get(column, [])))
                else:
                    row.append(entry.get(column, ""))
            click.echo("\t".join(row))
    elif output == "csv":
        if header:
            click.echo(",".join(columns))
        for entry in intelligence:
            row = []
            for column in columns:
                if column == "tags":
                    # Tags can be multiple values but they should only be
                    # one value on the csv so we join them with a comma
                    # surrounded the array by quotes
                    row.append(f'"{",".join(entry.get(column, []))}"')
                else:
                    row.append(entry.get(column, ""))
            click.echo(",".join(row))
    else:
        click.echo(f"Output format {output} not implemented.")


@intelligence_group.command("add")
@click.option(
    "--ioc",
    required=True,
    help="Indicator Of Compromise (IOC) value.",
)
@click.option(
    "--ioc-type",
    required=False,
    help="Type of the intelligence (ipv4, hash_sha256, hash_sha1, hash_md5, other).",
)
@click.option(
    "--tags",
    required=False,
    help="Comma separated list of tags.",
)
@click.pass_context
def add_intelligence(
    ctx: click.Context,
    ioc: str,
    tags: Optional[str] = None,
    ioc_type: Optional[
        Literal["ip", "domain", "url", "md5", "sha1", "sha256", "other"]
    ] = "other",
):
    """Add intelligence to a sketch.

    A sketch can have multiple intelligence entries. Each entry consists of
    an indicator, a type and a list of tags.

    Reference: https://timesketch.org/guides/user/intelligence/

    Args:
        ctx:  (click.Context) (required) Click context object.
        ioc: IOC value.
        ioc_type: Type of the intelligence. This is defined in the ontology file.
            If a string doesn't match any of the aforementioned IOC types,
            the type will fall back to other.
        tags: Comma separated list of tags.
    """
    sketch = ctx.obj.sketch

    # Create a tags dict from the comma separated list
    if tags:
        tags = tags.split(",")
        tags = {tag: [] for tag in tags}
    else:
        tags = []

    ioc_dict = {"ioc": ioc, "type": ioc_type, "tags": tags}
    # Put the ioc in a nested object to match the format of the API
    data = {"data": [ioc_dict]}
    try:
        sketch.add_attribute(name="intelligence", ontology="intelligence", value=data)
    except ValueError as e:
        click.echo(e)
        sys.exit(1)
    click.echo(f"Intelligence added: {ioc}")
