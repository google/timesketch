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
import time
import io
import zipfile
import subprocess
import csv
import datetime
import traceback
from typing import Optional
import yaml
import redis


import sqlalchemy
import click
import pandas as pd
from flask_restful import marshal
from flask import current_app
from flask.cli import FlaskGroup
from sqlalchemy import distinct
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException
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
from timesketch.models import db_session, drop_all, init_db, BaseModel
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Analysis
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sigma import SigmaRule
from timesketch.models.sketch import (
    Timeline,
    View,
    Event,
    Story,
    Aggregation,
    Attribute,
    Graph,
    GraphCache,
    AggregationGroup,
    AnalysisSession,
    SearchHistory,
    Scenario,
    Facet,
    InvestigativeQuestion,
    DataSource,
    AttributeValue,
    FacetTimeFrame,
    FacetConclusion,
    InvestigativeQuestionApproach,
    InvestigativeQuestionConclusion,
    SearchIndex,
)  # For mixin checks
from timesketch.models.user import Group, User

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
@click.option("--read-only", is_flag=True, help="Grant only read access to the sketch.")
def grant_user(username, sketch_id, read_only):
    """Grant a user access to a specific sketch.

    This command allows an administrator to grant permissions to a user
    for a given sketch. By default, both 'read' and 'write' permissions
    are granted. If the '--read-only' flag is provided, only 'read'
    permission will be granted.

    Args:
        username (str): The username of the user to grant access to.
        sketch_id (int): The ID of the sketch to grant access to.
        read_only (bool): If True, grants only 'read' permission.
                          Otherwise, grants 'read' and 'write' permissions.

    Prints a confirmation message upon success or an error message
    if the user or sketch does not exist.
    """
    sketch = Sketch.get_by_id(sketch_id)
    user = User.query.filter_by(username=username).first()
    if not sketch:
        print("Sketch does not exist.")
        return
    if not user:
        print(f"User {username} does not exist.")
        return

    sketch.grant_permission(permission="read", user=user)
    if not read_only:
        sketch.grant_permission(permission="write", user=user)
    print(f"User {username} added to the sketch {sketch.id} ({sketch.name})")


@cli.command(name="grant-group")
@click.argument("group_name")
@click.option("--sketch_id", type=int, required=True)
@click.option("--read-only", is_flag=True, help="Grant only read access to the sketch.")
def grant_group(group_name, sketch_id, read_only):
    """Grant a group access to a specific sketch.

    This command allows an administrator to grant permissions to a group
    for a given sketch. By default, both 'read' and 'write' permissions
    are granted. If the '--read-only' flag is provided, only 'read'
    permission will be granted.

    Args:
        group_name (str): The name of the group to grant access to.
        sketch_id (int): The ID of the sketch to grant access to.
        read_only (bool): If True, grants only 'read' permission.
                          Otherwise, grants 'read' and 'write' permissions.

    Prints a confirmation message upon success or an error message
    if the group or sketch does not exist.
    """
    sketch = Sketch.get_by_id(sketch_id)
    group = Group.query.filter_by(name=group_name).first()
    if not sketch:
        print("Sketch does not exist.")
        return
    if not group:
        print(f"Group {group_name} does not exist.")
        return
    sketch.grant_permission(permission="read", group=group)
    if not read_only:
        sketch.grant_permission(permission="write", group=group)
    print(f"Group {group_name} added to the sketch {sketch.id} ({sketch.name})")


