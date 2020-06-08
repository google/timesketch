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

from __future__ import unicode_literals

import json
import six

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
        return Column(Integer, ForeignKey('user.id'))

    @declared_attr
    def user(self):
        """A relationship to a user object.

        Returns:
            A relationship (instance of sqlalchemy.orm.relationship)
        """
        return relationship('User')


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
        if six.PY2:
            class_name = b'{0:s}Label'.format(self.__name__)
        else:
            class_name = '{0:s}Label'.format(self.__name__)

        self.Label = type(class_name, (
            Label,
            BaseModel,),
                          dict(
                              __tablename__='{0:s}_label'.format(
                                  self.__tablename__),
                              parent_id=Column(
                                  Integer,
                                  ForeignKey('{0:s}.id'.format(
                                      self.__tablename__))),
                              parent=relationship(self)))
        return relationship(self.Label)

    def add_label(self, label, user=None):
        """Add a label to an object.

        Each entry can have multible labels.

        Args:
            label: Name of the label.
            user: Optional user that adds the label (sketch.User).
        """
        if self.has_label(label):
            return
        self.labels.append(self.Label(user=user, label=label))
        db_session.commit()

    def remove_label(self, label):
        """Remove a label from an object.

        Args:
            label: Name of the label.
        """
        for label_obj in self.labels:
            if label_obj.label.lower() != label.lower():
                continue
            self.labels.remove(label_obj)
        db_session.commit()

    def has_label(self, label):
        """Returns a boolean whether a label is applied.

        Args:
            label: Name of the label.

        Returns:
            True if the label is set, False otherwise.
        """
        for label_obj in self.labels:
            if label_obj.label.lower() == label.lower():
                return True

        return False

    @property
    def get_labels(self):
        """Returns a list of all applied labels.

        Returns:
            A list of strings with all the applied labels.
        """
        if not self.labels:
            return []

        return [x.label for x in self.labels]

    @property
    def label_string(self):
        """Returns a JSON encoded string with a list of the labels.

        Returns:
            A JSON encoded string with the list of labels.
        """
        if not self.labels:
            return ''

        return json.dumps([x.label for x in self.labels])


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
        if six.PY2:
            class_name = b'{0:s}Comment'.format(self.__name__)
        else:
            class_name = '{0:s}Comment'.format(self.__name__)

        self.Comment = type(
            class_name, (
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
        if six.PY2:
            class_name = b'{0:s}Status'.format(self.__name__)
        else:
            class_name = '{0:s}Status'.format(self.__name__)

        self.Status = type(
            class_name, (
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
            self.status.append(self.Status(user=None, status='new'))
        return self.status[0]
