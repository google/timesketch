# Copyright 2021 Google Inc. All rights reserved.
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

import sys
import click

from requests.exceptions import ConnectionError as RequestConnectionError

#from timesketch_api_client import config as timesketch_config

from timesketch_cli_client.commands import analyze
from timesketch_cli_client.commands import config
from timesketch_cli_client.commands import importer
from timesketch_cli_client.commands import search
from timesketch_cli_client.commands import sketch as sketch_command
from timesketch_cli_client.commands import timelines
from timesketch_cli_client.commands import version

from .definitions import DEFAULT_OUTPUT_FORMAT


class TimesketchCli(object):
    """Timesketch CLI state object.

    Attributes:
        sketch_from_flag: Sketch ID if provided by flag
        config_assistant: Instance of ConfigAssistant
    """

    def __init__(self, api_client=None, sketch_from_flag=None, conf_file=""):
        """Initialize the state object.

        Args:
            sketch_from_flag: Sketch ID if provided by flag.
        """
        self.api_client = api_client
        self.conf_file = conf_file
        self.sketch_from_flag = sketch_from_flag

        #if not api_client:
        #    try:
        #        # TODO: Consider other config sections here as well.
        #        self.api = timesketch_config.get_client(load_cli_config=True)
        #        if not self.api:
        #            raise RequestConnectionError
        #    except RequestConnectionError:
        #        click.echo("ERROR: Cannot connect to the Timesketch server.")
        #        sys.exit(1)

        #self.config_assistant = timesketch_config.ConfigAssistant()
        #self.config_assistant.load_config_file(conf_file, load_cli_config=True)

    @property
    def config_assistant(self):
        from timesketch_api_client import config as timesketch_config
        _config_assistant = timesketch_config.ConfigAssistant()
        _config_assistant.load_config_file(
            self.conf_file, load_cli_config=True)
        return _config_assistant

    @property
    def api(self):
        # Use cached API client if multiple calls are made in the same command.
        if self.api_client:
            return self.api_client

        # Import late to optimize performance (i.e. don't import if not needed)
        from timesketch_api_client import config as timesketch_config
        try:
            _api_client = timesketch_config.get_client(load_cli_config=True)
            if not _api_client:
                raise RequestConnectionError
            self.api_client = _api_client
        except RequestConnectionError:
            click.echo("ERROR: Cannot connect to the Timesketch server.")
            sys.exit(1)
        return self.api_client

    @property
    def sketch(self):
        """Sketch object from the API client.

        Returns:
            Sketch object.
        """
        active_sketch = None
        sketch_from_config = self.config_assistant.get_config("sketch")

        if self.sketch_from_flag:
            active_sketch = self.api.get_sketch(sketch_id=int(self.sketch_from_flag))
        elif sketch_from_config:
            active_sketch = self.api.get_sketch(sketch_id=int(sketch_from_config))

        if not active_sketch:
            click.echo(
                "ERROR: You need to specify a sketch, either with a "
                "flag (--sketch <SKETCH ID>) or update the config."
            )
            sys.exit(1)

        # Make sure we have access to the sketch.
        try:
            active_sketch.name
        except KeyError:
            click.echo("ERROR: No such sketch or you don't have access.")
            sys.exit(1)

        return active_sketch

    @property
    def output_format(self):
        """Get the configured output format, or the default format if missing.

        Returns:
            Output format as a string.
        """
        output_format = self.config_assistant.get_config("output_format")
        if not output_format:
            self.config_assistant.set_config("output", DEFAULT_OUTPUT_FORMAT)
            self.config_assistant.save_config()
            output_format = DEFAULT_OUTPUT_FORMAT
        return output_format


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--sketch", type=int, default=None, help="Sketch to work in.")
@click.pass_context
def cli(ctx, sketch):
    """Timesketch CLI client.

    This tool provides similar features as the web client does.
    It operates within the context of a sketch so you either need to
    provide an existing sketch or create a new one.

    Basic options for editing the sketch is provided, e.g re-naming and
    changing the description as well as archiving and exporting. For
    other actions not available in this CLI client the web client should be
    used.

    For detailed help on each command, run  <command> --help
    """
    ctx.obj = TimesketchCli(sketch_from_flag=sketch)


# Register all commands.
cli.add_command(config.config_group)
cli.add_command(timelines.timelines_group)
cli.add_command(search.search_group)
cli.add_command(search.saved_searches_group)
cli.add_command(analyze.analysis_group)
cli.add_command(sketch_command.sketch_group)
cli.add_command(importer.importer)
cli.add_command(version.version)


# pylint: disable=no-value-for-parameter
if __name__ == "__main__":
    cli()
