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
def list_timelines(ctx: click.Context):
    """List all timelines in the sketch.

    Args:
        ctx (click.Context): Click CLI context object.
    """
    sketch = ctx.obj.sketch
    for timeline in sketch.list_timelines():
        click.echo(f"{timeline.id} {timeline.name}")


@timelines_group.command("describe")
@click.argument("timeline-id", type=int, required=True)
@click.pass_context
def describe_timeline(ctx: click.Context, timeline_id: int):
    """Displays detailed information about a timeline.

    Retrieves and displays details about a timeline within the current sketch,
    including its name, index, status, event count, color, fields, and
    associated datasources.
    The output format is determined by the context's 'output_format' setting.
    Supported output formats are 'json' and 'text'.

    Args:
        ctx (click.Context): The Click context object, containing the sketch
            and output format.
        timeline_id (int): The ID of the timeline to describe.

    Outputs:
        JSON: If the output format is 'json', the timeline's resource data
            is printed as JSON.
        Text: If the output format is 'text' (or an unsupported format),
            detailed information about the timeline is printed in a
            human-readable format.
        Error message: if the timeline id is not found.

    Example:
        timeline describe 1  # Displays details for timeline 1.
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
    click.echo(f"Color: {timeline.color}")
    click.echo(f"Number of fields: {len(timeline.index.fields)}")

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


@timelines_group.command("rename")
@click.argument("timeline-id", type=int, required=True)
@click.argument("new-name", type=str, required=True)
@click.pass_context
def rename_timeline(ctx: click.Context, timeline_id: int, new_name: str):
    """Renames a timeline within the current sketch.

    The timeline is identified by its integer ID, and its name is changed to
    the provided new name.
    The output format is determined by the context's 'output_format' setting.
    Supported output formats are 'json' and 'text'.

    Args:
        ctx (click.Context): The Click context object, containing the
            sketch and output format.
        timeline_id (int): The ID of the timeline to rename.
        new_name (str): The new name for the timeline.

    Outputs:
        JSON: If the output format is 'json', the timeline's resource data is
            printed as JSON.
        Text: If the output format is 'text' (or an unsupported format),
            the new timeline name is printed.
        Error message: if the timeline id is not found.

    Example:
        timeline rename 1 "New Timeline Name"  # Renames timeline 1.
    """
    sketch = ctx.obj.sketch
    output = ctx.obj.output_format
    timeline = sketch.get_timeline(timeline_id=timeline_id)
    if not timeline:
        click.echo("No such timeline")
        return
    timeline.lazyload_data()

    # Set new name
    timeline.name = new_name

    # Print output depending on output settings
    if output == "json":
        click.echo(f"{timeline.resource_data}")
        return
    if output != "text":
        click.echo(f'Unsupported output format: "{output}" - using "text" instead')
    else:
        click.echo(f"New name: {timeline.name}")


@timelines_group.command("delete")
@click.argument("timeline-id", type=int, required=True)
@click.pass_context
def delete_timeline(ctx: click.Context, timeline_id: int):
    """Delete a timeline.
    (Will mark a timeline as deleted, but the Opensearch Index will remain)

    Args:
        ctx (click.Context) (required): Click CLI context object.
        timeline_id (int) (required): Timeline ID from argument to be deleted.
    """
    sketch = ctx.obj.sketch
    timeline = sketch.get_timeline(timeline_id=timeline_id)
    if not timeline:
        click.echo("No such timeline")
        return
    timeline.lazyload_data()
    if click.confirm(
        f"Confirm to mark the timeline deleted:{timeline_id} {timeline.name}?"
    ):
        timeline.delete()

    click.echo("Deleted")
    return


@timelines_group.command("color")
@click.argument("timeline-id", type=int, required=True)
@click.argument("color", type=str, required=True)
@click.pass_context
def timeline_change_color(ctx: click.Context, timeline_id: int, color: str):
    """Changes the color of a timeline within the current sketch.

    The color is specified as a hexadecimal string (without the leading '#').
    The timeline is identified by its integer ID.

    Args:
        ctx (click.Context): The Click context object, containing the sketch.
        timeline_id (int): The ID of the timeline to modify.
        color (str): The hexadecimal color code (e.g., "AAAA" or "AABB11").

    Example:
        timeline color 1 AABBCC  # Changes the color of timeline 1 to AABBCC.
    """
    sketch = ctx.obj.sketch
    timeline = sketch.get_timeline(timeline_id=timeline_id)
    if not timeline:
        click.echo("No such timeline")
        return
    if not (len(color) == 4 or len(color) == 6):
        click.echo("Color must be hex without leading # e.g. AAAA or AABB11")
        return
    timeline.lazyload_data()
    timeline.color = color

    return
