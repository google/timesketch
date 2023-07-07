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
"""Commands for timelines."""

import click


@click.group("timelines")
def timelines_group():
    """Manage timelines."""


@timelines_group.command("list")
@click.pass_context
def list_timelines(ctx):
    """List all timelines in the sketch.

    Args:
        ctx: Click CLI context object.
    """
    sketch = ctx.obj.sketch
    for timeline in sketch.list_timelines():
        click.echo(f"{timeline.id} {timeline.name}")


@timelines_group.command("describe")
@click.argument("timeline-id", type=int, required=False)
@click.pass_context
def describe_timeline(ctx, timeline_id):
    """Show details for a timeline.

    Args:
        ctx: Click CLI context object.
        timeline-id: Timeline ID from argument.
    """
    sketch = ctx.obj.sketch
    output = ctx.obj.output_format
    timeline = sketch.get_timeline(timeline_id=timeline_id)
    if not timeline:
        click.echo("No such timeline")
        return
    timeline.lazyload_data()
    if output == "json":
        click.echo(f"{timeline.resource_data}")
        return
    if output != "text":
        click.echo(f'Unsupported output format: "{output}" - using "text" instead')

    click.echo(f"Name: {timeline.name}")
    click.echo(f"Index: {timeline.index_name}")
    click.echo(f"Status: {timeline.status}")
    lines_indexed = timeline.resource_data.get("meta").get("lines_indexed", 0)
    click.echo(f"Event count: {lines_indexed or 0}")

    for timeline_object in timeline.resource_data.get("objects", None):
        name = timeline_object.get("name", "no name")
        created = timeline_object.get("created_at", 0)
        click.echo(f"Name: {name}")
        click.echo(f"Created: {created}")
        click.echo("Datasources:")
        for datasource in timeline_object.get("datasources", []):
            error_message = datasource.get("error_message", None)
            original_filename = datasource.get("original_filename", None)
            file_on_disk = datasource.get("file_on_disk", None)

            click.echo(f"\tOriginal filename: {original_filename}")
            click.echo(f"\tFile on disk: {file_on_disk}")
            click.echo(f"\tError: {error_message}")
