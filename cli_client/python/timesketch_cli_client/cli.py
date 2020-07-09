from timesketch_api_client.client import TimesketchApi
import click
import pandas as pd
from tabulate import tabulate
import subprocess
from subprocess import Popen, PIPE, STDOUT
import readline


@click.group()
@click.pass_context
@click.option('--debug/--no-debug', default=False)
def cli(ctx, debug):
    client = TimesketchApi(host_uri='http://127.0.0.1:5000', username='dev',
                           password='dev')
    sketch = client.get_sketch(sketch_id=8)
    ctx.obj['DEBUG'] = debug
    ctx.obj['SKETCH'] = sketch


@cli.command()
@click.pass_context
def capture(ctx):
    #cmd = "history | grep cli.py | tail -1 | tr -s '[:space:]' | cut -d" " -f3-"
    #cmd = "bash -i -c history -r; history | grep cli.py | tail -1"
    cmd = ["echo", "history", "|", "bash",  "-i"]
    #print(cmd.split())
    #print(subprocess.check_output(cmd, shell=True, ))
    #e = Popen("echo history | bash -i", shell=True, stdin=PIPE,
    #          stdout=PIPE, stderr=STDOUT)
    #print(e.communicate())
    print(readline.get_current_history_length())


@cli.group()
@click.pass_context
def timelines(ctx):
    pass


@timelines.command()
@click.pass_context
@click.option('--foo', default='bar')
def list(ctx, foo):
    if ctx.obj.get('DEBUG'):
        print('DEBUG')
    sketch = ctx.obj['SKETCH']
    for timeline in sketch.list_timelines():
        print(timeline.name)


@timelines.command()
@click.pass_context
@click.option('--analyzer', default='domain')
def analyze(ctx, analyzer):
    sketch = ctx.obj['SKETCH']
    for timeline in sketch.list_timelines():
        session = sketch.run_analyzer(analyzer_name=analyzer, timeline_id=timeline.id)
        print(session.status)


@cli.command()
@click.pass_context
@click.option('--query', default='*')
def explore(ctx, query):
    sketch = ctx.obj['SKETCH']
    df = sketch.explore(query_string=query, as_pandas=True)
    df.rename(columns={'_source': 'timeline'}, inplace=True)
    print(tabulate(df[['datetime', 'message', 'timeline']], headers='keys', tablefmt='psql', showindex=False))




if __name__ == '__main__':
    cli(obj={})