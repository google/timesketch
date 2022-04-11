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


@set_group.command("sketch")
@click.argument("sketch_id")
@click.pass_context
def set_sketch(ctx, sketch_id):
    """Set the active sketch.

    Args:
        ctx: Click CLI context object.
        sketch_id: ID of the sketch to save to config.
    """
    ctx.obj.config_assistant.set_config("sketch", sketch_id)
    ctx.obj.config_assistant.save_config()


@set_group.command("output")
@click.argument("output_format")
@click.pass_context
def set_output_format(ctx, output_format):
    """Set the output format.

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
