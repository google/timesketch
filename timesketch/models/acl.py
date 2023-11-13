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
"""This module implements the Access Control List (ACL) system.

The ACL systems is simple. It works by creating a many-to-many relationship
to the model that needs ACL functionality. This is implemented as a MixIn to
make it easy to annotate models to give them access to the ACL system.

The model has the following permissions: "read", "write" and "delete".
"""

import codecs
import json

import six

from flask_login import current_user
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy import not_
from sqlalchemy import Unicode
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship

from timesketch.models import BaseModel
from timesketch.models import db_session


class AccessControlEntry(object):
    """
    Access Control Entry database model. It has a user object (instance of
    timesketch.models.user.User) and a permission (read, write or delete).
    """

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

    @declared_attr
    def group_id(self):
        """Foreign key to a group model.

        Returns:
            A column (instance of sqlalchemy.Column)
        """
        return Column(Integer, ForeignKey("group.id"))

    @declared_attr
    def group(self):
        """A relationship to a group object.

        Returns:
            A relationship (instance of sqlalchemy.orm.relationship)
        """
        return relationship("Group")

    # Permission column (read, write or delete)
    permission = Column(Unicode(255))


class AccessControlMixin(object):
    """
    A MixIn for generating the necessary tables in the database and to make
    it accessible from the parent model object (the model object that uses this
    MixIn, i.e. the object that the ACL is added to).
    """

    @declared_attr
    def acl(self):
        """
        Generates the ACL tables and adds the attribute to the parent model
        object.

        Returns:
            A relationship to an ACE (timesketch.models.acl.AccessControlEntry)
        """
        self.AccessControlEntry = type(
            "%sAccessControlEntry" % self.__name__,
            (
                AccessControlEntry,
                BaseModel,
            ),
            dict(
                __tablename__="%s_accesscontrolentry" % self.__tablename__,
                parent_id=Column(Integer, ForeignKey("%s.id" % self.__tablename__)),
                parent=relationship(self, viewonly=True),
            ),
        )
        return relationship(self.AccessControlEntry)

    @classmethod
    def all_with_acl(cls, user=None):
        """
        Get all instances of the parent class that the user has read
        permission on. I.e enforce ACL permission check when fetching from
        the database.

        Args:
            user: A user (Instance of timesketch.models.user.User)

        Returns:
            A SQLAlchemy query (instance of sqlalchemy.orm.query.Query)
        """
        # If no user, assume the user that made the request.
        if not user:
            user = current_user

        # pylint: disable=singleton-comparison
        return cls.query.filter(
            or_(
                cls.AccessControlEntry.user == user,
                and_(
                    cls.AccessControlEntry.user == None,
                    cls.AccessControlEntry.group == None,
                ),
                cls.AccessControlEntry.group_id.in_(
                    [group.id for group in user.groups]
                ),
            ),
            cls.AccessControlEntry.permission == "read",
            cls.AccessControlEntry.parent,
        )

    def _get_ace(self, permission, user=None, group=None, check_group=True):
        """Get the specific access control entry for the user and permission.

        Args:
            permission: Permission as string (read, write or delete)
            user: A user (Instance of timesketch.models.user.User)
            group: A group (Instance of timesketch.models.user.Group)
            check_group: Check group permission, default is True.

        Returns:
            An ACE (instance of timesketch.models.acl.AccessControlEntry) or
            None if no ACE is found.
        """
        # If group is specified check if an ACE exist for it and return early.
        if group:
            return self.AccessControlEntry.query.filter_by(
                group=group, permission=permission, parent=self
            ).all()

        # Check access for user.
        ace = self.AccessControlEntry.query.filter_by(
            user=user, group=None, permission=permission, parent=self
        ).all()

        # If user doesn't have a direct ACE, check group permission.
        if (user and check_group) and not ace:
            group_intersection = set(user.groups) & set(self.groups)
            for _group in group_intersection:
                # Get group ACE with the requested permission.
                ace = self.AccessControlEntry.query.filter_by(
                    group=_group, permission=permission, parent=self
                ).all()
                if ace:
                    return ace
        return ace

    @property
    def my_permissions(self):
        """Return a string with the permissions of the current user."""
        has_permissions = []

        permissions = ["read", "write", "delete"]
        for permission in permissions:
            if self.has_permission(user=current_user, permission=permission):
                has_permissions.append(permission)

        if current_user.admin:
            has_permissions.append("admin")

        return json.dumps(has_permissions)

    @property
    def all_permissions(self):
        """Return a string with all object permissions."""
        return json.dumps(self.get_all_permissions())

    @property
    def groups(self):
        """List what groups have acess to this sketch.

        Returns:
            Set of groups (instance of timesketch.models.user.Group)
        """
        # pylint: disable=singleton-comparison
        group_aces = self.AccessControlEntry.query.filter(
            not_(self.AccessControlEntry.group == None),
            self.AccessControlEntry.parent == self,
        ).all()
        return set(ace.group for ace in group_aces)

    @property
    def is_public(self):
        """Determine if the ACL is open to everyone.

        Returns:
            An ACE (instance of timesketch.models.acl.AccessControlEntry) if the
            object is readable by everyone or None if the object is private.
        """
        return self._get_ace(permission="read", user=None, group=None)

    @property
    def collaborators(self):
        """Get list of users that have explicit read permission on the object.

        Returns:
            List of users (instances of timesketch.models.user.User)
        """
        # pylint: disable=singleton-comparison
        aces = self.AccessControlEntry.query.filter(
            not_(self.AccessControlEntry.user == self.user),
            not_(self.AccessControlEntry.user == None),
            self.AccessControlEntry.permission == "read",
            self.AccessControlEntry.parent == self,
        ).all()
        return set(ace.user for ace in aces)

    def get_all_permissions(self):
        """Get a dict of all users/groups that have permission on the object.

        Returns:
            Dict with users/groups as the key and permissions as the value.
                Usernames are prepended by user/ and groups by groups/.
        """
        return_dict = {}

        # pylint: disable=singleton-comparison
        aces = self.AccessControlEntry.query.filter(
            not_(self.AccessControlEntry.user == None),
            self.AccessControlEntry.parent == self,
        ).all()

        for ace in aces:
            name = "user/{0:s}".format(ace.user.username)
            return_dict.setdefault(name, [])
            return_dict[name].append(ace.permission)

        group_aces = self.AccessControlEntry.query.filter(
            not_(self.AccessControlEntry.group == None),
            self.AccessControlEntry.parent == self,
        ).all()

        for ace in group_aces:
            name = "group/{0:s}".format(ace.group.name)
            return_dict.setdefault(name, [])
            return_dict[name].append(ace.permission)

        return_dict["is_public"] = bool(self.is_public)

        return return_dict

    def get_permissions(self, permission):
        """Get a dict of users and groups that have permission on the object.

        Args:
            permission (str): the permission string (read, write or delete)

        Returns:
            Dict with users, groups and an indication of whether the sketch
            is public. Values are a set of user objects
            (instances of timesketch.models.user.User) or group objects
            (instances of timesketch.models.user.Group)
        """
        return_dict = {}

        # pylint: disable=singleton-comparison
        aces = self.AccessControlEntry.query.filter(
            not_(self.AccessControlEntry.user == None),
            self.AccessControlEntry.permission == permission,
            self.AccessControlEntry.parent == self,
        ).all()

        return_dict["users"] = set(ace.user for ace in aces)

        group_aces = self.AccessControlEntry.query.filter(
            not_(self.AccessControlEntry.group == None),
            self.AccessControlEntry.permission == permission,
            self.AccessControlEntry.parent == self,
        ).all()

        return_dict["groups"] = set(ace.group for ace in group_aces)

        return_dict["is_public"] = self.is_public
        return return_dict

    def has_permission(self, user, permission):
        """Check if the user has a specific permission.

        Args:
            user: A user (Instance of timesketch.models.user.User)
            permission: Permission as string (read, write or delete)

        Returns:
            An ACE (instance of timesketch.models.acl.AccessControlEntry) if the
            user has the permission or None if the user do not have the
            permission.
        """
        public_ace = self.is_public
        if public_ace and permission == "read":
            return public_ace
        if isinstance(permission, six.binary_type):
            permission = codecs.decode(permission, "utf-8")
        return self._get_ace(permission=permission, user=user)

    def grant_permission(self, permission, user=None, group=None):
        """Grant permission to a user or group  with the specific permission.

        Args:
            permission: Permission as string (read, write or delete)
            user: A user (Instance of timesketch.models.user.User)
            group: A group (Instance of timesketch.models.user.Group)
        """
        # Grant permission to a group.
        if group and not self._get_ace(permission, group=group):
            self.acl.append(self.AccessControlEntry(permission=permission, group=group))
            db_session.add(self)
            db_session.commit()
            return

        # Grant permission to a user.
        if not self._get_ace(permission, user=user, check_group=False):
            self.acl.append(self.AccessControlEntry(permission=permission, user=user))
            db_session.add(self)
            db_session.commit()

    def revoke_permission(self, permission, user=None, group=None):
        """Revoke permission for user/group on the object.

        Args:
            permission: Permission as string (read, write or delete)
            user: A user (Instance of timesketch.models.user.User)
            group: A group (Instance of timesketch.models.user.Group)
        """
        # Revoke permission for a group.
        if group:
            group_ace = self._get_ace(permission=permission, group=group)
            if group_ace:
                for ace in group_ace:
                    self.acl.remove(ace)
                db_session.add(self)
                db_session.commit()
            return

        # Revoke permission for a user.
        user_ace = self._get_ace(permission=permission, user=user)
        if user_ace:
            for ace in user_ace:
                self.acl.remove(ace)
            db_session.add(self)
            db_session.commit()
