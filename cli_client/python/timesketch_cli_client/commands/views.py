# Copyright 2020 Google Inc. All rights reserved.
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
"""Commands for saved views."""

import click
import json


@click.group('views')
def views_group():
    """Managed saved views."""
    pass


@views_group.command('list')
@click.pass_context
def list_views(ctx):
    """List saved views in the sketch."""
    sketch = ctx.obj.sketch
    for view in sketch.list_views():
        click.echo('{} {}'.format(view.id, view.name))


@views_group.command('describe')
@click.argument('view_id', type=int, required=False)
@click.pass_context
def describe(ctx, view_id):
    """Show details for a view."""
    sketch = ctx.obj.sketch
    view = sketch.get_view(view_id=view_id)
    if not view:
        click.echo('No such view')
        return
    click.echo('query_string: {}'.format(view.query_string))
    click.echo('query_filter: {}'.format(
        json.dumps(view.query_filter, indent=2)))