@cli.command(name="version")
def get_version():
    """Return the version information of Timesketch."""
    timesketch_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(timesketch_path, ".."))
    git_dir = os.path.join(project_root, ".git")
    version_string = version.__version__

    if os.path.isdir(git_dir):
        try:
            # Get the short commit hash
            p_hash = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=project_root,
                check=False,
            )
            if p_hash.returncode == 0 and p_hash.stdout:
                version_string = p_hash.stdout.strip()

                # Check if the repository is dirty (has uncommitted changes)
                p_dirty = subprocess.run(
                    ["git", "status", "--porcelain"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=project_root,
                    check=False,
                )
                if p_dirty.returncode == 0 and p_dirty.stdout:
                    version_string += "-dirty"
        except OSError:
            # Not a git repo or git is not installed.
            pass

    print(f"Timesketch version: {version_string}")


@cli.command(name="drop-db")
def drop_db():
    """Permanently remove all database tables.

    This action is irreversible and will result in the loss of all data
    stored in the Timesketch database, including users, sketches, timelines,
    and all associated metadata. Use with extreme caution.
    """
    if click.confirm("Do you really want to drop all the database tables?"):
        if click.confirm(
            "Are you REALLLY sure you want to DROP ALL the database tables?"
        ):
            drop_all()
            print("All tables dropped. Database is now empty.")


@cli.command(name="list-sketches")
@click.option(
    "--archived",
    is_flag=True,
    help="Show only archived sketches. Mutually exclusive with --archived-with-open-indexes.",  # pylint: disable=line-too-long
)
@click.option(
    "--archived-with-open-indexes",
    is_flag=True,
    help="Show archived sketches that have at least one searchindex with status "
    "'new', 'ready', 'processing', 'fail','archived' or 'timeout'. "
    "Mutually exclusive with --archived. This will query OpenSearch.",
)
@click.option(
    "--include-deleted",
    is_flag=True,
    help="Include deleted sketches. Default: deleted sketches are hidden.",
)
def list_sketches(
    archived: bool, archived_with_open_indexes: bool, include_deleted: bool
):
    """List sketches.

    By default, this command lists all sketches that have not been deleted.

    - If the --archived flag is provided, it will only list sketches
      that have an 'archived' status.

    - If the --archived-with-open-indexes flag is provided, it will list
      archived sketches that have one or more associated SearchIndex database
      objects with a status of 'new', 'ready', 'processing', 'fail', or 'timeout'.

    - If the --include-deleted flag is provided, sketches marked as 'deleted'
      will also be included in the list, respecting other filters like --archived.
    """
    # Initialize the datastore client if needed for OpenSearch checks.
    datastore = None
    if archived_with_open_indexes:
        datastore = OpenSearchDataStore()
    all_sketches = Sketch.query.all()

    if archived and archived_with_open_indexes:
        raise click.UsageError(
            "The options --archived and --archived-with-open-indexes "
            "are mutually exclusive. Please use only one."
        )

    # SearchIndex statuses that indicate it's not properly closed/archived
    open_index_statuses = ["new", "ready", "processing", "fail", "timeout"]

    if archived_with_open_indexes:
        open_statuses_str = ", ".join(open_index_statuses)
        click.echo(
            "Searching for archived sketches with 'open' SearchIndex DB statuses "
            f"({open_statuses_str}) OR indices that are actually open in OpenSearch..."
        )

        found_sketches_info = []

        for sketch in all_sketches:
            if sketch.get_status.status != "archived":
                continue

            sketch_inconsistency_details = []
            indices_to_check_in_os = set()

            for tl in sketch.timelines:
                if tl.searchindex:
                    si = tl.searchindex
                    si_status = si.get_status.status
                    if si_status in open_index_statuses:
                        sketch_inconsistency_details.append(
                            f"  - Timeline: '{tl.name}' (ID: {tl.id}), "
                            f"SearchIndex DB: '{si.index_name}' (ID: {si.id}), "
                            f"DB Status: '{si_status}' (Inconsistent)"
                        )
                    else:
                        # If DB status is 'archived', add to list for OS check.
                        indices_to_check_in_os.add(si.index_name)

            if indices_to_check_in_os:
                try:
                    # Check the actual status of these indices in OpenSearch
                    # pylint: disable=unexpected-keyword-arg
                    indices_status = datastore.client.indices.get(
                        index=list(indices_to_check_in_os), features="settings"
                    )
                    # pylint: enable=unexpected-keyword-arg
                    for index_name, status_info in indices_status.items():
                        is_closed = (
                            status_info.get("settings", {})
                            .get("index", {})
                            .get("verified_before_close")
                            == "true"
                        )
                        if not is_closed:
                            sketch_inconsistency_details.append(
                                f"  - SearchIndex DB: '{index_name}' is marked "
                                "'archived' in DB, but is OPEN in OpenSearch."
                            )
                except Exception as e:  # pylint: disable=broad-except
                    click.echo(f"ERROR checking OpenSearch for indices: {e}", err=True)

            if sketch_inconsistency_details:
                found_sketches_info.append(
                    {
                        "sketch_id": sketch.id,
                        "sketch_name": sketch.name,
                        "details": sketch_inconsistency_details,
                    }
                )

        if not found_sketches_info:
            print("No archived sketches with inconsistent index statuses found.")
        else:
            print("Archived sketches with inconsistent index statuses found:")
            for sk_info in found_sketches_info:
                print(
                    f"Sketch ID: {sk_info['sketch_id']}, Name: '{sk_info['sketch_name']}' (status: archived)"  # pylint: disable=line-too-long
                )
                for detail in sk_info["details"]:
                    print(detail)
        return

    # Handle default listing or --archived only
    sketches_to_display = []
    for sketch in all_sketches:
        current_status = sketch.get_status.status

        if current_status == "deleted" and not include_deleted:
            continue

        if archived:
            if current_status == "archived":
                sketches_to_display.append(sketch)
        else:
            sketches_to_display.append(sketch)

    output_type = ""
    if not sketches_to_display:
        if archived:
            print("No archived sketches found.")
        elif include_deleted:
            print("No sketches found (including deleted).")
        else:
            print("No sketches found (excluding deleted).")
        return

    if archived:
        output_type = "Archived sketches"
    elif include_deleted:
        output_type = "Sketches (including deleted, ready, and archived)"
    else:  # Default
        output_type = "Sketches (excluding deleted; i.e., ready and archived)"

    print(f"{output_type}:")
    for sketch in sketches_to_display:
        print(f"{sketch.id} '{sketch.name}' (status: {sketch.get_status.status})")


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
    """Display detailed information about the Timesketch environment.

    This command provides a comprehensive overview of the Timesketch installation
    and its environment, including version information, commit details (if
    applicable), and the versions of key dependencies.

    The output includes:
        - Timesketch version and, if available, the Git commit hash (with a
          "-dirty" suffix if there are uncommitted changes).
        - Versions of essential tools like psort (from Plaso), Node.js, npm, yarn,
          Python, and pip.
    """
    print(f"Timesketch version: {version.get_version()}")  # Displays Timesketch version

    timesketch_path = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(
        os.path.join(timesketch_path, "..")
    )  # Project root directory
    git_dir = os.path.join(project_root, ".git")  # Path to the .git directory
    if os.path.isdir(git_dir):
        try:
            # Get the short commit hash
            p_hash = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True,
                text=True,
                cwd=project_root,
                check=False,
            )
            if (
                p_hash.returncode == 0 and p_hash.stdout
            ):  # Check for successful git execution and output
                commit_hash = p_hash.stdout.strip()

                # Check if the repository is dirty (has uncommitted changes)
                p_dirty = subprocess.run(
                    ["git", "status", "--porcelain"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=project_root,
                    check=False,
                )
                if p_dirty.returncode == 0 and p_dirty.stdout:
                    commit_hash += "-dirty"
                timesketch_commit = commit_hash
        except OSError:
            # Not a git repo or git is not installed.
            pass

        if timesketch_commit.endswith("-dirty"):
            timesketch_commit = timesketch_commit.replace("-dirty", "")
            print(f"Timesketch commit: {timesketch_commit} (dirty)")
        else:
            print(f"Timesketch commit: {timesketch_commit}")

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
    all_permissions = sketch.get_all_permissions()

    print("Shared with:")
    print("\tUsers: (user_id, username, access_level)")
    if sketch.collaborators:
        for user in sketch.collaborators:
            user_perm_key = f"user/{user.username}"
            perms = all_permissions.get(user_perm_key, [])
            access_level = "unknown"
            if "write" in perms:  # 'write' permission implies 'read'
                access_level = "read/write"
            elif "read" in perms:
                access_level = "read-only"
            else:
                access_level = "none"  # Should not happen if user is a collaborator
            print(f"\t\t{user.id}: {user.username} ({access_level})")
    else:
        print("\tNo users shared with.")

    print(f"\tGroups ({len(sketch.groups)}): (group_name, access_level)")
    if sketch.groups:
        for group in sketch.groups:
            group_perm_key = f"group/{group.name}"
            perms = all_permissions.get(group_perm_key, [])
            access_level = "unknown"
            if "write" in perms:  # 'write' permission implies 'read'
                access_level = "read/write"
            elif "read" in perms:
                access_level = "read-only"
            else:
                access_level = "none"  # Should not happen if group is listed
            print(f"\t\t{group.display_name} ({access_level})")
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


def _query_db_label_stats(sketch_id: int) -> list:
    """Query the relational database for label statistics."""
    print("\n[+] Querying Relational Database for 'timesketch_label'...")
    label_counts_db = []
    try:
        total_labeled_in_db = (
            db_session.query(distinct(Event.id))
            .filter(Event.sketch_id == sketch_id, Event.labels.any())
            .count()
        )
        print(f"  - Total events with at least one label: {total_labeled_in_db}")

        label_counts_db = (
            db_session.query(Event.Label.label, func.count(Event.id))
            .join(Event.labels)
            .filter(Event.sketch_id == sketch_id)
            .group_by(Event.Label.label)
            .order_by(func.count(Event.id).desc())
            .all()
        )

        if label_counts_db:
            print("  - Counts per label:")
            for label, count in label_counts_db:
                print(f"    - {label}: {count}")
        else:
            print("  - No individual label records found in the database.")
    except Exception as e:  # pylint: disable=broad-except
        print(f"  - ERROR querying database: {e}")
    return label_counts_db


def _query_os_label_stats_agg(
    sketch: Sketch, datastore: OpenSearchDataStore, indices: list, verbose: bool
) -> list:
    """Query OpenSearch for label stats using the aggregation API."""
    print("\n  -> Method 1: 'timesketch_label' counts using the Aggregation API")
    label_counts_agg = []
    try:
        query_dsl_total = {
            "query": {
                "nested": {
                    "path": "timesketch_label",
                    "query": {"term": {"timesketch_label.sketch_id": sketch.id}},
                }
            }
        }
        if verbose:
            print("    - Fetching all events with at least one label:")
            result = datastore.search(
                sketch_id=sketch.id, indices=indices, query_dsl=query_dsl_total
            )
            for event in result.get("hits", {}).get("hits", []):
                print(json.dumps(event, indent=2))
        else:
            total_labeled_os = datastore.search(
                sketch_id=sketch.id,
                indices=indices,
                query_dsl=query_dsl_total,
                count=True,
            )
            print(f"    - Total events with at least one label: {total_labeled_os}")

        label_counts_agg = datastore.get_filter_labels(sketch.id, indices)
        if label_counts_agg:
            print("    - Counts per label:")
            sorted_labels = sorted(
                label_counts_agg, key=lambda x: x["count"], reverse=True
            )
            for item in sorted_labels:
                print(f"      - {item['label']}: {item['count']}")
        else:
            print("    - No labels found via aggregation.")
    except Exception as e:  # pylint: disable=broad-except
        print(f"    - ERROR during aggregation query: {e}")
    return label_counts_agg


def _query_os_label_stats_search(
    sketch: Sketch,
    datastore: OpenSearchDataStore,
    indices: list,
    verbose: bool,
    label_counts_agg: list,
    label_counts_db: list,
):
    """Query OpenSearch for label stats using the search API."""
    print("\n  -> Method 2: 'timesketch_label' counts using the Search API")
    try:
        if label_counts_agg:
            labels_to_search = [item["label"] for item in label_counts_agg]
        else:
            labels_to_search = [label for label, _ in label_counts_db]

        if labels_to_search:
            if verbose:
                print("    - Events per label (iterative search):")
                for label in sorted(labels_to_search):
                    print(f"      --- Events for label: {label} ---")
                    query_filter = {"chips": [{"type": "label", "value": label}]}
                    result = datastore.search(
                        sketch_id=sketch.id,
                        indices=indices,
                        query_filter=query_filter,
                    )
                    for event in result.get("hits", {}).get("hits", []):
                        print(json.dumps(event, indent=2))
            else:
                print("    - Counts per label (iterative search):")
                for label in sorted(labels_to_search):
                    query_filter = {"chips": [{"type": "label", "value": label}]}
                    count = datastore.search(
                        sketch_id=sketch.id,
                        indices=indices,
                        query_filter=query_filter,
                        count=True,
                    )
                    print(f"      - {label}: {count}")
        else:
            print("    - No labels found to search for.")
    except Exception as e:  # pylint: disable=broad-except
        print(f"    - ERROR during search query: {e}")


def _query_os_tag_stats(
    sketch: Sketch, datastore: OpenSearchDataStore, indices: list, verbose: bool
):
    """Query OpenSearch for legacy 'tag' field statistics."""
    print("\n[+] Querying OpenSearch for legacy 'tag' field...")

    print("\n  -> Method 3: 'tag' count using Search API (query_string)")
    try:
        if verbose:
            print("    - Fetching all events with at least one tag:")
            result = datastore.search(
                sketch_id=sketch.id, indices=indices, query_string="_exists_:tag"
            )
            for event in result.get("hits", {}).get("hits", []):
                print(json.dumps(event, indent=2))
        else:
            total_tagged_events = datastore.search(
                sketch_id=sketch.id,
                indices=indices,
                query_string="_exists_:tag",
                count=True,
            )
            print(f"    - Total events with at least one tag: {total_tagged_events}")
    except Exception as e:  # pylint: disable=broad-except
        print(f"    - ERROR during search query: {e}")

    print("\n  -> Method 4: 'tag' counts using Aggregation API")
    try:
        agg_params = {"field": "tag.keyword", "limit": 100}
        result_obj, _ = api_utils.run_aggregator(
            sketch.id, "field_bucket", agg_params, indices=indices
        )
        tag_buckets = result_obj.to_dict().get("values", [])

        if tag_buckets:
            field_name = agg_params.get("field")
            if verbose:
                print("    - Events per tag (from aggregation results):")
                for bucket in tag_buckets:
                    tag = bucket[field_name]
                    print(f"      --- Events for tag: {tag} ---")
                    result = datastore.search(
                        sketch_id=sketch.id,
                        indices=indices,
                        query_string=f'tag:"{tag}"',
                    )
                    for event in result.get("hits", {}).get("hits", []):
                        print(json.dumps(event, indent=2))
            else:
                print("    - Counts per tag:")
                for bucket in tag_buckets:
                    print(f"      - {bucket[field_name]}: {bucket['count']}")
        else:
            print("    - No tags found via aggregation.")
    except Exception as e:  # pylint: disable=broad-except
        print(f"    - ERROR during aggregation query: {e}")


def _query_os_complex_example(
    sketch: Sketch, datastore: OpenSearchDataStore, indices: list, verbose: bool
):
    """Run and display a complex query example."""
    print("\n[+] Complex Query Example (Raw DSL)...")
    print("  -> Method 5: Count events with '__ts_star' but NOT '__ts_comment'")
    # pylint: disable=line-too-long
    try:
        complex_dsl = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "nested": {
                                "path": "timesketch_label",
                                "query": {
                                    "bool": {
                                        "must": [
                                            {
                                                "term": {
                                                    "timesketch_label.name.keyword": "__ts_star"
                                                }
                                            },
                                            {
                                                "term": {
                                                    "timesketch_label.sketch_id": sketch.id
                                                }
                                            },
                                        ]
                                    }
                                },
                            }
                        }
                    ],
                    "must_not": [
                        {
                            "nested": {
                                "path": "timesketch_label",
                                "query": {
                                    "bool": {
                                        "must": [
                                            {
                                                "term": {
                                                    "timesketch_label.name.keyword": "__ts_comment"
                                                }
                                            },
                                            {
                                                "term": {
                                                    "timesketch_label.sketch_id": sketch.id
                                                }
                                            },
                                        ]
                                    }
                                },
                            }
                        }
                    ],
                }
            }
        }
        # pylint: enable=line-too-long
        if verbose:
            print("    - Fetching events with '__ts_star' but NOT '__ts_comment':")
            result = datastore.search(
                sketch_id=sketch.id, indices=indices, query_dsl=complex_dsl
            )
            for event in result.get("hits", {}).get("hits", []):
                print(json.dumps(event, indent=2))
        else:
            complex_count = datastore.search(
                sketch_id=sketch.id, indices=indices, query_dsl=complex_dsl, count=True
            )
            print(f"    - Result: {complex_count} events")
    except Exception as e:  # pylint: disable=broad-except
        print(f"    - ERROR during complex DSL query: {e}")


