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
