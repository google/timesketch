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


@click.group('sketch')
def sketch_group():
    """Manage sketch."""


@sketch_group.command('list')
@click.pass_context
def list_sketches(ctx):
    """List all sketches.

    Args:
        ctx: Click CLI context object.
    """
    api_client = ctx.obj.api
    for sketch in api_client.list_sketches():
        click.echo(f'{sketch.id} {sketch.name}')


@sketch_group.command('describe')
@click.pass_context
def describe_sketch(ctx):
    """Show info about a sketch.

    Args:
        ctx: Click CLI context object.
    """
    sketch = ctx.obj.sketch
    # TODO (berggren): Add more details to the output.
    click.echo(f'Name: {sketch.name}')
    click.echo(f'Description: {sketch.description}')


@sketch_group.command('create')
@click.option(
    '--name', required=True, help='Name of the sketch.')
@click.option(
    '--description', required=False,
    help='Description of the sketch (optional)')
@click.pass_context
def create_sketch(ctx, name, description):
    """Create a new sketch.

    Args:
        ctx: Click CLI context object.
        name: Name of the sketch to create.
        description: Description of the sketch to create.
    """
    api_client = ctx.obj.api
    if not description:
        description = name
    sketch = api_client.create_sketch(name=name, description=description)
    click.echo(f'Sketch created: {sketch.name}')
