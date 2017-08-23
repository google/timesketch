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
"""
This module implements annotations that can be use on other database models.
"""

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from timesketch.models import BaseModel
from timesketch.models import db_session


class BaseAnnotation(object):
    """Base class with common attributes."""

    @declared_attr
    def user_id(self):
        """Foreign key to a user model.

        Returns:
            A column (instance of sqlalchemy.Column)
        """
        return Column(Integer, ForeignKey(u'user.id'))

    @declared_attr
    def user(self):
        """A relationship to a user object.

        Returns:
            A relationship (instance of sqlalchemy.orm.relationship)
        """
        return relationship(u'User')


class Label(BaseAnnotation):
    """A label annotation."""
    label = Column(Unicode(255))

    def __init__(self, user, label):
        """Initialize the model.

        Args:
            user: A user (instance of timesketch.models.user.User)
            name: Name of the label
        """
        super(Label, self).__init__()
        self.user = user
        self.label = label


class Comment(BaseAnnotation):
    """A comment annotation."""
    comment = Column(UnicodeText())

    def __init__(self, user, comment):
        """Initialize the model.

        Args:
            user: A user (instance of timesketch.models.user.User)
            body: The body if the comment
        """
        super(Comment, self).__init__()
        self.user = user
        self.comment = comment


class Status(BaseAnnotation):
    """A status annotation."""
    status = Column(Unicode(255))

    def __init__(self, user, status):
        """Initialize the model.

        Args:
            user: A user (instance of timesketch.models.user.User)
            status: The type of status (string, e.g. open)
        """
        super(Status, self).__init__()
        self.user = user
        self.status = status


class LabelMixin(object):
    """
    A MixIn for generating the necessary tables in the database and to make
    it accessible from the parent model object (the model object that uses this
    MixIn, i.e. the object that the label is added to).
    """

    @declared_attr
    def labels(self):
        """
        Generates the label tables and adds the attribute to the parent model
        object.

        Returns:
            A relationship to an label (timesketch.models.annotation.Label)
        """
        self.Label = type(
            '{0:s}Label'.format(self.__name__), (
                Label,
                BaseModel, ),
            dict(
                __tablename__='{0:s}_label'.format(self.__tablename__),
                parent_id=Column(
                    Integer,
                    ForeignKey('{0:s}.id'.format(self.__tablename__))),
                parent=relationship(self)))
        return relationship(self.Label)


class CommentMixin(object):
    """
    A MixIn for generating the necessary tables in the database and to make
    it accessible from the parent model object (the model object that uses this
    MixIn, i.e. the object that the comment is added to).
    """

    @declared_attr
    def comments(self):
        """
        Generates the comment tables and adds the attribute to the parent model
        object.

        Returns:
            A relationship to a comment (timesketch.models.annotation.Comment)
        """
        self.Comment = type(
            '{0:s}Comment'.format(self.__name__), (
                Comment,
                BaseModel, ),
            dict(
                __tablename__='{0:s}_comment'.format(self.__tablename__),
                parent_id=Column(
                    Integer,
                    ForeignKey('{0:s}.id'.format(self.__tablename__))),
                parent=relationship(self), ))
        return relationship(self.Comment)


class StatusMixin(object):
    """
    A MixIn for generating the necessary tables in the database and to make
    it accessible from the parent model object (the model object that uses this
    MixIn, i.e. the object that the status is added to).
    """

    @declared_attr
    def status(self):
        """
        Generates the status tables and adds the attribute to the parent model
        object.

        Returns:
            A relationship to a status (timesketch.models.annotation.Status)
        """
        self.Status = type(
            '{0:s}Status'.format(self.__name__), (
                Status,
                BaseModel, ),
            dict(
                __tablename__='{0:s}_status'.format(self.__tablename__),
                parent_id=Column(
                    Integer,
                    ForeignKey('{0:s}.id'.format(self.__tablename__))),
                parent=relationship(self), ))
        return relationship(self.Status)

    def set_status(self, status):
        """
        Set status on object. Although this is a many-to-many relationship
        this makes sure that the parent object only has one status set.

        Args:
            status: Name of the status
        """
        for _status in self.status:
            self.status.remove(_status)
        self.status.append(self.Status(user=None, status=status))
        db_session.commit()

    @property
    def get_status(self):
        """Get the current status.

        Returns:
            The status as a string
        """
        if not self.status:
            self.status.append(self.Status(user=None, status=u'new'))
        return self.status[0]
