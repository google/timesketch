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
import subprocess
import yaml


import click
import pandas as pd

from flask.cli import FlaskGroup
from sqlalchemy.exc import IntegrityError
from jsonschema import validate, ValidationError, SchemaError

from timesketch import version
from timesketch.app import create_app
from timesketch.lib import sigma_util
from timesketch.models import db_session
from timesketch.models import drop_all
from timesketch.models.user import Group
from timesketch.models.user import User
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Analysis
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sigma import SigmaRule
from timesketch.models.sketch import Timeline
from timesketch.models.sketch import SearchIndex


@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """Management script for the Timesketch application."""


@cli.command(name="list-users")
def list_users():
    """List all users."""
    for user in User.query.all():
        if user.admin:
            extra = " (admin)"
        else:
            extra = ""
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
@click.option("--sketch_id", required=True)
def grant_user(username, sketch_id):
    """Grant access to a sketch."""
    sketch = Sketch.query.filter_by(id=sketch_id).first()
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
def list_groups():
    """List all groups."""
    for group in Group.query.all():
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
        with open(file_path, "r") as fh:
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

        with open(file_path, "r") as fh:
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
                    relevant_data.append(rule.__getattribute__(column))
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
        error_msg = "No rule found with rule_uuid.{0!s}".format(rule_uuid)
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
            "The directory needs to exist, please create: " "{0:s} first".format(path)
        )

    all_sigma_rules = SigmaRule.query.all()

    n = 0

    for rule in all_sigma_rules:
        file_path = os.path.join(path, f"{rule.title}.yml")
        if os.path.isfile(file_path):
            print("File [{0:s}] already exists.".format(file_path))
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
@click.argument("sketch_id")
def sketch_info(sketch_id):
    """Give information about a sketch."""
    sketch = Sketch.query.filter_by(id=sketch_id).first()
    if not sketch:
        print("Sketch does not exist.")
    else:
        print(f"Sketch {sketch_id} Name: ({sketch.name})")

        # define the table data
        table_data = [
            [
                "searchindex_id",
                "index_name",
                "created_at",
                "user_id",
                "description",
            ],
        ]

        for t in sketch.active_timelines:
            table_data.append(
                [
                    t.searchindex_id,
                    t.searchindex.index_name,
                    t.created_at,
                    t.user_id,
                    t.description,
                ]
            )

        print_table(table_data)

        print("Shared with:")
        print("\tUsers: (user_id, username)")
        for user in sketch.collaborators:
            print(f"\t\t{user.id}: {user.username}")
        print("\tGroups:")
        for group in sketch.groups:
            print(f"\t\t{group.display_name}")
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
        for status in sketch.status:
            status_table.append(
                [status.id, status.status, status.created_at, status.user_id]
            )
        print("Status:")
        print_table(status_table)


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

    with open(path, "r") as fh:
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
    required=True,
    help="Searchindex ID to search for e.g. 4c5afdf60c6e49499801368b7f238353.",
)
def searchindex_info(searchindex_id):
    """Search for a searchindex and print information about it.
    Especially which sketch the searchindex belongs to.

    Args:
        searchindex_id: to search for e.g. 4c5afdf60c6e49499801368b7f238353.
    """

    index_to_search = SearchIndex.query.filter_by(index_name=searchindex_id).first()

    if not index_to_search:
        print(f"Searchindex: {searchindex_id} not found in database.")
        return

    print(
        f"Searchindex: {searchindex_id} Name: {index_to_search.name} found in database."
    )
    timeline = Timeline.query.filter_by(id=index_to_search.id).first()
    print(
        f"Corresponding Timeline id: {timeline.id} in Sketch Id: {timeline.sketch_id}"
    )
    sketch = Sketch.query.filter_by(id=timeline.sketch_id).first()
    print(f"Corresponding Sketch id: {sketch.id} Sketch name: {sketch.name}")


# Analyzer stats cli command
@cli.command(name="analyzer-stats")
@click.argument(
    "analyzer_name",
    required=False,
    default="all",
)
@click.option(
    "--timeline_id",
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
