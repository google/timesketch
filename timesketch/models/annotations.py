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


import json
import logging

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship
from sqlalchemy.orm import subqueryload

from timesketch.models import BaseModel
from timesketch.models import db_session

logger = logging.getLogger("timesketch.models.annotations")


class BaseAnnotation:
    """Base class with common attributes."""

    @declared_attr
    def user_id(self):
        """Foreign key to a user model.

        Returns:
            A column (instance of sqlalchemy.Column)
        """
        return Column(Integer, ForeignKey("user.id"))

    @declared_attr
    def user(self):
        """A relationship to a user object.

        Returns:
            A relationship (instance of sqlalchemy.orm.relationship)
        """
        return relationship("User")


class Label(BaseAnnotation):
    """A label annotation."""

    label = Column(Unicode(255))


class Comment(BaseAnnotation):
    """A comment annotation."""

    comment = Column(UnicodeText())


class Status(BaseAnnotation):
    """A status annotation."""

    status = Column(Unicode(255))


class GenericAttribute(BaseAnnotation):
    """Implements the attribute model."""

    name = Column(UnicodeText())
    value = Column(UnicodeText())
    ontology = Column(UnicodeText())
    description = Column(UnicodeText())


class LabelMixin:
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
        class_name = f"{self.__name__:s}Label"

        self.Label = type(
            class_name,
            (
                Label,
                BaseModel,
            ),
            {
                "__tablename__": f"{self.__tablename__:s}_label",
                "parent_id": Column(Integer, ForeignKey(f"{self.__tablename__:s}.id")),
                "parent": relationship(self, viewonly=True),
            },
        )
        return relationship(self.Label)

    def add_label(self, label, user=None):
        """Add a label to an object.

        Each entry can have multiple labels.

        Args:
            label: Name of the label.
            user: Optional user that adds the label (sketch.User).
        """
        if self.has_label(label):
            return
        self.labels.append(self.Label(user=user, label=label))
        db_session.add(self)
        db_session.commit()

    def remove_label(self, label):
        """Remove a label from an object.

        Args:
            label: Name of the label.
        """
        labels_to_remove = [
            label_obj
            for label_obj in self.labels
            if label_obj.label.lower() == label.lower()
        ]

        if not labels_to_remove:
            logger.warning(
                "Attempted to remove non-existent label: %s from object: %s",
                str(label),
                str(type(self).__name__),
            )

        for label_obj in labels_to_remove:
            self.labels.remove(label_obj)
        db_session.add(self)
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
            return ""

        return json.dumps([x.label for x in self.labels])


class CommentMixin:
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
        class_name = f"{self.__name__:s}Comment"

        self.Comment = type(
            class_name,
            (
                Comment,
                BaseModel,
            ),
            {
                "__tablename__": f"{self.__tablename__:s}_comment",
                "parent_id": Column(Integer, ForeignKey(f"{self.__tablename__:s}.id")),
                "parent": relationship(self, viewonly=True),
            },
        )
        return relationship(self.Comment)

    @classmethod
    def get_with_comments(cls, **kwargs):
        """Eagerly loads comments for a given object query using subquery.

        subqueryload is more efficient than joinedload for many-to-one
        references on large datasets.

        Args:
            kwargs: Keyword arguments passed to filter_by.

        Returns:
            List of objects with comments eagerly loaded.
        """
        return cls.query.filter_by(**kwargs).options(subqueryload(cls.comments))

    def remove_comment(self, comment_id):
        """Remove a comment from an event.

        Args:
            comment_id: Id of the comment.

        Returns:
            True if the comment was removed, False otherwise.
        """

        comments_to_remove = [
            comment_obj
            for comment_obj in self.comments
            if comment_obj.id == int(comment_id)
        ]
        if not comments_to_remove:
            logger.debug("Comment to delete not found")
            return False  # Comment not found
        for comment_obj in comments_to_remove:
            logger.debug("Removing comment")
            self.comments.remove(comment_obj)
        db_session.add(self)
        db_session.commit()
        return True

    def get_comment(self, comment_id):
        """Retrieves a comment.

        Args:
            comment_id: Id of the comment.

        Returns:
            The comment object, or None if the comment does not exist.
        """
        for comment_obj in self.comments:
            if comment_obj.id == int(comment_id):
                return comment_obj
        return None

    def update_comment(self, comment_id, comment):
        """Update an existing comment.

        Args:
            comment: Comment object with updated comment text.
        """
        for comment_obj in self.comments:
            if comment_obj.id == int(comment_id):
                comment_obj.comment = comment
                db_session.add(self)
                db_session.commit()
                return comment_obj

        return False


