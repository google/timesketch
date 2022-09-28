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
from re import search
import yaml
import json

import click
from flask.cli import FlaskGroup
from sqlalchemy.exc import IntegrityError

from timesketch import version
from timesketch.app import create_app
from timesketch.models import db_session
from timesketch.models import drop_all
from timesketch.models.user import Group
from timesketch.models.user import User
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import SearchTemplate


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
    user = User.get_or_create(username=username)
    user.set_password(plaintext=password)
    db_session.add(user)
    db_session.commit()
    print(f"User {username, password} created/updated")


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
            print("All tables dropped. Database is now empty.")
            drop_all()


@cli.command(name="list-sketches")
def list_sketches():
    """List all sketches."""
    sketches = Sketch.query.all()
    for sketch in sketches:
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
    group = Group.get_or_create(name=group_name)
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
        search_template_dict = None
        with open(file_path, "r") as fh:
            search_template_dict = yaml.safe_load(fh.read())

        if search_template_dict:
            print(f"Importing: {search_template_dict.get('short_name')}")
            name = search_template_dict.get("display_name")
            short_name = search_template_dict.get("short_name")
            description = search_template_dict.get("description")
            uuid = search_template_dict.get("id")
            query_string = search_template_dict.get("query_string")
            query_filter = search_template_dict.get("query_filter", {})
            query_dsl = search_template_dict.get("query_dsl", {})
            tags = search_template_dict.get("tags", [])

            searchtemplate = SearchTemplate.query.filter_by(template_uuid=uuid).first()
            if not searchtemplate:
                searchtemplate = SearchTemplate(name=name, template_uuid=uuid)
                db_session.add(searchtemplate)
                db_session.commit()

            searchtemplate.short_name = short_name
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
