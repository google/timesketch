import click


@click.group('timelines')
@click.pass_obj
def timelines_group(unused_state):
    pass


@timelines_group.command('list')
@click.pass_obj
def list_timelines(state):
    for timeline in state.sketch.list_timelines():
        print(timeline.name)