@cli.command(name="sketch-label-stats")
@click.option("--sketch_id", type=int, required=True)
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help="Show full event data instead of just counts.",
)
def sketch_label_stats(sketch_id: int, verbose: bool):
    """Display label and tag statistics for a specific sketch.

    This command provides statistics on labeled and tagged events for a given
    sketch. It queries both the relational database and the OpenSearch
    datastore to provide a comprehensive view.

    The output includes:
    - Total count of events with at least one label/tag.
    - A breakdown of event counts for each individual label/tag.
    - An example of a complex query using raw DSL.

    Args:
        sketch_id (int): The ID of the sketch to analyze.
        verbose (bool): If true, show full event data instead of counts.
    """
    sketch = Sketch.get_by_id(sketch_id)
    if not sketch:
        print(f"Sketch with ID {sketch_id} not found.")
        return

    print(f"--- Label and Tag Stats for Sketch: '{sketch.name}' (ID: {sketch.id}) ---")

    label_counts_db = _query_db_label_stats(sketch_id)

    print("\n[+] Querying OpenSearch Datastore...")
    datastore = OpenSearchDataStore()
    indices = [t.searchindex.index_name for t in sketch.active_timelines]

    if not indices:
        print("  - No active timelines in this sketch to query in OpenSearch.")
        return

    label_counts_agg = _query_os_label_stats_agg(sketch, datastore, indices, verbose)

    _query_os_label_stats_search(
        sketch, datastore, indices, verbose, label_counts_agg, label_counts_db
    )

    _query_os_tag_stats(sketch, datastore, indices, verbose)

    _query_os_complex_example(sketch, datastore, indices, verbose)

    print("\n--- End of Stats ---")


