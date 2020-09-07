from timesketch_api_client import client
from timesketch_api_client import config as timesketch_config
import click
import time
from tabulate import tabulate
import sys


def check_sketch(sketch):
    if not sketch:
        print('No sketch specified')
        sys.exit(1)
    try:
        sketch.name
    except KeyError:
        print('No such sketch or you don\'t have permission to access it')
        sys.exit(1)

    return sketch


@click.group()
@click.pass_context
@click.version_option(version='0.0.1')
@click.option('--sketch', type=int, default=None, help='Sketch ID')
def cli(ctx, sketch):
    api = timesketch_config.get_client()
    config_assistant = timesketch_config.ConfigAssistant()
    config_assistant.load_config_file()
    active_sketch = None

    sketch_from_flag = sketch
    sketch_from_config = config_assistant.get_config('sketch')

    if sketch_from_flag:
        active_sketch = api.get_sketch(sketch_id=int(sketch_from_flag))
    elif sketch_from_config:
        active_sketch = api.get_sketch(sketch_id=int(sketch_from_config))

    ctx.obj['SKETCH'] = active_sketch


# Config
@cli.group()
@click.pass_context
def config(ctx):
    pass


@config.group()
@click.pass_context
def set(ctx):
    pass


# config set sketch <sketch ID>
@set.command()
@click.argument('sketch_id')
def sketch(sketch_id):
    config_assistant = timesketch_config.ConfigAssistant()
    config_assistant.load_config_file()
    config_assistant.set_config('sketch', sketch_id)
    config_assistant.save_config()


@set.command()
@click.argument('format')
def output(format):
    supported_formats = ['tabular', 'csv']
    if format not in supported_formats:
        click.echo(
            'Unsupported format. Choose between {}'.format(', '.join(
                supported_formats)))

    config_assistant = timesketch_config.ConfigAssistant()
    config_assistant.load_config_file()
    config_assistant.set_config('output_format', format)
    config_assistant.save_config()


# Timelines
@cli.group()
@click.pass_context
def timelines(ctx):
    pass


@timelines.command()
@click.pass_context
def list(ctx):
    sketch = check_sketch(ctx.obj['SKETCH'])
    for timeline in sketch.list_timelines():
        print(timeline.name)


@timelines.command()
@click.pass_context
@click.option('--analyzer', default='domain')
def analyze(ctx, analyzer):
    sketch = check_sketch(ctx.obj['SKETCH'])
    for timeline in sketch.list_timelines():
        click.echo('Running analyzer [{}] on {}: ... '.format(
            analyzer, timeline.name), nl=False)
        session = sketch.run_analyzer(
            analyzer_name=analyzer, timeline_id=timeline.id)
        while True:
            status = session.status.split()[2]
            if status == 'DONE':
                click.echo(session.results)
                break
            time.sleep(3)

# Explore
@cli.command()
@click.pass_context
@click.option('--query', default='*')
def explore(ctx, query):
    sketch = check_sketch(ctx.obj['SKETCH'])
    df = sketch.explore(query_string=query, as_pandas=True)
    df.rename(columns={'_source': 'timeline'}, inplace=True)
    print(tabulate(df[['datetime', 'message', 'timeline']], headers='keys', tablefmt='psql', showindex=False))


if __name__ == '__main__':
    cli(obj={})
