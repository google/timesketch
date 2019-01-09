#!/usr/bin/python
# Copyright 2015 Google Inc. All rights reserved.
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
"""This module is for management of the Timesketch application."""
from __future__ import unicode_literals

import os
import pwd
import sys
import uuid
import yaml

from flask import current_app
from flask_migrate import MigrateCommand
from flask_script import Command
from flask_script import Manager
from flask_script import Server
from flask_script import Option
from flask_script import prompt_bool
from flask_script import prompt_pass
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import Forbidden

from timesketch import create_app
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.models import db_session
from timesketch.models import drop_all
from timesketch.models.user import Group
from timesketch.models.user import User
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline


class DropDataBaseTables(Command):
    """Drop all database tables."""

    def __init__(self):
        super(DropDataBaseTables, self).__init__()

    # pylint: disable=method-hidden
    def run(self):
        """Drop all tables after user ha verified."""
        verified = prompt_bool(
            u'Do you really want to drop all the database tables?')
        if verified:
            sys.stdout.write(u'All tables dropped. Database is now empty.\n')
            drop_all()


class AddUser(Command):
    """Create a new Timesketch user."""
    option_list = (
        Option(u'--username', u'-u', dest=u'username', required=True),
        Option(u'--password', u'-p', dest=u'password', required=False), )

    def __init__(self):
        super(AddUser, self).__init__()

    def get_password_from_prompt(self):
        """Get password from the command line prompt."""
        first_password = prompt_pass(u'Enter password')
        second_password = prompt_pass(u'Enter password again')
        if first_password != second_password:
            sys.stderr.write(u'Passwords don\'t match, try again.\n')
            self.get_password_from_prompt()
        return first_password

    # pylint: disable=arguments-differ, method-hidden
    def run(self, username, password):
        """Creates the user."""
        if not password:
            password = self.get_password_from_prompt()
        password = unicode(password.decode(encoding=u'utf-8'))
        username = unicode(username.decode(encoding=u'utf-8'))
        user = User.get_or_create(username=username)
        user.set_password(plaintext=password)
        db_session.add(user)
        db_session.commit()
        sys.stdout.write(u'User {0:s} created/updated\n'.format(username))


class AddGroup(Command):
    """Create a new Timesketch group."""
    option_list = (Option(u'--name', u'-n', dest=u'name', required=True), )

    def __init__(self):
        super(AddGroup, self).__init__()

    # pylint: disable=arguments-differ, method-hidden
    def run(self, name):
        """Creates the group."""
        name = unicode(name.decode(encoding=u'utf-8'))
        group = Group.get_or_create(name=name)
        db_session.add(group)
        db_session.commit()
        sys.stdout.write(u'Group {0:s} created\n'.format(name))


class GroupManager(Command):
    """Manage group memberships."""
    option_list = (
        Option(
            u'--remove',
            u'-r',
            dest=u'remove',
            action=u'store_true',
            required=False,
            default=False),
        Option(u'--group', u'-g', dest=u'group_name', required=True),
        Option(u'--user', u'-u', dest=u'user_name', required=True), )

    def __init__(self):
        super(GroupManager, self).__init__()

    # pylint: disable=arguments-differ, method-hidden
    def run(self, remove, group_name, user_name):
        """Add the user to the group."""
        group_name = unicode(group_name.decode(encoding=u'utf-8'))
        user_name = unicode(user_name.decode(encoding=u'utf-8'))
        group = Group.query.filter_by(name=group_name).first()
        user = User.query.filter_by(username=user_name).first()

        # Add or remove user from group
        if remove:
            try:
                user.groups.remove(group)
                sys.stdout.write(u'{0:s} removed from group {1:s}\n'.format(
                    user_name, group_name))
                db_session.commit()
            except ValueError:
                sys.stdout.write(u'{0:s} is not a member of group {1:s}\n'.
                                 format(user_name, group_name))
        else:
            user.groups.append(group)
            try:
                db_session.commit()
                sys.stdout.write(u'{0:s} added to group {1:s}\n'.format(
                    user_name, group_name))
            except IntegrityError:
                sys.stdout.write(u'{0:s} is already a member of group {1:s}\n'.
                                 format(user_name, group_name))


