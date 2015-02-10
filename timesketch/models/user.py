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

from flask_bcrypt import generate_password_hash
from flask_bcrypt import check_password_hash
from flask_login import UserMixin
from sqlalchemy import Column
from sqlalchemy import String
from sqlalchemy.orm import relationship

from timesketch.models import BaseModel


class User(UserMixin, BaseModel):
    """Implements the User model."""

    username = Column(String(255), unique=True)
    password = Column(String(128))
    name = Column(String(255))
    email = Column(String(255))
    sketches = relationship('Sketch', backref='user', lazy='dynamic')
    searchindices = relationship('SearchIndex', backref='user', lazy='dynamic')
    timelines = relationship('Timeline', backref='user', lazy='dynamic')
    views = relationship('View', backref='user', lazy='dynamic')

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
        self.password = generate_password_hash(plaintext, rounds)

    def check_password(self, plaintext):
        """Check a plaintext password against a stored password hash.

        Args:
            plaintext: A plaintext password

        Returns:
            A boolean value indicating if the plaintext password matches the
            stored password hash.
        """
        return check_password_hash(self.password, plaintext)
