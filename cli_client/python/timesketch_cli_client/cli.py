from timesketch_api_client import config as timesketch_config
import click
import sys

from requests.exceptions import ConnectionError

from commands.config import config_group
from commands.timelines import timelines_group
from commands.views import views_group
from commands.explore import explore_group
from commands.analysis import analysis_group


class TimesketchCli(object):
    def __init__(self, sketch_from_flag=None):
        self.sketch_from_flag = sketch_from_flag
        try:
            self.api = timesketch_config.get_client()
        except ConnectionError:
            print('No connection to server. Is it running?')
            sys.exit(1)

        self.config_assistant = timesketch_config.ConfigAssistant()
        self.config_assistant.load_config_file()

    @property
    def sketch(self):

        active_sketch = None
        sketch_from_config = self.config_assistant.get_config('sketch')

        if self.sketch_from_flag:
            active_sketch = self.api.get_sketch(
                sketch_id=int(self.sketch_from_flag))
        elif sketch_from_config:
            active_sketch = self.api.get_sketch(
                sketch_id=int(sketch_from_config))

        # Make sure we have access to the sketch.
        try:
            active_sketch.name
        except KeyError:
            print('No such sketch or you don\'t have permission to access it')
            sys.exit(1)

        return active_sketch

    @sketch.setter
    def sketch(self, sketch_id):
        self.config_assistant.set_config('sketch', sketch_id)
        self.config_assistant.save_config()

    @property
    def output(self):
        output_format = self.config_assistant.get_config('output')
        if not output_format:
            self.config_assistant.set_config('output', 'tabular')
            self.config_assistant.save_config()
            output_format = 'tabular'
        return output_format

    @output.setter
    def output(self, output_format):
        supported_formats = ['text', 'csv', 'tabular']

        if output_format not in supported_formats:
            click.echo(
                'Unsupported format. Choose between {}'.format(', '.join(
                    supported_formats)))
            sys.exit(1)

        self.config_assistant.set_config('output', output_format)
        self.config_assistant.save_config()


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.version_option(version='0.0.1')
@click.option('--sketch', type=int, default=None,
              help='Specify which sketch to work in.')
@click.pass_context
def cli(ctx, sketch):
    """
    Timesketch CLI client.

    This tool provides similar features as the web client does.
    It operates within the context of a sketch so you either need to
    provide an existing sketch or create a new one.

    Basic options for editing the sketch is provided, e.g re-naming and
    changing the description as well as archiving and exporting. For
    other actions not available in this CLI client the web client should be
    used.

    For detailed help on each command, run  <command> --help
    """
    ctx.obj = TimesketchCli(sketch)


# Register all commands.
cli.add_command(config_group)
cli.add_command(timelines_group)
cli.add_command(views_group)
cli.add_command(explore_group)
cli.add_command(analysis_group)


if __name__ == '__main__':
    cli()
