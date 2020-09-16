import click


@click.group('sketch')
def sketch_group():
    """Manage your sketch."""
    pass


@sketch_group.command('list', help='List all sketches.')
@click.pass_context
def list_sketches(ctx):
    api_client = ctx.obj.api
    for sketch in api_client.list_sketches():
        click.echo('{} {}'.format(sketch.id, sketch.name))


@sketch_group.command('describe', help='Show info about a sketch.')
@click.pass_context
def describe(ctx):
    sketch = ctx.obj.sketch
    click.echo('Name: {}'.format(sketch.name))
    click.echo('Description: {}'.format(sketch.description))


@sketch_group.command('create', help='Create a new sketches.')
@click.option('--name', required=True)
@click.option('--description', required=False)
@click.pass_context
def create_sketch(ctx, name, description):
    api_client = ctx.obj.api
    if not description:
        description = name
    sketch = api_client.create_sketch(name=name, description=description)
    click.echo('Sketch created: {}'.format(sketch.name))
