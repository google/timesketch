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
"""Commands to configure the CLI client."""

import sys

import click

from timesketch_cli_client.definitions import SUPPORTED_OUTPUT_FORMATS


@click.group("config")
def config_group():
    """Configuration for this CLI tool."""


@config_group.group("set")
def set_group():
    """Set configuration parameters."""


@config_group.command("get")
@click.argument("name")
@click.pass_context
def get_config_parameter(ctx: click.Context, name: str) -> None:
    """Get the value of a configuration parameter.

    Args:
        ctx: Click CLI context object.
        name: Name of the configuration parameter to get.
    """
    try:
        # Normalize name for output format settings
        if name in ("output", "output-format"):
            name = "output_format"

        value = ctx.obj.config_assistant.get_config(name)
        click.echo(value)
    except KeyError:
        click.echo(f"No such configuration parameter: {name}")
        ctx.exit(1)


@set_group.command("sketch")
@click.argument("sketch_id")
@click.pass_context
def set_sketch(ctx: click.Context, sketch_id: str) -> None:
    """Set the active sketch.

    Args:
        ctx: Click CLI context object.
        sketch_id: ID of the sketch to save to config.
    """
    if sketch_id:
        if not sketch_id.isdigit():
            click.echo("Error: Sketch ID must be an integer.")
            sys.exit(1)
        ctx.obj.config_assistant.set_config("sketch", int(sketch_id))
    else:
        ctx.obj.config_assistant.set_config("sketch", "")
    ctx.obj.config_assistant.save_config()


def _set_output_format(ctx: click.Context, output_format: str) -> None:
    """Sets the default output format in the configuration.

    Args:
        ctx: Click CLI context object.
        output_format: Format to use for output text.
    """
    if output_format not in SUPPORTED_OUTPUT_FORMATS:
        supported_formats = " ".join(SUPPORTED_OUTPUT_FORMATS)
        click.echo(f"Unsupported format. Choose between {supported_formats}")
        sys.exit(1)

    ctx.obj.config_assistant.set_config("output_format", output_format)
    ctx.obj.config_assistant.save_config()


@set_group.command("output")
@click.argument("output_format")
@click.pass_context
def set_output_format(ctx: click.Context, output_format: str) -> None:
    """Set the output format.

    Args:
        ctx: Click CLI context object.
        output_format: Format to use for output text.
    """
    _set_output_format(ctx, output_format)


@set_group.command("output-format")
@click.argument("output_format")
@click.pass_context
def set_output_format_alias(ctx: click.Context, output_format: str) -> None:
    """Set the output format.

    Args:
        ctx: Click CLI context object.
        output_format: Format to use for output text.
    """
    _set_output_format(ctx, output_format)