class AddSearchIndex(Command):
    """Create a new Timesketch searchindex."""
    option_list = (
        Option(u'--name', u'-n', dest=u'name', required=True),
        Option(u'--index', u'-i', dest=u'index', required=True),
        Option(u'--user', u'-u', dest=u'username', required=True), )

    def __init__(self):
        super(AddSearchIndex, self).__init__()

    # pylint: disable=arguments-differ, method-hidden
    def run(self, name, index, username):
        """Create the SearchIndex."""
        es = ElasticsearchDataStore(
            host=current_app.config[u'ELASTIC_HOST'],
            port=current_app.config[u'ELASTIC_PORT'])
        user = User.query.filter_by(username=username).first()
        if not user:
            sys.stderr.write(u'User does not exist\n')
            sys.exit(1)
        if not es.client.indices.exists(index=index):
            sys.stderr.write(u'Index does not exist in the datastore\n')
            sys.exit(1)
        if SearchIndex.query.filter_by(name=name, index_name=index).first():
            sys.stderr.write(
                u'Index with this name already exist in Timesketch\n')
            sys.exit(1)
        searchindex = SearchIndex(
            name=name, description=name, user=user, index_name=index)
        searchindex.grant_permission(u'read')
        db_session.add(searchindex)
        db_session.commit()
        sys.stdout.write(u'Search index {0:s} created\n'.format(name))


class PurgeTimeline(Command):
    """Delete timeline permanently from Timesketch and Elasticsearch."""
    option_list = (Option(
        u'--index', u'-i', dest=u'index_name', required=True), )

    def __init__(self):
        super(PurgeTimeline, self).__init__()

    # pylint: disable=arguments-differ, method-hidden
    def run(self, index_name):
        """Delete timeline in both Timesketch and Elasticsearch.

        Args:
            index_name: The name of the index in Elasticsearch
        """
        index_name = unicode(index_name.decode(encoding=u'utf-8'))
        searchindex = SearchIndex.query.filter_by(
            index_name=index_name).first()

        if not searchindex:
            sys.stdout.write(u'No such index\n')
            sys.exit()

        es = ElasticsearchDataStore(
            host=current_app.config[u'ELASTIC_HOST'],
            port=current_app.config[u'ELASTIC_PORT'])

        timelines = Timeline.query.filter_by(searchindex=searchindex).all()
        sketches = [
            t.sketch for t in timelines
            if t.sketch and t.sketch.get_status.status != u'deleted'
        ]
        if sketches:
            sys.stdout.write(u'WARNING: This timeline is in use by:\n')
            for sketch in sketches:
                sys.stdout.write(u' * {0:s}\n'.format(sketch.name))
                sys.stdout.flush()
        really_delete = prompt_bool(
            u'Are you sure you want to delete this timeline?')
        if really_delete:
            for timeline in timelines:
                db_session.delete(timeline)
            db_session.delete(searchindex)
            db_session.commit()
            es.client.indices.delete(index=index_name)


class SearchTemplateManager(Command):
    """Command Module to manipulate Search templates."""
    option_list = (
        Option(u'--import', u'-i', dest=u'import_location', required=False),
        Option(u'--export', u'-e', dest=u'export_location', required=False),
    )

    # pylint: disable=arguments-differ, method-hidden
    def run(self, import_location, export_location):
        """Export/Import search templates to/from file.

        Args:
            import_location: Path to the yaml file to import templates.
            export_location: Path to the yaml file to export templates.
        """

        if export_location:
            search_templates = []
            for search_template in SearchTemplate.query.all():
                labels = []
                for label in search_template.labels:
                    if label.label.startswith(u'supported_os:'):
                        labels.append(label.label.replace(
                            u'supported_os:', u''))
                search_templates.append({
                    u'name': search_template.name,
                    u'query_string': search_template.query_string,
                    u'query_dsl': search_template.query_dsl,
                    u'supported_os': labels
                })

            with open(export_location, 'w') as fh:
                yaml.safe_dump(search_templates, stream=fh)

        if import_location:
            try:
                with open(import_location, 'rb') as fh:
                    search_templates = yaml.safe_load(fh)
            except IOError as e:
                sys.stdout.write(u'Unable to open file: {0:s}\n'.format(e))
                sys.exit(1)

            for search_template in search_templates:
                name = search_template[u'name']
                query_string = search_template[u'query_string'],
                query_dsl = search_template[u'query_dsl']

                # Skip search template if already exits.
                if SearchTemplate.query.filter_by(name=name).first():
                    continue

                imported_template = SearchTemplate(
                    name=name,
                    user=User(None),
                    query_string=query_string,
                    query_dsl=query_dsl)

                # Add supported_os labels.
                for supported_os in search_template[u'supported_os']:
                    label_name = u'supported_os:{0:s}'.format(supported_os)
                    label = SearchTemplate.Label.get_or_create(
                        label=label_name, user=None)
                    imported_template.labels.append(label)

                # Set flag to identify local vs import templates.
                remote_flag = SearchTemplate.Label.get_or_create(
                    label=u'remote_template', user=None)
                imported_template.labels.append(remote_flag)

                db_session.add(imported_template)
                db_session.commit()