@cli.command(name="event-details")
@click.option("--sketch-id", "--sketch_id", type=int, required=True)
@click.option("--event-id", "--event_id", type=str, required=True)
@click.option(
    "--searchindex-id",
    type=str,
    required=False,
    help="Optional: The OpenSearch index name for the event.",
)
def event_details(sketch_id: int, event_id: str, searchindex_id: Optional[str] = None):
    """Display all data for a specific event.

    This command retrieves and displays all available information for a single
    event, combining data from both the OpenSearch datastore and the relational
    database.

    The output includes:
    - The full JSON source of the event from OpenSearch.
    - Comments and labels from the Timesketch database.
    - Tags stored within the OpenSearch document.

    If the --searchindex-id is not provided, the command will automatically
    search for the event across all active timelines within the sketch.
    """
    sketch = Sketch.get_by_id(sketch_id)
    if not sketch:
        print(f"Sketch with ID {sketch_id} not found.")
        return

    datastore = OpenSearchDataStore()

    os_event_data = None
    if searchindex_id:
        try:
            os_event_data = datastore.get_event(searchindex_id, event_id)
        except HTTPException as e:
            print(f"Error getting event from OpenSearch: {e.description}")
            return
        except Exception as e:  # pylint: disable=broad-except
            print(f"An unexpected error occurred while fetching from OpenSearch: {e}")
            return
    else:
        print("No searchindex_id provided, searching across all sketch timelines...")
        for timeline in sketch.active_timelines:
            current_index = timeline.searchindex.index_name
            try:
                os_event_data = datastore.get_event(current_index, event_id)
                if os_event_data:
                    searchindex_id = current_index
                    print(f"Event found in index: {searchindex_id}")
                    break
            except HTTPException:
                continue  # Event not found in this index, try the next one.
            except Exception as e:  # pylint: disable=broad-except
                print(f"An error occurred while searching index {current_index}: {e}")

    if not os_event_data:
        print(f"Event with ID '{event_id}' not found in any of the sketch's timelines.")
        return

    print(
        f"--- Details for Event ID: {event_id} in Sketch: {sketch.name} ({sketch.id}) ---"  # pylint: disable=line-too-long
    )
    print(f"--- Index: {searchindex_id} ---")

    print("\n[+] OpenSearch Document:")
    print(json.dumps(os_event_data.get("_source", {}), indent=2))

    # 2. Get data from Database
    print("\n[+] Timesketch Database Information:")
    searchindex = SearchIndex.query.filter_by(index_name=searchindex_id).first()
    if not searchindex:
        print(f"  - SearchIndex '{searchindex_id}' not found in the database.")
        db_event = None
    else:
        # Check if searchindex is part of sketch
        is_in_sketch = any(
            tl.searchindex and tl.searchindex.index_name == searchindex_id
            for tl in sketch.timelines
        )
        if not is_in_sketch:
            print(
                f"  - WARNING: SearchIndex '{searchindex_id}' is not part of sketch '{sketch.name}' ({sketch.id})."  # pylint: disable=line-too-long
            )

        db_event = Event.query.filter_by(
            sketch=sketch, searchindex=searchindex, document_id=event_id
        ).first()

    if not db_event:
        print(
            "  - No corresponding event record found in the Timesketch database (no comments or labels)."  # pylint: disable=line-too-long
        )
    else:
        # Get comments
        if db_event.comments:
            print("  - Comments:")
            for comment in db_event.comments:
                username = comment.user.username if comment.user else "System"
                print(f"    - [{comment.created_at}] by {username}: {comment.comment}")
        else:
            print("  - No comments.")

        # Get labels
        if db_event.labels:
            print("  - Labels:")
            for label in db_event.labels:
                username = label.user.username if label.user else "System"
                print(f"    - [{label.created_at}] by {username}: {label.label}")
        else:
            print("  - No labels.")

    # 3. Get tags from OpenSearch document
    print("\n[+] Tags (from OpenSearch document):")
    tags = os_event_data.get("_source", {}).get("tag", [])
    if tags:
        for tag in tags:
            print(f"  - {tag}")
    else:
        print("  - No tags.")

    print("\n--- End of Details ---")


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

        print("\nData Sources:")
        if timeline.datasources:
            ds_table_data = [
                [
                    "ID",
                    "File Path",
                    "Status",
                    "Error Message",
                ],
            ]
            for ds in timeline.datasources:
                error_message = ds.error_message or "N/A"
                ds_table_data.append(
                    [
                        ds.id,
                        ds.file_on_disk,
                        (ds.status[-1].status if ds.status else "N/A"),
                        error_message,
                    ]
                )
            print_table(ds_table_data)
        else:
            print("No data sources found for this timeline.")

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
        print((f"To verify run: tsctl timeline-status {timeline_id} --action get"))


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

    print(
        f"Searchindex: {index_to_search.id} Name: {index_to_search.name}"
        f" [Status: {index_to_search.status[-1].status}] found"
    )

    timelines = index_to_search.timelines
    if timelines:
        print("Associated Timelines:")
        for timeline in timelines:
            print(
                f"  ID: {timeline.id}, Name: {timeline.name}"
                f"[Status: {timeline.status[-1].status}]"
            )
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
        print(
            (
                f"To verify run: tsctl searchindex-status "
                f"--searchindex_id {searchindex_id} --action get"
            )
        )


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
                                "  WARNING: Skipping invalid JSON line: "
                                f"{line[:100]}..."
                            )
                        except Exception as row_err:  # pylint: disable=broad-except
                            print(
                                f"  WARNING: Error processing row: {row_err} "
                                f"- Line: {line[:100]}..."
                            )

                event_data_bytes = output_csv.getvalue().encode("utf-8")

            except json.JSONDecodeError as first_line_error:
                print(
                    "  ERROR parsing first JSON line for CSV headers: "
                    f"{first_line_error}"
                )
                message = (
                    f"  Content of first line:"
                    f"{jsonl_data[first_valid_line_index][:200]}..."
                )
                print(message)
                print(traceback.format_exc())
                raise  # Re-raise to stop execution
            except Exception as conversion_error:  # pylint: disable=broad-except
                message = f"  ERROR converting JSONL to CSV: {conversion_error}"
                print(message)
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
                    message = (
                        f"    Detected CSV dialect: delimiter='{dialect.delimiter}'"
                    )
                    print(message)
                except csv.Error:
                    print("    Could not detect CSV dialect, assuming comma delimiter.")
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
        datastore = OpenSearchDataStore()

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


