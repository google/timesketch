import click


@click.group('config')
@click.pass_obj
def config_group(state):
    pass


@config_group.group('set')
@click.pass_obj
def set_group(state):
    pass


@set_group.command('sketch')
@click.argument('sketch_id')
@click.pass_obj
def set_sketch(state, sketch_id):
    state.sketch = sketch_id


@set_group.command('output')
@click.argument('output_format')
@click.pass_obj
def set_output(state, output_format):
    state.output = output_format
