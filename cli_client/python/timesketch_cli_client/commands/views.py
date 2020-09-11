import click


@click.group('views', help='Operate on views.')
@click.pass_obj
def views_group(unused_state):
    pass


@views_group.command('list', help='List all views in the sketch.')
@click.pass_obj
def list_views(state):
    for view in state.sketch.list_views():
        print(view.name)