@cli.command(name="check-opensearch-links")
def check_opensearch_links():
    """Checks for broken links between the database and OpenSearch.

    This command iterates through all SearchIndex records in the database
    and verifies that the corresponding index exists in OpenSearch. It helps
    identify timelines that might be broken after an incomplete migration or
    accidental index deletion.
    """
    print("Checking for broken links to OpenSearch...")
    datastore = OpenSearchDataStore()
    search_indices = SearchIndex.query.all()

    if not search_indices:
        print("No search indices found in the database.")
        return

    # Collect all index names from the database for a single bulk check.
    db_index_names = {s.index_name for s in search_indices}

    try:
        # Get all existing indices from OpenSearch in a single API call.
        # ignore_unavailable=True is a valid argument
        # pylint: disable-next=unexpected-keyword-arg
        existing_indices_info = datastore.client.indices.get(
            index=list(db_index_names),
            ignore_unavailable=True,
        )
        existing_os_index_names = set(existing_indices_info.keys())

        # Determine which indices are in the DB but not in OpenSearch.
        missing_index_names = db_index_names - existing_os_index_names

        if not missing_index_names:
            print(
                "No broken links found. All database search"
                " indices exist in OpenSearch."
            )
            return

        # Create a map for quick lookup of original DB objects.
        search_indices_map = {s.index_name: s for s in search_indices}

        for index_name in sorted(list(missing_index_names)):
            search_index = search_indices_map.get(index_name)
            print(
                f"BROKEN LINK: DB record for index '{index_name}' "
                f"(ID: {search_index.id}) "
                f"exists, but the index is MISSING in OpenSearch."
            )
            for timeline in search_index.timelines:
                if timeline.sketch:
                    print(
                        f"  - Associated with Timeline '{timeline.name}'"
                        f" (ID: {timeline.id})"
                        f" in Sketch '{timeline.sketch.name}'"
                        f" (ID: {timeline.sketch.id})"
                    )
                else:
                    print(
                        f"  - Associated with Timeline '{timeline.name}' "
                        f"(ID: {timeline.id}) "
                        f"which has no associated sketch (orphaned)."
                    )
        print("\nCheck complete. Broken links found as listed above.")

    except Exception as e:  # pylint: disable=broad-except
        print(f"ERROR communicating with OpenSearch while checking indices: {e}")
        return


