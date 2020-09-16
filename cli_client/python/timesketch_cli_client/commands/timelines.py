import click


@click.group('timelines')
def timelines_group():
    """Manage your timelines."""
    pass


@timelines_group.command('list')
@click.pass_context
def list_timelines(ctx):
    """List all timelines in the sketch."""
    sketch = ctx.obj.sketch
    for timeline in sketch.list_timelines():
        click.echo('{} {}'.format(timeline.id, timeline.name))


@timelines_group.command('describe')
@click.argument('timeline_id', type=int, required=False)
@click.pass_context
def describe(ctx, timeline_id):
    """Show details for a timeline."""
    sketch = ctx.obj.sketch
    timeline = sketch.get_timeline(timeline_id=timeline_id)
    if not timeline:
        click.echo('No such timeline')
        return
    click.echo('Name: {}'.format(timeline.name))
    click.echo('Index: {}'.format(timeline.index_name))
