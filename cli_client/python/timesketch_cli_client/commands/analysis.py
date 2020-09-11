import click
import time


@click.group('analysis', help='Run and list analyzers.')
@click.pass_obj
def analysis_group(unused_state):
    pass


@analysis_group.command()
@click.option('--analyzer', default='domain')
@click.pass_obj
def run(state, analyzer):
    for timeline in state.sketch.list_timelines():
        click.echo('Running analyzer [{}] on timeline [{}]: '.format(
            analyzer, timeline.name), nl=False)
        session = state.sketch.run_analyzer(
            analyzer_name=analyzer, timeline_id=timeline.id)
        while True:
            status = session.status.split()[2]
            if status == 'DONE':
                click.echo(session.results)
                break
            time.sleep(3)


@analysis_group.command('list')
@click.pass_obj
def list_analyzers(state):
    for analyzer in state.sketch.list_available_analyzers():
        print(analyzer)
