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

# pylint: disable=import-error
from timesketch_api_client import config as timesketch_config

# pylint: enable=import-error

from timesketch_cli_client.commands import analyze
from timesketch_cli_client.commands import config
from timesketch_cli_client.commands import importer
from timesketch_cli_client.commands import search
from timesketch_cli_client.commands import sketch as sketch_command
from timesketch_cli_client.commands import timelines
from timesketch_cli_client.commands import events
from timesketch_cli_client.commands import sigma

from .definitions import DEFAULT_OUTPUT_FORMAT
from .version import get_version


class TimesketchCli(object):
    """Timesketch CLI state object.

    Attributes:
        sketch_from_flag: Sketch ID if provided by flag
        config_assistant: Instance of ConfigAssistant
        output_format_from_flag: Output format to use
    """

    def __init__(
        self,
        api_client=None,
        sketch_from_flag=None,
        conf_file="",
        output_format_from_flag=None,
    ):
        """Initialize the state object.

        Args:
            sketch_from_flag: Sketch ID if provided by flag.
            conf_file: Path to the config file.
            output_format_from_flag: Output format to use.
        """
        self.api = api_client
        self.sketch_from_flag = sketch_from_flag
        self.output_format_from_flag = output_format_from_flag

        if not api_client:
            try:
                # TODO: Consider other config sections here as well.
                self.api = timesketch_config.get_client(load_cli_config=True)
                if not self.api:
                    raise RequestConnectionError
            except RequestConnectionError:
                click.echo("ERROR: Cannot connect to the Timesketch server.")
                sys.exit(1)

        self.config_assistant = timesketch_config.ConfigAssistant()
        self.config_assistant.load_config_file(conf_file, load_cli_config=True)

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
        """Get the output format
        The priority is:
            * output_format set via flag
            * output_format set via config file
            * or the default format if missing.

        Returns:
            Output format as a string.
        """
        if self.output_format_from_flag:
            output_format = self.output_format_from_flag
            self.config_assistant.set_config("output", output_format)
            self.config_assistant.save_config()
            return output_format
        try:
            output_format = self.config_assistant.get_config("output")
        except KeyError:  # in case value does not exist in the config file
            self.config_assistant.set_config("output", DEFAULT_OUTPUT_FORMAT)
            self.config_assistant.save_config()
            output_format = DEFAULT_OUTPUT_FORMAT
        return output_format


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=get_version(), prog_name="Timesketch CLI")
@click.option("--sketch", type=int, default=None, help="Sketch to work in.")
@click.option(
    "--output-format",
    "output",
    required=False,
    help="Set output format [json, text, tabular, csv] (overrides global setting).",
)
@click.pass_context
def cli(ctx, sketch, output):
    """Timesketch CLI client.

    This tool provides similar features as the web client does.
    It operates within the context of a sketch so you either need to
    provide an existing sketch or create a new one.

    Basic options for editing the sketch is provided, e.g. re-naming and
    changing the description as well as archiving and exporting. For
    other actions not available in this CLI client the web client should be
    used.

    For detailed help on each command, run  <command> --help
    """
    ctx.obj = TimesketchCli(sketch_from_flag=sketch, output_format_from_flag=output)


# Register all commands.
cli.add_command(config.config_group)
cli.add_command(timelines.timelines_group)
cli.add_command(search.search_group)
cli.add_command(search.saved_searches_group)
cli.add_command(analyze.analysis_group)
cli.add_command(sketch_command.sketch_group)
cli.add_command(importer.importer)
cli.add_command(events.events_group)
cli.add_command(sigma.sigma_group)


# pylint: disable=no-value-for-parameter
if __name__ == "__main__":
    cli()
