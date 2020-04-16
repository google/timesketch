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
"""This module implements the user model."""

from __future__ import unicode_literals

import codecs

import six

from flask_bcrypt import generate_password_hash
from flask_bcrypt import check_password_hash
from flask_login import UserMixin
from sqlalchemy.types import Boolean
from sqlalchemy import Column
from sqlalchemy import PrimaryKeyConstraint
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Table
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship

from timesketch.models import BaseModel
from timesketch.models.annotations import LabelMixin
from timesketch.models.annotations import StatusMixin

# Helper table for Groups many-to-many relationship.
user_group = Table('user_group', BaseModel.metadata,
                   Column('user_id', Integer(), ForeignKey('user.id')),
                   Column('group_id', Integer(), ForeignKey('group.id')),
                   PrimaryKeyConstraint('user_id', 'group_id'))


class User(UserMixin, BaseModel):
    """Implements the User model."""

    username = Column(Unicode(255), unique=True)
    password = Column(Unicode(128))
    name = Column(Unicode(255))
    email = Column(Unicode(255))
    active = Column(Boolean(), default=True)
    sketches = relationship('Sketch', backref='user', lazy='dynamic')
    searchindices = relationship(
        'SearchIndex', backref='user', lazy='dynamic')
    timelines = relationship('Timeline', backref='user', lazy='dynamic')
    views = relationship('View', backref='user', lazy='dynamic')
    stories = relationship('Story', backref='user', lazy='dynamic')
    aggregations = relationship('Aggregation', backref='user', lazy='dynamic')
    aggregationgroups = relationship(
        'AggregationGroup', backref='user', lazy='dynamic')
    my_groups = relationship('Group', backref='user', lazy='dynamic')
    groups = relationship(
        'Group',
        secondary=user_group,
        backref=backref('users', lazy='dynamic'))

    def __init__(self, username, name=None):
        """Initialize the User object.

        Args:
            username: Username for the user
            name: Name of the user
        """
        super(User, self).__init__()
        self.username = username
        self.name = name
        if not name:
            self.name = username

    def set_password(self, plaintext, rounds=12):
        """Sets the password for the user. The password hash is created with the
        Bcrypt python library (http://www.mindrot.org/projects/py-bcrypt/).

        Args:
            plaintext: The plaintext password to hash
            rounds: Number of rounds to use for the bcrypt hashing
        """
        password_hash = generate_password_hash(plaintext, rounds)
        if isinstance(password_hash, six.binary_type):
            password_hash = codecs.decode(password_hash, 'utf-8')
        self.password = password_hash

    def check_password(self, plaintext):
        """Check a plaintext password against a stored password hash.

        Args:
            plaintext: A plaintext password

        Returns:
            A boolean value indicating if the plaintext password matches the
            stored password hash.
        """
        return check_password_hash(self.password, plaintext)


class Group(LabelMixin, StatusMixin, BaseModel):
    """Implements the Group model."""

    name = Column(Unicode(255), unique=True)
    display_name = Column(Unicode(255))
    description = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))

    def __init__(self, name, display_name=None, description=None, user=None):
        """Initialize the Group object.

        Args:
            name: Name of the group
            display_name: User friendly name of the group
            description: Description of the group
            user: Creator (instance of timesketch.models.user.User)
        """
        super(Group, self).__init__()
        self.name = name
        self.display_name = display_name or name
        self.description = description or name
        self.user = user
