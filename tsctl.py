#!/usr/bin/env python
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
"""This module is for management of the timesketch application."""

import sys

from flask import current_app
from flask_script import Command
from flask_script import Manager
from flask_script import Option
from flask_script import prompt_bool
from flask_script import prompt_pass
from sqlalchemy.exc import IntegrityError

from timesketch import create_app
from timesketch.lib.datastores.elastic import ElasticSearchDataStore
from timesketch.models import db_session
from timesketch.models import drop_all
from timesketch.models.user import User
from timesketch.models.sketch import SearchIndex


class DropDataBaseTables(Command):
    """Drop all database tables."""
    def __init__(self):
        super(DropDataBaseTables, self).__init__()

    # pylint: disable=method-hidden
    def run(self):
        """Drop all tables after user ha verified."""
        verified = prompt_bool(
            'Do you really want to drop all the database tables?')
        if verified:
            sys.stdout.write('All tables dropped. Database is now empty.\n')
            drop_all()


class AddUser(Command):
    """Create a new Timesketch user."""
    option_list = (
        Option('--username', '-u', dest='username', required=True),
        Option('--password', '-p', dest='password', required=False),
    )

    def __init__(self):
        super(AddUser, self).__init__()

    def get_password_from_prompt(self):
        """Get password from the command line prompt."""
        first_password = prompt_pass('Enter password')
        second_password = prompt_pass('Enter password again')
        if first_password != second_password:
            sys.stderr.write('Passwords don\'t match, try again.\n')
            self.get_password_from_prompt()
        return first_password

    # pylint: disable=arguments-differ, method-hidden
    def run(self, username, password):
        """Creates the user."""
        if not password:
            password = self.get_password_from_prompt()
        user = User(username=username, name=username)
        user.set_password(plaintext=password)
        try:
            db_session.add(user)
            db_session.commit()
            sys.stdout.write('User {0:s} created\n'.format(username))
        except IntegrityError:
            sys.stderr.write(
                'The username ({0:s}) is already taken, '
                'try another one.\n'.format(username))


class AddSearchIndex(Command):
    """Create a new Timesketch searchindex."""
    option_list = (
        Option('--name', '-n', dest='name', required=True),
        Option('--index', '-i', dest='index', required=True),
        Option('--user', '-u', dest='username', required=True),
    )

    def __init__(self):
        super(AddSearchIndex, self).__init__()

    # pylint: disable=arguments-differ, method-hidden
    def run(self, name, index, username):
        """Create the SearchIndex."""
        es = ElasticSearchDataStore(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])
        user = User.query.filter_by(username=username).first()
        if not user:
            sys.stderr.write('User does not exist\n')
            sys.exit(1)
        if not es.client.indices.exists(index=index):
            sys.stderr.write('Index does not exist in the datastore\n')
            sys.exit(1)
        if SearchIndex.query.filter_by(name=name, index_name=index).first():
            sys.stderr.write(
                'Index with this name already exist in Timesketch\n')
            sys.exit(1)
        searchindex = SearchIndex(
            name=name, description=name, user=user, index_name=index)
        searchindex.grant_permission(None, 'read')
        db_session.add(searchindex)
        db_session.commit()
        sys.stdout.write('Search index {0:s} created\n'.format(name))


if __name__ == '__main__':
    # Setup Flask-script command manager and register commands.
    shell_manager = Manager(create_app)
    shell_manager.add_command('add_user', AddUser())
    shell_manager.add_command('add_index', AddSearchIndex())
    shell_manager.add_command('drop_db', DropDataBaseTables())
    shell_manager.add_option(
        '-c', '--config', dest='config', default='/etc/timesketch.conf',
        required=False)
    shell_manager.run()
