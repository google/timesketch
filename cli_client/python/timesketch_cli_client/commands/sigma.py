# Copyright 2023 Google Inc. All rights reserved.
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
"""Commands for sigma rules."""

import sys
import click


@click.group("sigma")
def sigma_group():
    """Manage sigma rules."""


@sigma_group.command("list")
# add a option for header or no header
@click.option(
    "--header/--no-header",
    default=True,
    help="Include header in output. (default is to show header))",
)
# add option for columns
@click.option(
    "--columns",
    default="rule_uuid,title",
    help="Comma separated list of columns to show. (default: rule_uuid,title)",
)
@click.pass_context
def list_sigmarules(ctx, header, columns):
    """List all sigma rules."""
    api_client = ctx.obj.api

    if not columns:
        columns = "rule_uuid,title"

    columns = columns.split(",")

    output = ctx.obj.output_format
    try:
        sigma_rules = api_client.list_sigmarules()
    except ValueError as e:
        click.echo(e)
        sys.exit(1)

    if output == "json":
        click.echo(sigma_rules.to_json(orient="records"))
    elif output == "jsonl":
        click.echo(sigma_rules.to_json(orient="records", lines=True))
    elif output == "csv":
        click.echo(sigma_rules.to_csv(header=header))
    elif output == "text":
        click.echo(
            sigma_rules.to_string(index=header, columns=columns),
        )
    else:
        click.echo(sigma_rules.to_string(index=header, columns=columns))


@sigma_group.command("describe")
@click.option(
    "--rule-uuid",
    "rule_uuid",
    required=True,
    help="UUID of the sigma rule.",
)
@click.pass_context
def describe_sigmarule(ctx, rule_uuid):
    """Describe a sigma rule."""
    api_client = ctx.obj.api
    output = ctx.obj.output_format
    try:
        sigma_rule = api_client.get_sigmarule(rule_uuid)
    except ValueError as e:
        click.echo(e)
        sys.exit(1)

    if output == "json":
        click.echo(sigma_rule.__dict__)
    else:
        click.echo(f"Title: {sigma_rule.title}")
        click.echo(f"Author: {sigma_rule.author}")
        click.echo(f"Status: {sigma_rule.status}")
        click.echo(f"Rule UUID: {sigma_rule.rule_uuid}")
        click.echo(f"Search: {sigma_rule.search_query}")