class StatusMixin:
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
        class_name = f"{self.__name__:s}Status"

        self.Status = type(
            class_name,
            (
                Status,
                BaseModel,
            ),
            {
                "__tablename__": f"{self.__tablename__:s}_status",
                "parent_id": Column(Integer, ForeignKey(f"{self.__tablename__:s}.id")),
                "parent": relationship(self, viewonly=True),
            },
        )
        return relationship(self.Status)

    def set_status(self, status):
        """
        Set status on object. Although this is a many-to-many relationship
        this makes sure that the parent object only has one status set.

        Args:
            status: Name of the status
        """
        self.status = []  # replace the list with an empty list.
        self.status.append(self.Status(user=None, status=status))
        db_session.add(self)
        db_session.commit()

    @property
    def get_status(self):
        """Get the current status.

        Only one status should be in the database at a time.

        Raises:
            RuntimeError: If more than one status is available.

        Returns:
            The status as a string
        """
        if not self.status:
            self.status.append(self.Status(user=None, status="new"))
        if len(self.status) > 1:
            self_id = self.id if hasattr(self, "id") else None
            # TODO: Change from warning to raising an exception once we ensured
            # it won't affect the deployment.
            # raise RuntimeError(
            # "More than one status available for object [%s] with ID: [%s]",
            #     str(type(self).__name__),
            #     str(self_id),
            # )
            logging.warning(
                "More than one status available for object [%s] with ID: [%s]",
                str(type(self).__name__),
                str(self_id),
            )
        return self.status[0]


class GenericAttributeMixin:
    """
    A MixIn for generating the necessary tables in the database and to make
    it accessible from the parent model object (the model object that uses this
    MixIn, i.e. the object that the attribute is added to).
    """

    @declared_attr
    def genericattributes(self):
        """
        Generates the status tables and adds the attribute to the parent model
        object.

        Returns:
            A relationship with (timesketch.models.annotation.GenericAttribute)
        """
        class_name = f"{self.__name__:s}GenericAttribute"

        self.GenericAttribute = type(
            class_name,
            (
                GenericAttribute,
                BaseModel,
            ),
            {
                "__tablename__": f"{self.__tablename__:s}_genericattribute",
                "parent_id": Column(Integer, ForeignKey(f"{self.__tablename__:s}.id")),
                "parent": relationship(self, viewonly=True),
            },
        )
        return relationship(self.GenericAttribute)

    def add_attribute(self, name, value, ontology=None, user=None, description=None):
        """Add a attribute to an object.

        Each entry can have multiple generic attributes.

        Args:
            name: Name of the attribute.
            value: Value of the attribute.
            ontology: Optional ontology of the attribute.
            user: Optional user that adds the attribute (timesketch.models.user.User).
            description: Optional description of the attribute.
        """
        self.genericattributes.append(
            self.GenericAttribute(
                user=user,
                name=name,
                value=value,
                ontology=ontology,
                description=description,
            )
        )
        db_session.add(self)
        db_session.commit()

    @property
    def get_attributes(self):
        """Returns a list of all attributes.

        Returns:
            A list of strings with all attributes.
        """
        if not self.genericattributes:
            return []
        return self.genericattributes
