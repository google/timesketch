import click
import sys

from timesketch_cli_client.definitions import SUPPORTED_OUTPUT_FORMATS


@click.group('config')
def config_group():
    """Configure the tool."""
    pass


@config_group.group('set')
def set_group():
    """Set config parameters."""
    pass


@set_group.command('sketch')
@click.argument('sketch_id')
@click.pass_context
def set_sketch(ctx, sketch_id):
    """Set the active sketch."""
    ctx.obj.config_assistant.set_config('sketch', sketch_id)
    ctx.obj.config_assistant.save_config()


@set_group.command('output-format')
@click.argument('output_format')
@click.pass_context
def set_output_format(ctx, output_format):
    """Set the output format."""
    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        click.echo(
            'Unsupported format. Choose between {}'.format(', '.join(
                SUPPORTED_OUTPUT_FORMATS)))
        sys.exit(1)

    ctx.obj.config_assistant.set_config('output_format', output_format)
    ctx.obj.config_assistant.save_config()