@cli.command(name="check-db-orphaned-data")
@click.option(
    "--verbose-checks",
    is_flag=True,
    default=False,
    help="Show output for all checks, even those that find no orphans.",
)
def check_db_orphaned_data(verbose_checks: bool):
    """Checks for various types of orphaned data in the database.

    This command looks for records that should have been deleted via
    cascading rules if their parent objects were removed, particularly
    in the context of a Sketch deletion or general database integrity.
    """
    print("Starting orphaned data check...")
    found_orphans_overall = False

    def _check_fk_orphans(
        ModelClass: type,
        fk_attr_name: str,
        ParentModelClass: type,
        description: str,
        verbose_checks_enabled: bool,
    ):
        nonlocal found_orphans_overall
        if verbose_checks_enabled:
            print(
                f"\nChecking for orphaned {description} "
                f"({ModelClass.__name__} records)..."
            )
        orphaned_count = 0
        all_records = ModelClass.query.all()

        if not all_records:
            if verbose_checks_enabled:
                print(f"  No {ModelClass.__name__} records found.")
            return

        for record in all_records:
            parent_id = getattr(record, fk_attr_name)
            if parent_id:
                parent = ParentModelClass.get_by_id(parent_id)
                if not parent:
                    # This is the first orphan found for this check type, print header
                    if orphaned_count == 0 and not verbose_checks_enabled:
                        print(
                            f"\nFound orphaned {description} "
                            f"({ModelClass.__name__} records):"
                        )

                    record_info_parts = [f"ID={record.id}"]
                    if hasattr(record, "name") and record.name:
                        record_info_parts.append(f"Name='{str(record.name)[:50]}'")
                    elif hasattr(record, "title") and record.title:
                        record_info_parts.append(f"Title='{str(record.title)[:50]}'")
                    elif (
                        hasattr(record, "original_filename")
                        and record.original_filename
                    ):
                        record_info_parts.append(
                            f"File='{str(record.original_filename)[:50]}'"
                        )
                    elif (
                        hasattr(record, "label")
                        and record.label
                        and isinstance(record.label, str)
                    ):
                        record_info_parts.append(f"LabelVal='{str(record.label)[:50]}'")
                    elif (
                        hasattr(record, "status")
                        and record.status
                        and isinstance(record.status, str)
                    ):
                        record_info_parts.append(
                            f"StatusVal='{str(record.status)[:50]}'"
                        )
                    elif (
                        hasattr(record, "comment")
                        and record.comment
                        and isinstance(record.comment, str)
                    ):
                        record_info_parts.append(
                            f"Comment='{str(record.comment)[:30]}...'"
                        )

                    record_info = ", ".join(record_info_parts)
                    print(
                        f"  ORPHANED {ModelClass.__name__}: {record_info}, "
                        "linked to "
                        f"non-existent {ParentModelClass.__name__} ID={parent_id} "
                        f"via {fk_attr_name}"
                    )

                    orphaned_count += 1
                    found_orphans_overall = True

        if orphaned_count == 0:
            if verbose_checks_enabled:
                print(f"  No orphaned {description} ({ModelClass.__name__}) found.")
        elif verbose_checks_enabled:  # Only print count if verbose and orphans found
            print(
                f"  Found {orphaned_count} orphaned {description} "
                f"({ModelClass.__name__}) record(s)."
            )

    # Define checks: (ModelClass, fk_attr_name, ParentModelClass, description_plural)
    fk_checks = [
        # Direct children of Sketch
        (Timeline, "sketch_id", Sketch, "Timelines (sketch link)"),
        (View, "sketch_id", Sketch, "Views (sketch link)"),
        (Event, "sketch_id", Sketch, "Events (DB metadata, sketch link)"),
        (Story, "sketch_id", Sketch, "Stories (sketch link)"),
        (Aggregation, "sketch_id", Sketch, "Aggregations (sketch link)"),
        (Attribute, "sketch_id", Sketch, "Attributes (sketch link)"),
        (Graph, "sketch_id", Sketch, "Graphs (sketch link)"),
        (GraphCache, "sketch_id", Sketch, "GraphCaches (sketch link)"),
        (AggregationGroup, "sketch_id", Sketch, "AggregationGroups (sketch link)"),
        (Analysis, "sketch_id", Sketch, "Analyses (sketch link)"),
        (AnalysisSession, "sketch_id", Sketch, "AnalysisSessions (sketch link)"),
        (SearchHistory, "sketch_id", Sketch, "SearchHistories (sketch link)"),
        (Scenario, "sketch_id", Sketch, "Scenarios (sketch link)"),
        (Facet, "sketch_id", Sketch, "Facets (sketch link)"),
        (
            InvestigativeQuestion,
            "sketch_id",
            Sketch,
            "InvestigativeQuestions (sketch link)",
        ),
        # Grandchildren and other relations
        (DataSource, "timeline_id", Timeline, "DataSources (timeline link)"),
        (Analysis, "timeline_id", Timeline, "Analyses (timeline link)"),
        (Analysis, "analysissession_id", AnalysisSession, "Analyses (session link)"),
        (
            Analysis,
            "approach_id",
            InvestigativeQuestionApproach,
            "Analyses (approach link)",
        ),
        (
            Analysis,
            "question_conclusion_id",
            InvestigativeQuestionConclusion,
            "Analyses (question conclusion link)",
        ),
        (AttributeValue, "attribute_id", Attribute, "AttributeValues (attribute link)"),
        (Aggregation, "view_id", View, "Aggregations (view link)"),
        (
            Aggregation,
            "aggregationgroup_id",
            AggregationGroup,
            "Aggregations (group link)",
        ),
        (AggregationGroup, "view_id", View, "AggregationGroups (view link)"),
        (FacetTimeFrame, "facet_id", Facet, "FacetTimeFrames (facet link)"),
        (FacetConclusion, "facet_id", Facet, "FacetConclusions (facet link)"),
        (
            InvestigativeQuestionApproach,
            "investigativequestion_id",
            InvestigativeQuestion,
            "InvestigativeQuestionApproaches (question link)",
        ),
        (
            InvestigativeQuestionConclusion,
            "investigativequestion_id",
            InvestigativeQuestion,
            "InvestigativeQuestionConclusions (question link)",
        ),
        (
            SearchHistory,
            "parent_id",
            SearchHistory,
            "SearchHistories (parent/child link)",
        ),
        (SearchHistory, "scenario_id", Scenario, "SearchHistories (scenario link)"),
        (SearchHistory, "facet_id", Facet, "SearchHistories (facet link)"),
        (
            SearchHistory,
            "question_id",
            InvestigativeQuestion,
            "SearchHistories (question link)",
        ),
        (
            SearchHistory,
            "approach_id",
            InvestigativeQuestionApproach,
            "SearchHistories (approach link)",
        ),
        (Facet, "scenario_id", Scenario, "Facets (scenario link)"),
        (
            InvestigativeQuestion,
            "scenario_id",
            Scenario,
            "InvestigativeQuestions (scenario link)",
        ),
        (
            InvestigativeQuestion,
            "facet_id",
            Facet,
            "InvestigativeQuestions (facet link)",
        ),
    ]

    for Model, fk_attr, ParentModel, desc in fk_checks:
        _check_fk_orphans(Model, fk_attr, ParentModel, desc, verbose_checks)

    # Mixin checks
    mixin_parent_models = [
        (Sketch, "Sketch"),
        (Timeline, "Timeline"),
        (View, "View"),
        (Event, "Event (DB metadata)"),
        (Story, "Story"),
        (Aggregation, "Aggregation"),
        (AggregationGroup, "AggregationGroup"),
        (Analysis, "Analysis"),
        (Scenario, "Scenario"),
        (Facet, "Facet"),
        (InvestigativeQuestion, "InvestigativeQuestion"),
        (InvestigativeQuestionApproach, "InvestigativeQuestionApproach"),
        (InvestigativeQuestionConclusion, "InvestigativeQuestionConclusion"),
        (FacetConclusion, "FacetConclusion"),
        (SearchIndex, "SearchIndex"),
        (SearchTemplate, "SearchTemplate"),
        (SigmaRule, "SigmaRule"),
        (Group, "Group"),
    ]

    mixin_types_info = [
        ("Label", "Labels"),
        ("Comment", "Comments"),
        ("Status", "Statuses"),
        ("GenericAttribute", "GenericAttributes"),
        ("AccessControlEntry", "AccessControlEntries (ACLs)"),
    ]

    if verbose_checks:
        print("\nChecking for orphaned Mixin-based Annotation records...")

    for ParentModel, parent_model_name_desc in mixin_parent_models:
        for mixin_class_name_suffix, mixin_desc_plural in mixin_types_info:
            try:
                AnnotationModel = getattr(ParentModel, mixin_class_name_suffix, None)
                if AnnotationModel:  # If the mixin is used and class is available
                    _check_fk_orphans(
                        AnnotationModel,
                        "parent_id",
                        ParentModel,
                        f"{mixin_desc_plural} for {parent_model_name_desc}",
                        verbose_checks,
                    )
            except AttributeError:  # ParentModel might not use this mixin.
                pass  # ParentModel might not use this mixin or it's not initialized.
            except Exception as e:  # pylint: disable=broad-except
                print(
                    f"  ERROR trying to check {mixin_desc_plural} for "
                    f"{parent_model_name_desc}: {e}"
                )
                found_orphans_overall = True

    if not found_orphans_overall:
        if verbose_checks:
            print("\nNo orphaned data found based on current checks.")
        else:
            print(
                "No orphaned data found."
            )  # Minimal output if no orphans and not verbose
    else:
        print("\nOrphaned data check complete. Issues found as listed above.")


