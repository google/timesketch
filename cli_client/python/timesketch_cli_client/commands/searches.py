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
"""Commands for saved searches."""

import click
import json


@click.group('searches')
def saved_searches_group():
    """Managed saved searches."""
    pass


@saved_searches_group.command('list')
@click.pass_context
def list_saved_searches(ctx):
    """List saved searches in the sketch.

    Args:
        ctx: Click CLI context object.
    """
    sketch = ctx.obj.sketch
    for saved_search in sketch.list_views():
        click.echo('{} {}'.format(saved_search.id, saved_search.name))


@saved_searches_group.command('describe')
@click.argument('search_id', type=int, required=False)
@click.pass_context
def describe_saved_search(ctx, search_id):
    """Show details for a view.

    Args:
        ctx: Click CLI context object.
        search_id: View ID from argument.
    """
    sketch = ctx.obj.sketch
    saved_search = sketch.get_view(view_id=search_id)
    if not saved_search:
        click.echo('No such view')
        return
    click.echo('query_string: {}'.format(saved_search.query_string))
    click.echo('query_filter: {}'.format(
        json.dumps(saved_search.query_filter, indent=2)))
