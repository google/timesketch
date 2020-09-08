import click
from tabulate import tabulate


@click.command('explore')
@click.option('--query', '-q', default='*')
@click.pass_obj
def explore_group(state, query):
    df = state.sketch.explore(query_string=query, as_pandas=True)
    df.rename(columns={'_source': 'timeline'}, inplace=True)
    print(tabulate(df[['datetime', 'message', 'timeline']], headers='keys', tablefmt='psql', showindex=False))