@cli.command(name="find-inconsistent-archives")
def find_inconsistent_archives():
    """Finds sketches that are in an inconsistent archival state.

    An inconsistent state is defined as a sketch that has been marked as
    'archived', but still contains one or more timelines that are not also
    archived (e.g., they are 'ready', 'failed' or 'processing'). This can
    happen if the archival process was interrupted or failed.

    This command helps administrators identify these inconsistencies so they
    can be manually resolved, ensuring data integrity and proper data
    lifecycle management.

    To resolve an inconsistent archive, you typically need to:
    1. Unarchive the sketch.
    2. Remove the inconsistent timeline(s) from the sketch.
    3. Re-archive the sketch.
    These actions can be performed via the API or the UI.
    """
    print("Searching for inconsistently archived sketches...")
    inconsistent_sketches = []

    sketches = Sketch.query.all()
    for sketch in sketches:
        if sketch.get_status.status == "archived":
            unarchived_timelines = []
            for timeline in sketch.timelines:
                if timeline.get_status.status != "archived":
                    unarchived_timelines.append(timeline)

            if unarchived_timelines:
                inconsistent_sketches.append((sketch, unarchived_timelines))

    if not inconsistent_sketches:
        print("No inconsistent sketches found.")
        return

    print(f"\nFound {len(inconsistent_sketches)} inconsistently archived sketch(es):")
    for sketch, timelines in inconsistent_sketches:
        print("-" * 40)
        print(f"Sketch: '{sketch.name}' (ID: {sketch.id})")
        print("  Unarchived Timelines:")
        for timeline in timelines:
            print(
                f"    - Timeline: '{timeline.name}' (ID: {timeline.id}), "
                f"Status: {timeline.get_status.status}"
            )
            if timeline.get_status.status == "fail":
                for datasource in timeline.datasources:
                    error_msg = datasource.error_message or "No error message recorded."
                    print(f"      - Reason: {error_msg}")

        print("\n  Recommendation:")
        print("    To resolve this, you need to:")
        print("    1. Unarchive the sketch.")
        print("    2. Remove the inconsistent timeline(s) from the sketch.")
        print("    3. Re-archive the sketch.")
        print("    These actions can be performed via the API or the UI.")
        print(
            "    - To get more details for a timeline, run: "
            "tsctl timeline-status <TIMELINE_ID>"
        )

    print("-" * 40)


