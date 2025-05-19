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
"""CLI management tool."""

import os
import pathlib
import json
import re
import logging
import subprocess
import time
import io
import zipfile
import csv
import datetime
import traceback
from typing import Optional
import yaml
import redis


import click
import pandas as pd
from flask_restful import marshal
from flask import current_app
from flask.cli import FlaskGroup
from sqlalchemy.exc import IntegrityError
from jsonschema import validate, ValidationError, SchemaError
from celery.result import AsyncResult


from timesketch.api.v1 import export as api_export
from timesketch.api.v1.resources import ResourceMixin
from timesketch.api.v1 import utils as api_utils
from timesketch.lib import utils as lib_utils
from timesketch.lib.datastores.opensearch import OpenSearchDataStore

from timesketch.lib.definitions import DEFAULT_SOURCE_FIELDS

from timesketch import version
from timesketch.app import create_app
from timesketch.app import create_celery_app
from timesketch.lib import sigma_util
from timesketch.models import db_session
from timesketch.models import drop_all
from timesketch.models.user import Group
from timesketch.models.user import User
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Event
from timesketch.models.sketch import AnalysisSession
from timesketch.models.sketch import Analysis
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sigma import SigmaRule
from timesketch.models.sketch import Timeline
from timesketch.models.sketch import SearchIndex


# Default filenames for sketch export
DEFAULT_EXPORT_METADATA_FILENAME = "metadata.json"
DEFAULT_EXPORT_EVENTS_FILENAME_TEMPLATE = "events.{output_format}"
DEFAULT_EXPORT_ARCHIVE_FILENAME_TEMPLATE = (
    "sketch_{sketch_id}_{output_format}_export.zip"
)


def configure_opensearch_logger():
    """Configure the opensearch-py logger for tsctl."""
    opensearch_logger = logging.getLogger("opensearch")
    # Set level to INFO to see more request/response logs
    opensearch_logger.setLevel(logging.WARNING)
    # Remove any default handlers to prevent duplicate or unwanted formatting
    opensearch_logger.handlers = []
    # Add a new handler with a desired formatter
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(name)s/%(levelname)s %(message)s")
    handler.setFormatter(formatter)
    opensearch_logger.addHandler(handler)


