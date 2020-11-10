# Copyright 2020 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Timesketch CLI client."""

from timesketch_api_client import config as timesketch_config
import click
import sys

from requests.exceptions import ConnectionError

from timesketch_cli_client.commands.config import config_group
from timesketch_cli_client.commands.timelines import timelines_group
from timesketch_cli_client.commands.views import views_group
from timesketch_cli_client.commands.explore import explore_group
from timesketch_cli_client.commands.analyze import analysis_group
from timesketch_cli_client.commands.sketch import sketch_group
from timesketch_cli_client.commands.importer import importer

from .definitions import DEFAULT_OUTPUT_FORMAT


class TimesketchCli(object):
    """Timesketch CLI state object.

    Attributes:
        sketch_from_flag: Sketch ID if provided by flag
        config_assistant: Instance of ConfigAssistant
    """
    def __init__(self, sketch_from_flag=None):
        """Initialize the state object.

        Args:
            sketch_from_flag: Sketch ID if provided by flag.
        """
        self.sketch_from_flag = sketch_from_flag
        try:
            self.api = timesketch_config.get_client()
            if not self.api:
                raise ConnectionError
        except ConnectionError:
            sys.exit(1)

        self.config_assistant = timesketch_config.ConfigAssistant()
        self.config_assistant.load_config_file()

    @property
    def sketch(self):
        """Sketch object from the API client.

        Returns:
            Sketch object.
        """
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
            sys.exit(1)

        return active_sketch

    @property
    def output_format(self):
        """Get or set the default output format.

        Returns:
            Output format as a string.
        """
        output_format = self.config_assistant.get_config('output_format')
        if not output_format:
            self.config_assistant.set_config('output', DEFAULT_OUTPUT_FORMAT)
            self.config_assistant.save_config()
            output_format = DEFAULT_OUTPUT_FORMAT
        return output_format


@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.version_option(version='0.0.1')
@click.option('--sketch', type=int, default=None, help='Sketch to work in.')
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
cli.add_command(sketch_group)
cli.add_command(importer)


if __name__ == '__main__':
    cli()