@cli.command(name="export-db")
@click.argument(
    "filepath", type=click.Path(dir_okay=False, writable=True), required=True
)
def export_db(filepath):
    """Export the database to a zip file."""
    click.echo(f"Exporting database to {filepath}...")
    engine = db_session.get_bind()
    with engine.connect() as connection:
        with zipfile.ZipFile(filepath, "w", zipfile.ZIP_DEFLATED) as zipf:
            for table in BaseModel.metadata.sorted_tables:
                table_name = table.name
                try:
                    result = connection.execute(table.select())
                    df = pd.DataFrame(result.fetchall(), columns=result.keys())
                    row_count = df.shape[0]
                    click.echo(f"  Exporting table: {table_name} ({row_count} rows)")
                    json_data = df.to_json(orient="records", date_format="iso")
                    zipf.writestr(f"{table_name}.json", json_data)
                except Exception as e:
                    click.echo(f"Error exporting table {table_name}: {e!s}", err=True)
                    click.echo("Database export failed.", err=True)
                    raise click.Abort()
    click.echo("Database export complete.")


@cli.command(name="import-db")
@click.argument("filepath", type=click.Path(exists=True, dir_okay=False))
@click.option("--yes", is_flag=True, help="Skip confirmation.")
def import_db(filepath, yes):
    """Import the database from a zip file. This will delete existing data."""
    if not yes:
        click.confirm(
            "This will drop the current database and import data from the "
            "file. This is a destructive action. Are you sure?",
            abort=True,
        )

    click.echo("Dropping all tables...")
    drop_all()

    click.echo("Creating new tables...")
    init_db()

    # Create a mapping from table names to model classes for bulk insertion.
    model_class_registry = {
        cls.__tablename__: cls
        for cls in BaseModel.__subclasses__()
        if hasattr(cls, "__tablename__")
    }

    engine = db_session.get_bind()
    dialect = engine.dialect.name

    try:
        # For certain database backends, we need to disable foreign key checks
        # to allow for out-of-order table imports.
        if dialect == "sqlite":
            db_session.execute(sqlalchemy.text("PRAGMA foreign_keys=OFF"))
        elif dialect == "postgresql":
            db_session.execute(
                sqlalchemy.text("SET session_replication_role = 'replica'")
            )

        with zipfile.ZipFile(filepath, "r") as zipf:
            sorted_tables = BaseModel.metadata.sorted_tables
            for table in sorted_tables:
                table_name = table.name
                json_filename = f"{table_name}.json"

                if json_filename not in zipf.namelist():
                    msg = (
                        f"  File not found in archive for table: {table_name}, "
                        "skipping."
                    )
                    click.echo(msg)
                    continue
                with zipf.open(json_filename) as json_file:
                    data = json_file.read()
                    if not data:
                        click.echo(f"    Skipping empty file: {json_filename}")
                        continue

                    records = json.loads(data)
                    row_count = len(records)
                    click.echo(f"  Importing table: {table_name} ({row_count} rows)")

                    if not records:
                        continue

                    # Coerce types for bulk insert
                    for record in records:
                        for column in table.columns:
                            value = record.get(column.name)
                            if value is None:
                                continue
                            # Handle datetimes
                            if isinstance(column.type, sqlalchemy.DateTime):
                                if isinstance(value, str):
                                    try:
                                        record[column.name] = pd.to_datetime(value)
                                    except (ValueError, TypeError):
                                        click.echo(
                                            f"Warning: Could not parse datetime '{value}' for column '{column.name}' in table '{table_name}'. Setting to NULL.",  # pylint: disable=line-too-long
                                            err=True,
                                        )
                                        record[column.name] = None

                    mapped_class = model_class_registry.get(table_name)
                    if mapped_class:
                        db_session.bulk_insert_mappings(mapped_class, records)
                    elif records:
                        db_session.execute(table.insert(), records)

        if dialect == "postgresql":
            click.echo("Updating PostgreSQL sequences...")
            for table in sorted_tables:
                for column in table.primary_key.columns:
                    if column.autoincrement:
                        query_string = (
                            "SELECT pg_get_serial_sequence("
                            f"'\"{table.name}\"', '{column.name}')"
                        )
                        seq_name = db_session.execute(
                            sqlalchemy.text(query_string)
                        ).scalar()
                        if seq_name:
                            max_id_val = db_session.execute(
                                sqlalchemy.text(
                                    f'SELECT MAX("{column.name}") FROM "{table.name}"'
                                )
                            ).scalar()
                            max_id = max_id_val or 1
                            db_session.execute(
                                sqlalchemy.text(
                                    f"SELECT setval('{seq_name}', {max_id}, true);"
                                )
                            )
            click.echo("Sequences updated.")

        try:
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            click.echo(f"Error committing to database: {e!s}", err=True)
            raise click.Abort()
    except Exception as e:
        db_session.rollback()
        click.echo(f"An error occurred during import: {e}", err=True)
        raise click.Abort()
    finally:
        # reset the database settings
        if dialect == "sqlite":
            db_session.execute(sqlalchemy.text("PRAGMA foreign_keys=ON"))
        elif dialect == "postgresql":
            db_session.execute(
                sqlalchemy.text("SET session_replication_role = 'origin'")
            )
        click.echo("Database import finished.")