# Configure the opensearch logger immediately after imports
configure_opensearch_logger()


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Management script for the Timesketch application."""


@cli.command(name="list-users")
@click.option("--status", "-s", is_flag=True, help="Show status of the users.")
def list_users(status):
    """List all users."""
    for user in User.query.all():
        if user.admin:
            extra = " (admin)"
        else:
            extra = ""
        if status:
            print(f"{user.username}{extra} (active: {user.active})")
        else:
            print(f"{user.username}{extra}")


@cli.command(name="create-user")
@click.argument("username")
@click.option("--password")
def create_user(username, password=None):
    """Create a user."""

    def get_password_from_prompt():
        """Get password from the command line prompt."""
        first_password = click.prompt("Enter password", hide_input=True, type=str)
        second_password = click.prompt(
            "Enter password again", hide_input=True, type=str
        )
        if first_password != second_password:
            print("Passwords don't match, try again.")
            get_password_from_prompt()
        return first_password

    if not password:
        password = get_password_from_prompt()
    user = User.get_or_create(username=username, name=username)
    user.set_password(plaintext=password)
    db_session.add(user)
    db_session.commit()
    print(f"User account for {username} created/updated")


@cli.command(name="enable-user")
@click.argument("username")
def enable_user(username):
    """Enable a user."""
    user = User.query.filter_by(username=username).first()
    if not user:
        print("User does not exist.")
        return

    user.active = True
    db_session.add(user)
    db_session.commit()
    print(f"Activated user {username}")


@cli.command(name="disable-user")
@click.argument("username")
def disable_user(username):
    """Disable a user."""
    user = User.query.filter_by(username=username).first()
    if not user:
        print("User does not exist.")
        return

    user.active = False
    db_session.add(user)
    db_session.commit()
    print(f"Disabled user {username}")


@cli.command(name="make-admin")
@click.argument("username")
def make_admin(username):
    """Give a user the admin role."""
    user = User.query.filter_by(username=username).first()
    if not user:
        print("User does not exist.")
        return

    user.admin = True
    db_session.add(user)
    db_session.commit()
    print("User is now an admin.")


@cli.command(name="revoke-admin")
@click.argument("username")
def revoke_admin(username):
    """Revoke a user the admin role."""
    user = User.query.filter_by(username=username).first()
    if not user:
        print("User does not exist.")
        return

    user.admin = False
    db_session.add(user)
    db_session.commit()
    print("User is not an admin anymore.")


@cli.command(name="grant-user")
@click.argument("username")
@click.option("--sketch_id", type=int, required=True)
def grant_user(username, sketch_id):
    """Grant access to a sketch."""
    sketch = Sketch.get_by_id(sketch_id)
    user = User.query.filter_by(username=username).first()
    if not sketch:
        print("Sketch does not exist.")
    elif not user:
        print(f"User {username} does not exist.")
    else:
        sketch.grant_permission(permission="read", user=user)
        sketch.grant_permission(permission="write", user=user)
        print(f"User {username} added to the sketch {sketch.id} ({sketch.name})")


@cli.command(name="version")
def get_version():
    """Return the version information of Timesketch."""
    print(f"Timesketch version: {version.get_version()}")


@cli.command(name="drop-db")
def drop_db():
    """Drop all database tables."""
    if click.confirm("Do you really want to drop all the database tables?"):
        if click.confirm(
            "Are you REALLLY sure you want to DROP ALL the database tables?"
        ):
            drop_all()
            print("All tables dropped. Database is now empty.")


@cli.command(name="list-sketches")
def list_sketches():
    """List all sketches."""
    sketches = Sketch.query.all()
    for sketch in sketches:
        assert isinstance(sketch, Sketch)
        status = sketch.get_status.status
        if status == "deleted":
            continue
        print(sketch.id, sketch.name, f"status:{status}")


@cli.command(name="list-groups")
@click.option("--showmembership", is_flag=True, help="Show members of that group.")
def list_groups(showmembership):
    """List all groups."""
    for group in Group.query.all():
        if showmembership:
            users = []
            for user in group.users:
                users.append(user.username)
            print(f"{group.name}:{','.join(users)}")
        else:
            print(group.name)


@cli.command(name="create-group")
@click.argument("group_name")
def create_group(group_name):
    """Create a group."""
    group = Group.get_or_create(name=group_name, display_name=group_name)
    db_session.add(group)
    db_session.commit()
    print(f"Group created: {group_name}")


@cli.command(name="list-group-members")
@click.argument("group_name")
def list_group_members(group_name):
    """List all members of a group."""
    group = Group.query.filter_by(name=group_name).first()
    if not group:
        print("No such group.")
        return

    for user in group.users:
        print(user.username)


@cli.command(name="add-group-member")
@click.argument("group_name")
@click.option("--username", required=True)
def add_group_member(group_name, username):
    """Add a user to a group."""
    group = Group.query.filter_by(name=group_name).first()
    if not group:
        print("No such group.")
        return

    user = User.query.filter_by(username=username).first()
    if not user:
        print("User does not exist.")
        return

    try:
        user.groups.append(group)
        db_session.commit()
        print("Added user to group.")
    except IntegrityError:
        print("User is already a member of the group.")


@cli.command(name="remove-group-member")
@click.argument("group_name")
@click.option("--username", required=True)
def remove_group_member(group_name, username):
    """Remove a user from a group."""
    group = Group.query.filter_by(name=group_name).first()
    if not group:
        print("No such group.")
        return

    user = User.query.filter_by(username=username).first()
    if not user:
        print("User does not exist.")
        return

    try:
        user.groups.remove(group)
        db_session.commit()
        print("Removed user from group.")
    except ValueError:
        print("User is not a member of the group.")


@cli.command(name="import-search-templates")
@click.argument("path")
def import_search_templates(path):
    """Import search templates from filesystem path."""
    file_paths = set()
    supported_file_types = [".yml", ".yaml"]
    for root, _, files in os.walk(path):
        for file in files:
            file_extension = pathlib.Path(file.lower()).suffix
            if file_extension in supported_file_types:
                file_paths.add(os.path.join(root, file))

    for file_path in file_paths:
        search_templates = None
        with open(file_path, "r", encoding="utf-8") as fh:
            search_templates = yaml.safe_load(fh.read())

        if isinstance(search_templates, dict):
            search_templates = [search_templates]

        if search_templates:
            for search_template_dict in search_templates:
                print(f"Importing: {search_template_dict.get('short_name')}")
                display_name = search_template_dict.get("display_name")
                description = search_template_dict.get("description")
                uuid = search_template_dict.get("id")
                query_string = search_template_dict.get("query_string")
                query_filter = search_template_dict.get("query_filter", {})
                query_dsl = search_template_dict.get("query_dsl", {})
                tags = search_template_dict.get("tags", [])

                searchtemplate = SearchTemplate.query.filter_by(
                    template_uuid=uuid
                ).first()
                if not searchtemplate:
                    searchtemplate = SearchTemplate(
                        name=display_name, template_uuid=uuid
                    )
                    db_session.add(searchtemplate)
                    db_session.commit()

                searchtemplate.name = display_name
                searchtemplate.description = description
                searchtemplate.template_json = json.dumps(search_template_dict)
                searchtemplate.query_string = query_string
                searchtemplate.query_filter = json.dumps(query_filter)
                searchtemplate.query_dsl = json.dumps(query_dsl)

                if tags:
                    for tag in tags:
                        searchtemplate.add_label(tag)

                db_session.add(searchtemplate)
                db_session.commit()


@cli.command(name="import-sigma-rules")
@click.argument("path")
def import_sigma_rules(path):
    """Import sigma rules from filesystem path."""
    file_paths = set()
    supported_file_types = [".yml", ".yaml"]

    if os.path.isfile(path):
        file_paths.add(path)

    for root, _, files in os.walk(path):
        for file in files:
            file_extension = pathlib.Path(file.lower()).suffix
            if file_extension in supported_file_types:
                file_paths.add(os.path.join(root, file))

    for file_path in file_paths:
        sigma_rule = None
        sigma_yaml = None

        with open(file_path, "r", encoding="utf-8") as fh:
            try:
                sigma_yaml = fh.read()
                sigma_rule = sigma_util.parse_sigma_rule_by_text(sigma_yaml)
            except ValueError as e:
                print(f"Sigma Rule Parsing error: {e}")
                continue
            except NotImplementedError as e:
                print(f"Sigma Rule Parsing error: {e}")
                continue

        print(f"Importing: {sigma_rule.get('title')}")

        if not sigma_rule:
            continue

        # Query rules to see if it already exist and exit if found
        rule_uuid = sigma_rule.get("id")
        sigma_rule_from_db = SigmaRule.query.filter_by(rule_uuid=rule_uuid).first()
        if sigma_rule_from_db:
            print(f"Rule {rule_uuid} is already imported")
            continue

        sigma_db_rule = SigmaRule.query.filter_by(rule_uuid=rule_uuid).first()
        if not sigma_db_rule:
            sigma_db_rule = SigmaRule(
                rule_uuid=rule_uuid,
                rule_yaml=sigma_yaml,
                description=sigma_rule.get("description"),
                title=sigma_rule.get("title"),
                user=None,
            )
            db_session.add(sigma_db_rule)
            db_session.commit()

            sigma_db_rule.set_status(sigma_rule.get("status", "experimental"))
            # query string is not stored in the database but we attach it to
            # the JSON result here as it is added in the GET methods
            sigma_db_rule.query_string = sigma_rule.get("search_query")
        else:
            print(f"Rule already imported: {sigma_rule.get('title')}")


@cli.command(name="list-sigma-rules")
@click.option(
    "--columns",
    default="rule_uuid,title",
    required=False,
    help="Comma separated list of columns to show",
)
def list_sigma_rules(columns):
    """List sigma rules"""

    all_sigma_rules = SigmaRule.query.all()

    table_data = [
        [columns],
    ]

    for rule in all_sigma_rules:
        relevant_data = []
        for column in columns.split(","):
            if column == "status":
                relevant_data.append(rule.get_status.status)
            else:
                try:
                    relevant_data.append(getattr(rule, column))
                except AttributeError:
                    print(f"Column {column} not found in SigmaRule")
                    return
        table_data.append([relevant_data])

    print_table(table_data)


@cli.command(name="remove-sigma-rule")
@click.argument("rule_uuid")
def remove_sigma_rule(rule_uuid):
    """Deletes a Sigma rule from the database.

    Deletes a single Sigma rule selected by the `uuid`
    Args:
        rule_uuid: UUID of the rule to be deleted.
    """

    rule = SigmaRule.query.filter_by(rule_uuid=rule_uuid).first()

    if not rule:
        error_msg = f"No rule found with rule_uuid.{rule_uuid!s}"
        print(error_msg)  # only needed in debug cases
        return

    print(f"Rule {rule_uuid} deleted")
    db_session.delete(rule)
    db_session.commit()


@cli.command(name="remove-all-sigma-rules")
def remove_all_sigma_rules():
    """Deletes all Sigma rule from the database."""

    if click.confirm("Do you really want to drop all the Sigma rules?"):
        if click.confirm("Are you REALLLY sure you want to DROP ALL the Sigma rules?"):
            all_sigma_rules = SigmaRule.query.all()
            for rule in all_sigma_rules:
                db_session.delete(rule)
                db_session.commit()

            print("All rules deleted")


@cli.command(name="export-sigma-rules")
@click.argument("path")
def export_sigma_rules(path):
    """Export sigma rules to a filesystem path."""

    if not os.path.isdir(path):
        raise RuntimeError(
            f"The directory needs to exist, please create: {path:s} first"
        )

    all_sigma_rules = SigmaRule.query.all()

    n = 0

    for rule in all_sigma_rules:
        file_path = os.path.join(path, f"{rule.title}.yml")
        if os.path.isfile(file_path):
            print(f"File [{file_path:s}] already exists.")
            continue

        with open(file_path, "wb") as fw:
            fw.write(rule.rule_yaml.encode("utf-8"))
        n = n + 1
    print(f"{n} Sigma rules exported")


@cli.command(name="info")
def info():
    """Get various information about the environment that runs Timesketch."""

    # Get Timesketch version
    print(f"Timesketch version: {version.get_version()}")

    # Get plaso version
    try:
        output = subprocess.check_output(["psort.py", "--version"])
        print(output.decode("utf-8"))
    except FileNotFoundError:
        print("psort.py not installed")

    # Get installed node version
    try:
        output = subprocess.check_output(["node", "--version"]).decode("utf-8")
        print(f"Node version: {output} ")
    except FileNotFoundError:
        print("Node not installed. Node is only used in the dev environment.")

    try:
        # Get installed npm version
        output = subprocess.check_output(["npm", "--version"]).decode("utf-8")
        print(f"npm version: {output}")
    except FileNotFoundError:
        print("npm not installed. npm is only used in the dev environment.")

    try:
        # Get installed yarn version
        output = subprocess.check_output(["yarn", "--version"]).decode("utf-8")
        print(f"yarn version: {output} ")
    except FileNotFoundError:
        print("yarn not installed. Yarn is only used in the dev environment.")

    try:
        # Get installed python version
        output = subprocess.check_output(["python3", "--version"]).decode("utf-8")
        print(f"Python version: {output} ")
    except FileNotFoundError:
        print("Python3 not installed")

    try:
        # Get installed pip version
        output = subprocess.check_output(["pip", "--version"]).decode("utf-8")
        print(f"pip version: {output} ")
    except FileNotFoundError:
        print("pip not installed")


def print_table(table_data):
    """Prints a table."""
    # calculate the maximum length of each column
    max_lengths = [0] * len(table_data[0])
    for row in table_data:
        for i, cell in enumerate(row):
            max_lengths[i] = max(max_lengths[i], len(str(cell)))

    # create the table
    for row in table_data:
        for i, cell in enumerate(row):
            print(str(cell).ljust(max_lengths[i]), end=" ")
        print()


@cli.command(name="sketch-info")
@click.argument("sketch_id", type=int)
def sketch_info(sketch_id: int):
    """Display detailed information about a specific sketch.

    This command retrieves and displays comprehensive information about a
    Timesketch sketch, including:

    - **Sketch Details:** The sketch's ID and name.
    - **Timelines:** A table listing the timelines within the
      sketch, including their search index ID, index name, creation date,
      user ID, description, status, timeline name, and timeline ID.
    - **Sharing Information:** Details about users and groups with whom the
      sketch is shared.
    - **Sketch Status:** The current status of the sketch (e.g., "ready",
      "archived").
    - **Public Status:** Whether the sketch is publicly accessible.
    - **Sketch Labels:** Any labels applied to the sketch.
    - **Status History:** A table showing the status history of the sketch,
      including the status ID, status value, creation date, and user ID.

    Args:
        sketch_id (str): The ID of the sketch to retrieve information about.

    Raises:
        SystemExit: If the specified sketch does not exist.
    """
    sketch = Sketch.get_by_id(sketch_id)
    if not sketch:
        print("Sketch does not exist.")
        return

    print(f"Sketch {sketch_id} Name: ({sketch.name})")

    # define the table data
    table_data = [
        [
            "searchindex_id",
            "index_name",
            "created_at",
            "user_id",
            "description",
            "status",
            "timeline_name",
            "timeline_id",
        ],
    ]
    for t in sketch.timelines:
        table_data.append(
            [
                t.searchindex_id,
                t.searchindex.index_name,
                t.created_at,
                t.user_id,
                t.description,
                t.status[-1].status,
                t.name,
                t.id,
            ]
        )
    print_table(table_data)

    print(f"Created by: {sketch.user.username}")
    print("Shared with:")
    print("\tUsers: (user_id, username)")
    if sketch.collaborators:
        print("\tUsers: (user_id, username)")
        for user in sketch.collaborators:
            print(f"\t\t{user.id}: {user.username}")
    else:
        print("\tNo users shared with.")
    print(f"\tGroups ({len(sketch.groups)}):")
    if sketch.groups:
        for group in sketch.groups:
            print(f"\t\t{group.display_name}")
    else:
        print("\tNo groups shared with.")
    sketch_labels = [label.label for label in sketch.labels]
    print(f"Sketch Status: {sketch.get_status.status}")
    print(f"Sketch is public: {bool(sketch.is_public)}")
    sketch_labels = ([label.label for label in sketch.labels],)
    print(f"Sketch Labels: {sketch_labels}")

    status_table = [
        [
            "id",
            "status",
            "created_at",
            "user_id",
        ],
    ]
    for _status in sketch.status:
        status_table.append(
            [_status.id, _status.status, _status.created_at, _status.user_id]
        )
    print("Status:")
    print_table(status_table)


@cli.command(name="timeline-status")
@click.argument("timeline_id", type=int)
@click.option(
    "--action",
    default="get",
    type=click.Choice(["get", "set"]),
    required=False,
    help="get or set timeline status.",
)
@click.option(
    "--status",
    required=False,
    type=click.Choice(["ready", "processing", "fail"]),
    help="get or set timeline status.",
)
def timeline_status(timeline_id: int, action: str, status: str):
    """Get or set a timeline status.

    If "action" is "set", the given value of status will be written in the status.

    Args:
        timeline_id (int): The ID of the timeline.
        action (str):  The action to perform ("get" or "set").
        status (str): The timeline status to set.  Must be one of "ready",
                      "processing", or "fail".
    """
    if action == "get":
        timeline = Timeline.query.filter_by(id=timeline_id).first()
        if not timeline:
            print("Timeline does not exist.")
            return
        # define the table data
        table_data = [
            [
                "searchindex_id",
                "index_name",
                "created_at",
                "user_id",
                "description",
                "status",
            ],
        ]
        table_data.append(
            [
                timeline.searchindex_id,
                timeline.searchindex.index_name,
                timeline.created_at,
                timeline.user_id,
                timeline.description,
                timeline.status[-1].status,
            ]
        )
        print_table(table_data)

        status_table = [
            [
                "id",
                "status",
                "created_at",
                "user_id",
            ],
        ]
        for _status in timeline.status:
            status_table.append(
                [_status.id, _status.status, _status.created_at, _status.user_id]
            )
        print("Status:")
        print_table(status_table)

    elif action == "set":
        timeline = Timeline.query.filter_by(id=timeline_id).first()
        if not timeline:
            print("Timeline does not exist.")
            return
        # exit if status is not set
        if not status:
            print("Status is not set.")
            return
        timeline.set_status(status)
        db_session.commit()
        print(f"Timeline {timeline_id} status set to {status}")
        # to verify run:
        print(f"To verify run: tsctl timeline-status {timeline_id} --action get")


@cli.command(name="validate-context-links-conf")
@click.argument("path")
def validate_context_links_conf(path):
    """Validates the provided context link yaml configuration file."""

    hardcoded_modules_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "short_name": {"type": "string"},
            "match_fields": {
                "type": "array",
                "items": [
                    {"type": "string"},
                ],
            },
            "validation_regex": {"type": "string"},
        },
        "required": ["short_name", "match_fields"],
    }

    linked_services_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "context_link": {
                "type": "string",
                "pattern": "<ATTR_VALUE>",
            },
            "match_fields": {
                "type": "array",
                "minItems": 1,
                "items": [
                    {
                        "type": "string",
                    },
                ],
            },
            "redirect_warning": {
                "type": "boolean",
            },
            "short_name": {
                "type": "string",
                "minLength": 1,
            },
            "validation_regex": {
                "type": "string",
            },
        },
        "required": [
            "context_link",
            "match_fields",
            "redirect_warning",
            "short_name",
        ],
    }

    if not os.path.isfile(path):
        print(f"Cannot load the config file: {path} does not exist!")
        return

    with open(path, "r", encoding="utf-8") as fh:
        context_link_config = yaml.safe_load(fh)

    if not context_link_config:
        print("The provided config file is empty.")
        return

    if context_link_config["hardcoded_modules"]:
        for entry in context_link_config["hardcoded_modules"]:
            try:
                validate(
                    instance=context_link_config["hardcoded_modules"][entry],
                    schema=hardcoded_modules_schema,
                )
                print(f'=> OK: "{entry}"')
            except (ValidationError, SchemaError) as err:
                print(f'=> ERROR: "{entry}" >> {err}\n')

    if context_link_config["linked_services"]:
        for entry in context_link_config["linked_services"]:
            try:
                validate(
                    instance=context_link_config["linked_services"][entry],
                    schema=linked_services_schema,
                )
                print(f'=> OK: "{entry}"')
            except (ValidationError, SchemaError) as err:
                print(f'=> ERROR: "{entry}" >> {err}\n')


@cli.command(name="searchindex-info")
@click.option(
    "--searchindex_id",
    type=int,
    required=False,
    help="Searchindex database ID to search for e.g. 3.",
)
@click.option(
    "--index_name",
    required=False,
    help="Searchindex name to search for e.g. 4c5afdf60c6e49499801368b7f238353.",
)
def searchindex_info(searchindex_id: int, index_name: str):
    """Search for a searchindex and print information about it.
    Especially which sketch the searchindex belongs to. You can either use the
    searchindex ID or the index name.


    Args:
        searchindex_id (int): The searchindex database ID to search for (e.g.,
                              "3").
        index_name (str): The search index ID to search for (e.g.,
                              "4c5afdf60c6e49499801368b7f238353").
    """
    if searchindex_id:
        if not searchindex_id.isdigit():
            print("Searchindex database ID needs to be an integer.")
            return

    index_to_search = None

    if searchindex_id:
        index_to_search = SearchIndex.query.filter_by(id=searchindex_id).first()
    elif index_name:
        index_to_search = SearchIndex.query.filter_by(index_name=index_name).first()
    else:
        print("Please provide either a searchindex ID or an index name")
        return

    if not index_to_search:
        print("Searchindex not found in database.")
        return

    print(f"Searchindex: {index_to_search.id} Name: {index_to_search.name} found")

    timelines = index_to_search.timelines
    if timelines:
        print("Associated Timelines:")
        for timeline in timelines:
            print(f"  ID: {timeline.id}, Name: {timeline.name}")
            if timeline.sketch:
                print(
                    f"    Sketch ID: {timeline.sketch.id}, Name: {timeline.sketch.name}"
                )
            else:
                print("    No associated sketch found.")
    else:
        print("No associated timelines found.")
        return


@cli.command(name="searchindex-status")
@click.option(
    "--action",
    default="get",
    type=click.Choice(["get", "set"]),
    required=False,
    help="get or set timeline status.",
)
@click.option(
    "--status",
    required=False,
    type=click.Choice(["ready", "processing", "fail"]),
    help="get or set timeline status.",
)
@click.option(
    "--searchindex_id",
    required=True,
    help="Searchindex database ID to search for e.g. 1.",
)
def searchindex_status(searchindex_id: str, action: str, status: str):
    """Get or set a searchindex status.

    If "action" is "set", the given value of status will be written in the status.

    Args:
        searchindex_id (str): The ID of the search index.
        action (str): The action to perform ("get" or "set").
        status (str): The search index status to set ("ready", "processing", or
                      "fail").
    """
    if action == "get":
        searchindex = SearchIndex.query.filter_by(id=searchindex_id).first()
        if not searchindex:
            print("Searchindex does not exist.")
            return
        table_data = [
            [
                "searchindex_id",
                "index_name",
                "created_at",
                "user_id",
                "description",
                "status",
            ],
        ]
        table_data.append(
            [
                searchindex.id,
                searchindex.index_name,
                searchindex.created_at,
                searchindex.user_id,
                searchindex.description,
                searchindex.status[-1].status,
            ]
        )
        print_table(table_data)

        # Display all historical statuses
        if searchindex.status:
            print("\nFull Status Value (only one should be there):")
            status_history_table_data = [
                ["ID", "Status", "Created At", "User ID", "Is Latest"],
            ]
            latest_status_obj = searchindex.status[-1]
            for _status_entry in searchindex.status:
                is_latest_marker = (
                    "(latest)" if _status_entry == latest_status_obj else ""
                )
                status_history_table_data.append(
                    [
                        _status_entry.id,
                        _status_entry.status,
                        _status_entry.created_at,
                        _status_entry.user.username if _status_entry.user else "N/A",
                        is_latest_marker,
                    ]
                )
            print_table(status_history_table_data)
    elif action == "set":
        searchindex = SearchIndex.query.filter_by(id=searchindex_id).first()
        if not searchindex:
            print("Searchindex does not exist.")
            return
        # exit if status is not set
        if not status:
            print("Status is not set.")
            return
        searchindex.set_status(status)
        db_session.commit()
        print(f"Searchindex {searchindex_id} status set to {status}")
        # to verify run:
        print(f"To verify run: tsctl searchindex-status {searchindex_id} --action get")


# Analyzer stats cli command
@cli.command(name="analyzer-stats")
@click.argument(
    "analyzer_name",
    required=False,
    default="all",
)
@click.option(
    "--timeline_id",
    type=int,
    required=False,
    help="Timeline ID if the analyzer results should be filtered by timeline.",
)
@click.option(
    "--scope",
    required=False,
    help="Scope on: [many_hits, long_runtime, recent]",
)
@click.option(
    "--result_text_search",
    required=False,
    help="Search in result text. E.g. for a specific rule_id.",
)
@click.option(
    "--limit",
    required=False,
    help="Limit the number of results.",
)
@click.option(
    "--export_csv",
    required=False,
    help="Export the results to a CSV file.",
)
def analyzer_stats(
    analyzer_name, timeline_id, scope, result_text_search, limit, export_csv
):
    """Prints analyzer stats."""

    if timeline_id:
        timeline = Timeline.get_by_id(timeline_id)
        if not timeline:
            print("No timeline found with this ID.")
            return
        if analyzer_name == "all":
            analysis_history = Analysis.query.filter_by(timeline=timeline).all()
        else:
            analysis_history = Analysis.query.filter_by(
                timeline=timeline, analyzer_name=analyzer_name
            ).all()
    elif analyzer_name == "all":
        analysis_history = Analysis.query.filter_by().all()
    else:
        # analysis filter by analyzer_name
        analysis_history = Analysis.query.filter_by(analyzer_name=analyzer_name).all()

    df = pd.DataFrame()
    for analysis in analysis_history:
        # extract number of hits from result to a int so it could be sorted
        # TODO: make this more generic as the number of events might only
        # be a part of the result string in Sigma analyzers
        try:
            matches = int(re.search(r"\d+(?=\s+events)", analysis.result))
        except TypeError:
            matches = 0
        new_row = pd.DataFrame(
            [
                {
                    "analyzer_name": analysis.analyzer_name,
                    "runtime": analysis.updated_at - analysis.created_at,
                    "hits": matches,
                    "timeline_id": analysis.timeline_id,
                    "analysis_id": analysis.id,
                    "created_at": analysis.created_at,
                    "result": analysis.result,
                }
            ]
        )
        df = pd.concat([df, new_row], ignore_index=True)

    if df.empty:
        print("No Analyzer runs found!")
        return

    # make the runtime column to only display in minutes and cut away days etc.
    df["runtime"] = df["runtime"].dt.seconds / 60

    if result_text_search:
        df = df[df.result.str.contains(result_text_search, na=False)]

    # Sorting the dataframe depending on the parameters

    if scope in ["many_hits", "many-hits", "hits"]:
        if analyzer_name == "sigma":
            df = df.sort_values("hits", ascending=False)
        else:
            print("Sorting by hits is only possible for sigma analyzer.")
            df = df.sort_values("runtime", ascending=False)
    elif scope == "long_runtime":
        df = df.sort_values("runtime", ascending=False)
    elif scope == "recent":
        df = df.sort_values("created_at", ascending=False)
    else:
        df = df.sort_values("runtime", ascending=False)

    if limit:
        df = df.head(int(limit))

    # remove hits column if analyzer_name is not sigma
    if analyzer_name != "sigma":
        df = df.drop(columns=["hits"])

    if export_csv:
        df.to_csv(export_csv, index=False)
        print(f"Analyzer stats exported to {export_csv}")
    else:
        pd.options.display.max_colwidth = 500
        print(df)


@cli.command(name="celery-tasks-redis")
def celery_tasks_redis():
    """Check and display the status of all Celery tasks stored in Redis.

    This command connects to the Redis instance used by Celery to store
    task metadata and retrieves information about all tasks. It then
    presents this information in a formatted table, including the task ID,
    name, status, and result.

    The command handles potential connection errors to Redis and gracefully
    exits if no tasks are found. It also handles exceptions that might occur
    when retrieving task details, displaying "N/A" for any unavailable
    information.

    Note: Celery tasks have a `result_expire` date, which by default is
        one day. After that, the results will no longer be available.

    """
    celery = create_celery_app()
    redis_url = celery.conf.broker_url

    try:
        redis_client = redis.from_url(redis_url)
    except redis.exceptions.ConnectionError:
        print("Could not connect to Redis.")
        return

    # Get all keys matching the pattern for Celery task metadata
    task_meta_keys = redis_client.keys("celery-task-meta-*")

    if not task_meta_keys:
        print("No Celery tasks found in Redis.")
        return

    table_data = [["Task ID", "Name", "Status", "Result"]]
    for key in task_meta_keys:
        task_id = key.decode("utf-8").split("celery-task-meta-")[1]
        task_result = AsyncResult(task_id, app=celery)

        try:
            task_name = task_result.name
        except Exception:  # pylint: disable=broad-except
            task_name = "N/A"

        try:
            task_status = task_result.status
        except Exception:  # pylint: disable=broad-except
            task_status = "N/A"

        try:
            task_result_value = str(task_result.result)
        except Exception:  # pylint: disable=broad-except
            task_result_value = "N/A"

        table_data.append([task_id, task_name, task_status, task_result_value])

    max_lengths = [0] * len(table_data[0])
    for row in table_data:
        for i, cell in enumerate(row):
            max_lengths[i] = max(max_lengths[i], len(str(cell)))

    # create the table
    for row in table_data:
        for i, cell in enumerate(row):
            print(str(cell).ljust(max_lengths[i]), end=" ")
        print()


@cli.command(name="celery-tasks")
@click.option(
    "--task_id",
    required=False,
    help="Show information about a specific task ID.",
)
@click.option(
    "--active",
    is_flag=True,
    help="Show only active tasks.",
)
@click.option(
    "--show_all",
    is_flag=True,
    help="Show all tasks, including pending, active, and failed.",
)
def celery_tasks(task_id, active, show_all):
    """Show running or past Celery tasks.
    This command provides various ways to inspect and view the status of
    Celery tasks within the Timesketch application. It can display
    information about a specific task, list active tasks, show all tasks
    (including pending, active, and failed).

    Args:
        task_id (str): If provided, display detailed information about the
            task with this ID.
        active (bool): If True, display only currently active tasks.
        show_all (bool): If True, display all tasks, including active, pending,
            reserved, scheduled, and failed tasks.

    Notes:
        - Celery tasks have a `result_expire` date, which defaults to one day.
          After this period, task results may no longer be available.
        - When displaying all tasks, the status of each task is retrieved,
          which may take some time.
        - If no arguments are provided, it will print a message to use
            --active or --show_all.

    Examples:
        # Show information about a specific task:
        tsctl celery-tasks --task_id <task_id>

        # Show all active tasks:
        tsctl celery-tasks --active

        # Show all tasks (including pending, active, and failed):
        tsctl celery-tasks --show_all
    """
    celery = create_celery_app()

    if task_id:
        # Show information about a specific task
        task_result = AsyncResult(task_id, app=celery)
        print(f"Task ID: {task_id}")
        print(f"Status: {task_result.status}")
        if task_result.status == "FAILURE":
            print(f"Traceback: {task_result.traceback}")
        if task_result.status == "SUCCESS":
            print(f"Result: {task_result.result}")
        return

    # Show a list of tasks
    inspector = celery.control.inspect()

    if active:
        active_tasks = inspector.active()
        if not active_tasks:
            print("No active tasks found.")
            return
        table_data = [["Task ID", "Name", "Time Start", "Worker name"]]
        for worker_name, tasks in active_tasks.items():
            for task in tasks:
                table_data.append(
                    [
                        task["id"],
                        task["name"],
                        time.strftime(
                            "%Y-%m-%d %H:%M:%S", time.localtime(task["time_start"])
                        ),
                        worker_name,
                    ]
                )
        print_table(table_data)
        return

    if show_all:
        # Show all tasks (active, pending, reserved, scheduled, failed)
        all_tasks = {}
        all_tasks.update(inspector.active() or {})
        all_tasks.update(inspector.reserved() or {})
        all_tasks.update(inspector.scheduled() or {})

        if not all_tasks:
            print("No tasks found.")
            return

        table_data = [["Task ID", "Name", "Status", "Time Start", "Worker name"]]
        for worker_name, tasks in all_tasks.items():
            for task in tasks:
                task_id = task["id"]
                task_result = AsyncResult(task_id, app=celery)
                status = task_result.status
                time_start = task.get("time_start", "N/A")
                if time_start != "N/A":
                    time_start = time.strftime(
                        "%Y-%m-%d %H:%M:%S", time.localtime(time_start)
                    )
                table_data.append(
                    [
                        task_id,
                        task["name"],
                        status,
                        time_start,
                        worker_name,
                    ]
                )
        print_table(table_data)
        return

    print("Please use --active or --show_all to show tasks")


@cli.command(name="celery-revoke-task")
@click.argument("task_id")
def celery_revoke_task(task_id):
    """Revoke (cancel) a Celery task.

     This command attempts to revoke a running Celery task, effectively
    canceling its execution.  It uses the task ID to identify the specific
    task to revoke. If the task is successfully revoked, a confirmation
    message is printed. If an error occurs during the revocation process,
    an error message is displayed.

    Args:
        task_id (str): The ID of the Celery task to revoke.

    Raises:
        Exception: If there is an error communicating with Celery or if the
            task cannot be revoked.

    """
    celery = create_celery_app()
    try:
        celery.control.revoke(task_id, terminate=True)
        print(f"Task {task_id} has been revoked.")
    except Exception as e:  # pylint: disable=broad-except
        print(f"Error revoking task {task_id}: {e}")


@cli.command(name="list-config")
def list_config():
    """List all configuration variables loaded by the Flask application.

    This command iterates through the application's configuration dictionary
    (current_app.config). It identifies keys associated with potentially
    sensitive information (e.g., passwords, API keys, secrets) based on a
    predefined list of keywords.

    The values corresponding to these sensitive keys are redacted and replaced
    with '******** (redacted)' before printing. All other configuration
    key-value pairs are printed as they are.

    The output is formatted for readability, showing each configuration key
    followed by its (potentially redacted) value.
    """
    print("Timesketch Configuration Variables:")
    print("-" * 35)
    # Keywords/patterns to identify sensitive keys (case-insensitive)
    sensitive_keywords = [
        "SECRET",
        "PASSWORD",
        "API_KEY",
        "TOKEN",
        "CREDENTIALS",
        "AUTH",
        "KEYFILE",
        "SQLALCHEMY_DATABASE_URI",
    ]

    # Compile a regex pattern for efficiency
    sensitive_pattern = re.compile("|".join(sensitive_keywords), re.IGNORECASE)

    # Sort items for consistent output
    config_items = sorted(current_app.config.items())
    for key, value in config_items:
        display_value = value

        # Check if the key matches any sensitive patterns
        if sensitive_pattern.search(key):
            display_value = "******** (redacted)"

        print(f"{key}: {display_value}")
    print("-" * 35)
    print("Note: Some values might be sensitive (e.g., SECRET_KEY, passwords).")


def _isoformat_or_none(dt: Optional[datetime.datetime]) -> Optional[str]:
    """Return ISO format of a datetime object, or None if the object is None.

    Example:
        _isoformat_or_none(datetime.datetime.now()) == '2024-01-01T12:00:00'
    """
    return dt.isoformat() if dt else None


# Helper function to gather sketch metadata
def _get_sketch_metadata(sketch: Sketch) -> dict:
    """Gathers comprehensive metadata for a given Timesketch sketch.
    This function collects various details about the sketch, its associated
    objects (timelines, views, stories, aggregations, etc.), permissions,
    and export context into a structured dictionary.
    Args:
        sketch: The timesketch.models.sketch.Sketch object to extract metadata from.
    Returns:
        A dictionary containing metadata about the sketch, including:
            - Basic sketch info (ID, name, description, status, timestamps, owner).
            - Permissions and sharing details.
            - List of associated timelines with their details (including data sources).
            - List of saved views (name, query, filter, DSL).
            - List of stories (title, content).
            - List of aggregations and aggregation groups.
            - List of saved graphs.
            - List of analysis sessions.
            - List of DFIQ scenarios (including nested facets, questions, etc.).
            - Sketch attributes.
            - Export timestamp and Timesketch version.
            - Comments.
    """
    # Schemas for marshalling, from the API resource mixin
    schemas = ResourceMixin.fields_registry
    print("Gathering metadata...")
    metadata = {
        "sketch_id": sketch.id,
        "name": sketch.name,
        "description": sketch.description,
        "status": sketch.get_status.status,
        "created_at": _isoformat_or_none(sketch.created_at),
        "updated_at": _isoformat_or_none(sketch.updated_at),
        "created_by": sketch.user.username if sketch.user else None,
        "is_public": bool(sketch.is_public),
        "labels": [label.label for label in sketch.labels],
        "all_permissions": sketch.get_all_permissions(),
        "timelines": [],
        "views": [],
        "stories": [],
        "aggregations": [],
        "aggregation_groups": [],
        "graphs": [],
        "analysis_sessions": [],
        "scenarios": [],
        "comments": [],
        "attributes": api_utils.get_sketch_attributes(sketch),
        "export_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "timesketch_version": version.get_version(),
    }

    # Timelines
    for timeline in sketch.timelines:
        marshalled_timeline = marshal(timeline, schemas["timeline"])
        metadata["timelines"].append(marshalled_timeline)

    # Views
    for view in sketch.get_named_views:
        marshalled_view = marshal(view, schemas["view"])
        metadata["views"].append(marshalled_view)

    # Stories
    for story in sketch.stories:
        marshalled_story = marshal(story, schemas["story"])
        metadata["stories"].append(marshalled_story)

    # Aggregations
    for agg in sketch.aggregations:
        marshalled_agg = marshal(agg, schemas["aggregation"])
        metadata["aggregations"].append(marshalled_agg)

    # Aggregation Groups
    for group in sketch.aggregationgroups:
        marshalled_group = marshal(group, schemas["aggregationgroup"])
        metadata["aggregation_groups"].append(marshalled_group)

    # Graphs
    for graph in sketch.graphs:
        marshalled_graph = marshal(graph, schemas["graph"])
        metadata["graphs"].append(marshalled_graph)

    # Comments
    # Fetch Event DB objects that are part of the sketch and have comments.
    events_with_comments_list = Event.get_with_comments(sketch=sketch).all()

    if events_with_comments_list:
        print(f"  Processing comments for {len(events_with_comments_list)} event(s)...")
        for db_event_with_comment in events_with_comments_list:
            for comment_obj in db_event_with_comment.comments:
                metadata["comments"].append(
                    {
                        "id": comment_obj.id,  # Comment's own SQL PK
                        "comment": comment_obj.comment,
                        "user": (
                            comment_obj.user.username if comment_obj.user else None
                        ),
                        "created_at": _isoformat_or_none(comment_obj.created_at),
                        "updated_at": _isoformat_or_none(comment_obj.updated_at),
                        # SQL PK of the Event object
                        "event_id": db_event_with_comment.id,
                        # OpenSearch _id
                        "event_uuid": db_event_with_comment.document_id,
                    }
                )
    else:
        print("  No events with comments found for this sketch.")

    # Analysis Sessions (and their analyses)
    # Assuming AnalysisSession has a 'sketch' backref or can be queried via sketch
    # A more robust query might be needed if direct sketch_id isn't on AnalysisSession
    # For example, joining through Analysis and Timeline if sessions are per timeline.
    # This example assumes a direct or easily derivable link.
    analysis_sessions = (
        AnalysisSession.query.join(Analysis)
        .join(Timeline)
        .filter(Timeline.sketch_id == sketch.id)
        .distinct()
        .all()
    )
    for session in analysis_sessions:
        metadata["analysis_sessions"].append(
            marshal(session, schemas["analysissession"])
        )

    # DFIQ Scenarios (and their nested facets, questions, etc.)
    for scenario in sketch.scenarios:
        metadata["scenarios"].append(marshal(scenario, schemas["scenario"]))

    return metadata


# Helper function to fetch and prepare event data
def _fetch_and_prepare_event_data(
    sketch: Sketch, datastore: OpenSearchDataStore, return_fields: list
) -> tuple[str, bool]:
    """Fetches all event data for a sketch and determines its format.
    This function queries the datastore for all events associated with the
    active timelines of the given sketch. It requests the data ideally in
    JSONL format using the `api_export.query_to_filehandle` utility.
    After fetching, it reads the entire content, ensures it's a string (decoding
    from UTF-8 if necessary), and attempts to detect if the content is
    JSONL by checking if it starts with '{' and if the first line can be
    successfully parsed as JSON. This detection helps downstream functions
    handle potential format discrepancies (e.g., if the API returned CSV
    instead of the requested JSONL).
    Args:
        sketch: The timesketch.models.sketch.Sketch object whose events
                are to be fetched.
        datastore: An initialized
                    timesketch.lib.datastores.opensearch.OpenSearchDataStore
                    instance used for querying.
        return_fields: A list of field names to include in the fetched events.
    Returns:
        A tuple containing:
            - input_content (str): The fetched event data as a single string,
                                   stripped of leading/trailing whitespace.
                                   Will be an empty string if fetching fails or
                                   no data is returned.
            - is_likely_jsonl (bool): True if the fetched content starts with '{'
                                      and the first line parses as JSON,
                                      False otherwise.
    Raises:
        ValueError: If no active timelines or valid indices are found for the
                    sketch, preventing event fetching.
        # Note: Other exceptions from the datastore interaction or file reading
        # are caught and logged, resulting in an empty string return value.
    """
    query_string = "*"
    query_filter = {
        "indices": "_all",
        "size": 10000,  # Use default size, export handles scrolling
    }
    query_dsl = None

    indices, _ = lib_utils.get_validated_indices("_all", sketch)
    if not indices:
        indices = [t.searchindex.index_name for t in sketch.active_timelines]
        if not indices:
            raise ValueError(
                "ERROR: No active timelines (and thus no indices) found"
                "for this sketch."
            )

    active_indices = list({t.searchindex.index_name for t in sketch.active_timelines})
    if not active_indices:
        raise ValueError(
            "ERROR: No active timelines (and thus no indices) found for this sketch."
        )

    print("Get number of events for this sketch...")
    try:
        total_event_count, _ = datastore.count(active_indices)
        print(f"  Total events in active timelines: {total_event_count:,}")
    except Exception as count_error:  # pylint: disable=broad-except
        total_event_count = 0
        print(f"  WARNING: Could not get total event count: {count_error}")

    print("  Requesting event data (preferring JSONL)...")
    # TODO: Use PIT, search_after and slicing to improve performance
    event_file_handle = api_export.query_to_filehandle(
        query_string=query_string,
        query_filter=query_filter,
        query_dsl=query_dsl,
        indices=indices,
        sketch=sketch,
        datastore=datastore,
        return_fields=return_fields,
    )
    event_file_handle.seek(0)

    try:
        # TODO(jaegeral): A streaming approach (reading, converting, and writing
        #  to the zip archive line-by-line or in chunks) would be more
        # memory-efficient but also significantly more complex to implement
        content_str = event_file_handle.read()
        if not isinstance(content_str, str):
            content_str = content_str.decode("utf-8", errors="replace")
    except Exception as read_err:  # pylint: disable=broad-except
        print(f"  ERROR reading event data stream: {read_err}")
        content_str = ""

    input_content = content_str.strip()
    is_likely_jsonl = False
    if input_content and input_content.startswith("{"):
        try:
            first_line = input_content.split("\n", 1)[0]
            json.loads(first_line)
            is_likely_jsonl = True
            print("  Detected JSONL format in response.")
        except Exception:  # pylint: disable=broad-except
            is_likely_jsonl = False
            print("  Detected non-JSONL format in response (assuming CSV).")
    elif input_content:
        print("  Detected non-JSONL format in response (assuming CSV).")
    else:
        print("  WARNING: Received empty content from export function.")

    return input_content, is_likely_jsonl


# Helper function to convert event data
def _convert_event_data(
    input_content: str,
    is_likely_jsonl: bool,
    output_format: str,
    return_fields: list,
) -> bytes:
    """Converts fetched event data between JSONL and CSV formats.
    This function takes the raw event data string, determines the necessary
    conversion based on the detected input format (`is_likely_jsonl`) and the
    desired `output_format`, and performs the conversion.
    - If the input is JSONL and the output is CSV, it parses each JSON line,
      extracts relevant fields, and writes to a CSV structure. List values are
      represented as `[value1, value2]` (e.g., `["foo", "bar"]`) and empty lists
      (e.g., an empty "tag" field) as `[]`.
    - If the input is CSV and the output is JSONL, it reads the CSV, attempts
      basic type inference (int, float, bool) for values, and writes each row
      as a JSON line. It also attempts to sniff the CSV dialect.
    - If the input and output formats match, it returns the input content
      encoded directly.
    Warnings are printed for skipped lines or conversion issues. Errors during
    critical conversion steps (like parsing the first line for CSV headers or
    major CSV/JSONL conversion failures) will raise exceptions.
    Args:
        input_content: The fetched event data as a single string, stripped of
                       leading/trailing whitespace.
        is_likely_jsonl: Boolean flag indicating if the `input_content` is
                         detected as JSONL format.
        output_format: The target format for the event data ('csv' or 'jsonl').
        return_fields: A list of field names expected in the output. Primarily
                       used to determine headers when converting JSONL to CSV
                       if the `return_fields` option was specified for the export.
    Returns:
        A bytes object containing the event data in the specified `output_format`,
        encoded in UTF-8. Returns empty bytes if `input_content` is empty.
    Raises:
        ValueError: If no valid JSON lines are found when converting JSONL to CSV.
        json.JSONDecodeError: If parsing the first JSON line for CSV headers fails.
        Exception: Propagates exceptions from underlying CSV/JSON processing or
                   other unexpected errors during conversion.
    """
    event_data_bytes = b""

    if not input_content:
        print(f"  WARNING: No event data returned to format as {output_format}.")
        return event_data_bytes

    if output_format == "csv":
        if is_likely_jsonl:
            print("  Input is JSONL, converting to CSV...")
            jsonl_data = input_content.split("\n")
            output_csv = io.StringIO()
            try:
                first_valid_line_index = -1
                for i, line in enumerate(jsonl_data):
                    if line.strip():
                        first_valid_line_index = i
                        break

                if first_valid_line_index == -1:
                    raise ValueError("No valid JSON lines found for CSV conversion.")

                first_event = json.loads(jsonl_data[first_valid_line_index])

                if return_fields:
                    fieldnames = [f for f in return_fields if f in first_event]
                    if not fieldnames:
                        print(
                            "  WARNING: return_fields did not match event keys,"
                            " using all keys."
                        )
                        fieldnames = sorted(first_event.keys())
                else:
                    fieldnames = sorted(first_event.keys())

                writer = csv.DictWriter(
                    output_csv, fieldnames=fieldnames, extrasaction="ignore"
                )
                writer.writeheader()

                for line in jsonl_data:
                    line = line.strip()
                    if line:
                        try:
                            event_dict = json.loads(line)
                            csv_row = {}
                            for key in fieldnames:
                                value = event_dict.get(key)
                                if isinstance(value, list):
                                    csv_row[key] = f"[{', '.join(map(str, value))}]"
                                elif value is None:
                                    csv_row[key] = ""
                                else:
                                    csv_row[key] = str(value)
                            writer.writerow(csv_row)
                        except json.JSONDecodeError:
                            print(
                                f"  WARNING: Skipping invalid JSON line: {line[:100]}..."  # pylint: disable=line-too-long
                            )
                        except Exception as row_err:  # pylint: disable=broad-except
                            print(
                                f"  WARNING: Error processing row: {row_err}"
                                f" - Line: {line[:100]}..."
                            )

                event_data_bytes = output_csv.getvalue().encode("utf-8")

            except json.JSONDecodeError as first_line_error:
                print(
                    f"  ERROR parsing first JSON line for CSV headers: {first_line_error}"  # pylint: disable=line-too-long
                )
                print(
                    f"  Content of first line:"
                    f"{jsonl_data[first_valid_line_index][:200]}..."
                )
                print(traceback.format_exc())
                raise  # Re-raise to stop execution
            except Exception as conversion_error:  # pylint: disable=broad-except
                print(f"  ERROR converting JSONL to CSV: {conversion_error}")
                print(traceback.format_exc())
                raise  # Re-raise to stop execution
        else:
            print("  Input is not JSONL, using as CSV...")
            event_data_bytes = input_content.encode("utf-8")

    elif output_format == "jsonl":
        if is_likely_jsonl:
            print("  Input is JSONL, using as is...")
            event_data_bytes = input_content.encode("utf-8")
        else:
            print("  Input is not JSONL, converting CSV to JSONL...")
            try:
                csv_input = io.StringIO(input_content)
                try:
                    dialect = csv.Sniffer().sniff(csv_input.read(1024))
                    csv_input.seek(0)
                    reader = csv.DictReader(csv_input, dialect=dialect)
                    print(
                        f"    Detected CSV dialect: delimiter='{dialect.delimiter}'"
                    )  # pylint: disable=line-too-long
                except csv.Error:
                    print(
                        "    Could not detect CSV dialect, assuming comma delimiter."
                    )  # pylint: disable=line-too-long
                    csv_input.seek(0)
                    reader = csv.DictReader(csv_input)

                output_jsonl = io.StringIO()
                count = 0
                for row in reader:
                    processed_row = {}
                    for key, value in row.items():
                        try:
                            processed_row[key] = int(value)
                            continue
                        except (ValueError, TypeError):
                            pass
                        try:
                            processed_row[key] = float(value)
                            continue
                        except (ValueError, TypeError):
                            pass
                        if isinstance(value, str):
                            if value.lower() == "true":
                                processed_row[key] = True
                                continue
                            if value.lower() == "false":
                                processed_row[key] = False
                                continue
                        processed_row[key] = value

                    output_jsonl.write(json.dumps(processed_row) + "\n")
                    count += 1

                event_data_bytes = output_jsonl.getvalue().encode("utf-8")
                print(f"    Successfully converted {count} CSV rows to JSONL.")

            except Exception as conversion_error:  # pylint: disable=broad-except
                print(f"  ERROR converting CSV to JSONL: {conversion_error}")
                print(traceback.format_exc())
                raise  # Re-raise to stop execution

    return event_data_bytes


# Helper function to create the zip archive
# TODO(jaegeral): https://github.com/google/timesketch/issues/3415
def _create_export_archive(
    filename: str, metadata: dict, event_data_bytes: bytes, event_filename: str
):
    """Creates the zip archive with metadata and event data."""
    print("Creating zip archive...")
    try:
        with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as zipf:
            metadata_bytes = json.dumps(metadata, indent=2, ensure_ascii=False).encode(
                "utf-8"
            )
            zipf.writestr(DEFAULT_EXPORT_METADATA_FILENAME, metadata_bytes)

            if event_data_bytes:
                zipf.writestr(event_filename, event_data_bytes)
            else:
                print("  WARNING: No event data was generated to include in the zip.")

        print(f"Sketch exported successfully to {filename}")

    except Exception as zip_error:  # pylint: disable=broad-except
        print(f"ERROR creating zip file: {zip_error}")
        print(traceback.format_exc())


# --- Main CLI command using the helper functions ---
@cli.command(name="export-sketch")
@click.argument("sketch_id", type=int)
@click.option(
    "--output-format",
    type=click.Choice(["csv", "jsonl"], case_sensitive=False),
    default="csv",
    help="Format for event data export (csv or jsonl). Default: csv",
)
@click.option(
    "--filename",
    required=False,
    help=(
        "Filename for the output zip archive. "
        f"(Default: {DEFAULT_EXPORT_ARCHIVE_FILENAME_TEMPLATE})"
    ),
)
@click.option(
    "--default-fields",
    is_flag=True,
    default=False,  # Default is now False, meaning all fields are exported by default
    help=(
        "Export only the default set of event fields. "
        "If not specified, all fields are exported."
    ),
)
def export_sketch(
    sketch_id: int, output_format: str, filename: str, default_fields: bool
):
    """Exports a Timesketch sketch to a zip archive.

    The archive includes sketch metadata (as 'metadata.json') and all associated
    events, formatted as specified (CSV or JSONL). By default, only a predefined
    set of common fields are exported. Use the --default-fields flag to export
    only the default set of fields.
    Progress messages are printed to the console
    during the export process.

    **WARNING:** Re-importing this archive into Timesketch is not natively
    supported. This export is primarily for data archival, external analysis,
    or manual migration.

    Note: When running this command within a container (e.g., Docker),
    the output zip file is written inside the container's filesystem.
    Ensure you write to a mounted volume or copy the file out of the
    container afterwards.
    """
    sketch = sketch = Sketch.get_by_id(sketch_id)
    if not sketch:
        print(f"ERROR: Sketch with ID {sketch_id} not found.")
        return

    if not filename:
        filename = DEFAULT_EXPORT_ARCHIVE_FILENAME_TEMPLATE.format(
            sketch_id=sketch_id, output_format=output_format
        )

    if not filename.lower().endswith(".zip"):
        filename += ".zip"

    print(f'Exporting sketch [{sketch_id}] "{sketch.name}" to {filename}...')

    # --- Add prominent warning to console output ---
    click.echo(
        click.style(
            "\nWARNING: There is currently no native method to re-import "
            "this exported archive back into Timesketch.\n",
            fg="yellow",
            bold=True,
        ),
        err=True,  # Print to stderr to make it more noticeable
    )
    # --- End warning ---

    try:
        # 1. Gather Metadata
        metadata = _get_sketch_metadata(sketch)

        # 2. Fetch and Prepare Event Data
        # Get datastore instance
        datastore = OpenSearchDataStore(
            host=current_app.config["OPENSEARCH_HOST"],
            port=current_app.config["OPENSEARCH_PORT"],
        )

        if default_fields:
            print(
                f"  Exporting default fields only: {', '.join(DEFAULT_SOURCE_FIELDS)}"
            )
            return_fields_to_fetch = DEFAULT_SOURCE_FIELDS
        else:
            print("  Exporting all event fields.")
            return_fields_to_fetch = None  # Pass None to get all fields

        input_content, is_likely_jsonl = _fetch_and_prepare_event_data(
            sketch, datastore, return_fields_to_fetch
        )

        # 3. Convert Event Data
        event_data_bytes = _convert_event_data(
            input_content, is_likely_jsonl, output_format, return_fields_to_fetch
        )
        event_filename = DEFAULT_EXPORT_EVENTS_FILENAME_TEMPLATE.format(
            output_format=output_format
        )

        # 4. Create Zip Archive
        _create_export_archive(filename, metadata, event_data_bytes, event_filename)

    except ValueError as ve:  # Catch specific errors raised by helpers
        print(f"ERROR: {ve}")
        return
    except Exception as e:  # pylint: disable=broad-except
        print(f"An unexpected error occurred during export: {e}")
        print(traceback.format_exc())
        return
