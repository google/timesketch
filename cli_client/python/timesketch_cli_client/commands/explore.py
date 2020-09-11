import click
from tabulate import tabulate


def get_time_chips(time_ranges):
    chips = []
    for time_range in time_ranges:
        if isinstance(time_range, str):
            time_range = (time_range, time_range)

        chip = {
            "field": "",
            "value": "{},{}".format(time_range[0], time_range[1]),
            "type": "datetime_range",
            "operator": "must"
        }
        chips.append(chip)
    return chips


def get_label_chip(label):
    chip = {
        'field': '',
        'value': label,
        'type': 'label',
        'operator': 'must'
    }
    return chip


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


@click.command('explore', help='Search and filter.')
@click.option('--query', '-q', default='*')
@click.option('--time', 'times', multiple=True)
@click.option('--time-range', 'time_ranges', multiple=True, nargs=2)
@click.option('--starred', is_flag=True, default=False)
@click.option('--commented', is_flag=True, default=False)
@click.option('--header/--no-header', default=True)
@click.option('--format', 'format_')
@click.option('--return-fields', 'return_fields', default='')
@click.option('--order', default='asc')
@click.option('--limit', type=int, default=40)
@click.option('--view')
@click.pass_obj
def explore_group(state, query, times, time_ranges, starred, commented, header, format_, return_fields, order, limit, view):

    output_format = state.output
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
        view = state.sketch.get_view(view_name=view)
        query = view.query_string
        query_filter = view.query_filter
        result = search(state.sketch, query, query_filter, return_fields)
        click.echo(format_output(result, output_format, header), nl=new_line)
        return

    if time_ranges:
        chips = get_time_chips(time_ranges)
        query_filter['chips'].extend(chips)

    if times:
        chips = get_time_chips(times)
        query_filter['chips'].extend(chips)

    if starred:
        query_filter['chips'].append(get_label_chip('__ts_star'))

    if commented:
        query_filter['chips'].append(get_label_chip('__ts_comment'))

    result = search(state.sketch, query, query_filter, return_fields)
    click.echo(format_output(result, output_format, header), nl=new_line)