class ImportTimeline(Command):
    """Create a new Timesketch timeline from a file."""
    option_list = (
        Option('--file', '-f', dest='file_path', required=True),
        Option('--sketch_id', '-s', dest='sketch_id', required=False),
        Option('--username', '-u', dest='username', required=False),
        Option('--timeline_name', '-n', dest='timeline_name',
               required=False),
    )

    def __init__(self):
        super(ImportTimeline, self).__init__()

    # pylint: disable=arguments-differ, method-hidden
    def run(self, file_path, sketch_id, username, timeline_name):
        """This is the run method."""

        file_path = os.path.realpath(file_path)
        file_path_no_extension, extension = os.path.splitext(file_path)
        extension = extension.lstrip('.')
        filename = os.path.basename(file_path_no_extension)

        supported_extensions = ('plaso', 'csv', 'jsonl')

        if not os.path.isfile(file_path):
            sys.exit('No such file: {0:s}'.format(file_path))

        if extension not in supported_extensions:
            sys.exit(
                'Extension {0:s} is not supported. '
                '(supported extensions are: {1:s})'.format(
                    extension, ', '.join(supported_extensions)))

        user = None
        if not username:
            username = pwd.getpwuid(os.stat(file_path).st_uid).pw_name
        if username is not 'root':
            user = User.query.filter_by(username=unicode(username)).first()
        if not user:
            sys.exit('Cannot determine user for file: {0:s}'.format(file_path))

        sketch = None
        # If filename starts with <number> then use that as sketch_id.
        # E.g: 42_file_name.plaso means sketch_id is 42.
        sketch_id_from_filename = filename.split('_')[0]
        if not sketch_id and sketch_id_from_filename.isdigit():
            sketch_id = sketch_id_from_filename

        if sketch_id:
            try:
                sketch = Sketch.query.get_with_acl(sketch_id, user=user)
            except Forbidden:
                pass

        if not timeline_name:
            timeline_name = unicode(filename.replace('_', ' '))
            # Remove sketch ID if present in the filename.
            timeline_parts = timeline_name.split()
            if timeline_parts[0].isdigit():
                timeline_name = ' '.join(timeline_name.split()[1:])

        if not sketch:
            # Create a new sketch.
            sketch_name = 'Sketch for: {0:s}'.format(timeline_name)
            sketch = Sketch(
                name=sketch_name, description=sketch_name, user=user)
            # Need to commit here to be able to set permissions later.
            db_session.add(sketch)
            db_session.commit()
            sketch.grant_permission(permission='read', user=user)
            sketch.grant_permission(permission='write', user=user)
            sketch.grant_permission(permission='delete', user=user)
            sketch.status.append(sketch.Status(user=None, status=u'new'))
            db_session.add(sketch)
            db_session.commit()

        index_name = unicode(uuid.uuid4().hex)
        searchindex = SearchIndex.get_or_create(
            name=timeline_name,
            description=timeline_name,
            user=user,
            index_name=index_name)

        searchindex.grant_permission(permission='read', user=user)
        searchindex.grant_permission(permission='write', user=user)
        searchindex.grant_permission(permission='delete', user=user)

        searchindex.set_status('processing')
        db_session.add(searchindex)
        db_session.commit()

        if sketch and sketch.has_permission(user, 'write'):
            timeline = Timeline(
                name=searchindex.name,
                description=searchindex.description,
                sketch=sketch,
                user=user,
                searchindex=searchindex)
            timeline.set_status('processing')
            sketch.timelines.append(timeline)
            db_session.add(timeline)
            db_session.commit()

        # Start Celery pipeline for indexing and analysis.
        # Import here to avoid circular imports.
        from timesketch.lib import tasks
        pipeline = tasks.build_index_pipeline(
            file_path, timeline_name, index_name, extension, sketch.id)
        pipeline.apply_async(task_id=index_name)

        print('Imported {0:s} to sketch: {1:d} ({2:s})'.format(
            file_path, sketch.id, sketch.name))


def main():
    # Setup Flask-script command manager and register commands.
    shell_manager = Manager(create_app)
    shell_manager.add_command('add_user', AddUser())
    shell_manager.add_command('add_group', AddGroup())
    shell_manager.add_command('manage_group', GroupManager())
    shell_manager.add_command('add_index', AddSearchIndex())
    shell_manager.add_command('db', MigrateCommand)
    shell_manager.add_command('drop_db', DropDataBaseTables())
    shell_manager.add_command('purge', PurgeTimeline())
    shell_manager.add_command('search_template', SearchTemplateManager())
    shell_manager.add_command('import', ImportTimeline())
    shell_manager.add_command('runserver',
                              Server(host='127.0.0.1', port=5000))
    shell_manager.add_option(
        '-c',
        '--config',
        dest='config',
        default='/etc/timesketch.conf',
        required=False)
    shell_manager.run()


if __name__ == '__main__':
    main()
