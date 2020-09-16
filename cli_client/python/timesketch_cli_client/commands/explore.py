import click
from tabulate import tabulate
import json


def _create_empty_chip():
    return {
        'field': '',
        'value': '',
        'type': None,
        'operator': 'must'
    }


def get_filter_chip(values, type):
    chips = []
    if type == 'label':
        for label in values:
            if label in ['star', 'comment']:
                label = '__ts_{}'.format(label)
            chip = _create_empty_chip()
            chip['value'] = label
            chip['type'] = 'label'
            chips.append(chip)
    elif type == 'datetime_range':
        for time_range in values:
            if isinstance(time_range, str):
                time_range = (time_range, time_range)
            chip = _create_empty_chip()
            chip['value'] = '{},{}'.format(time_range[0], time_range[1])
            chip['type'] = 'datetime_range'
            chips.append(chip)
    return chips


def search(sketch, query_string, query_filter, return_fields):
    dataframe = sketch.explore(
        query_string=query_string, query_filter=query_filter,
        return_fields=return_fields, as_pandas=True)
    return dataframe


def format_output(dataframe, output_format, show_headers):
    result = None

    if output_format == 'text':
        result = dataframe.to_string(index=False, header=show_headers)
    elif output_format == 'csv':
        result = dataframe.to_csv(index=False, header=show_headers)
    elif output_format == 'tabular':
        if show_headers:
            result = tabulate(
                dataframe, headers='keys', tablefmt='psql', showindex=False)
        else:
            result = tabulate(dataframe, tablefmt='psql', showindex=False)

    return result


def describe_query(query_string, query_filter):
    click.echo('Query string: {}'.format(query_string))
    click.echo('Filter: {}'.format(json.dumps(query_filter, indent=2)))


@click.command('explore')
@click.option(
    '--query', '-q', default='*',
    help='Search query in Elasticsearch query string format.')
@click.option(
    '--time', 'times', multiple=True,
    help='Datetime filter (e.g. 2020-01-01T12:00).')
@click.option(
    '--time-range', 'time_ranges', multiple=True, nargs=2,
    help='Datetime range filter (e.g: 2020-01-01 2020-02-01).')
@click.option(
    '--label', 'labels', multiple=True,
    help='Filter events with label.')
@click.option(
    '--header/--no-header', default=True,
    help='Toggle header information (default is to show).')
@click.option(
    '--output-format', 'format_',
    help='Set output format (overrides global setting).')
@click.option(
    '--return-fields', 'return_fields', default='',
    help='What event fields to show.')
@click.option(
    '--order', default='asc',
    help='Order the output (asc/desc) based on the time field.')
@click.option(
    '--limit', type=int, default=40,
    help='Limit amount of events to show (default: 40).')
@click.option('--view', help='Query and filter from saved view.')
@click.option(
    '--describe', is_flag=True, default=False,
    help='Show the query and filter then exit.')
@click.pass_context
def explore_group(ctx, query, times, time_ranges, labels, header, format_,
                  return_fields, order, limit, view, describe):
    """Search and explore."""
    sketch = ctx.obj.sketch
    output_format = ctx.obj.output_format
    if format_:
        output_format = format_

    new_line = True
    if output_format == 'csv':
        new_line = False

    query_filter = {
        'from': 0,
        'terminate_after': limit,
        'size': limit,
        'indices': ['_all'],
        'order': order,
        'chips': [],
    }

    if view:
        view = sketch.get_view(view_name=view)
        query = view.query_string
        query_filter = view.query_filter
        if describe:
            describe_query(query, query_filter)
            return
        result = search(sketch, query, query_filter, return_fields)
        click.echo(format_output(result, output_format, header), nl=new_line)
        return

    if time_ranges:
        chips = get_filter_chip(time_ranges, type='datetime_range')
        query_filter['chips'].extend(chips)

    if times:
        chips = get_filter_chip(times, type='datetime_range')
        query_filter['chips'].extend(chips)

    if labels:
        chips = get_filter_chip(labels, type='label')
        query_filter['chips'].extend(chips)

    if describe:
        describe_query(query, query_filter)
        return

    result = search(sketch, query, query_filter, return_fields)
    click.echo(format_output(result, output_format, header), nl=new_line)
