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

from flask_login import current_user
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
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
        return Column(Integer, ForeignKey(u'user.id'))

    @declared_attr
    def user(self):
        """A relationship to a user object.

        Returns:
            A relationship (instance of sqlalchemy.orm.relationship)
        """
        return relationship(u'User')

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
            '%sAccessControlEntry' % self.__name__,
            (AccessControlEntry, BaseModel,),
            dict(
                __tablename__='%s_accesscontrolentry' % self.__tablename__,
                parent_id=Column(
                    Integer, ForeignKey('%s.id' % self.__tablename__)),
                parent=relationship(self),
            )
        )
        return relationship(self.AccessControlEntry)

    @classmethod
    def all_with_acl(cls, user=None):
        """
        Get all instances of the parent class that the user has read
        permission on. I.e enforce ACL permission check when fetching from
        the database.

        Returns:
            An ACL base query (instance of timesketch.models.AclBaseQuery)
        """
        # If no user, assume the user that made the request.
        if not user:
            user = current_user

        # pylint: disable=singleton-comparison
        return cls.query.filter(
            or_(
                cls.AccessControlEntry.user == user,
                cls.AccessControlEntry.user == None),
            cls.AccessControlEntry.permission == u'read',
            cls.AccessControlEntry.parent)

    def _get_ace(self, user, permission):
        """Get the specific access control entry for the user and permission.

        Returns:
            An ACE (instance of timesketch.models.acl.AccessControlEntry) or
            None if no ACE is found.
        """
        return self.AccessControlEntry.query.filter_by(
            user=user, permission=permission, parent=self).all()

    @property
    def is_public(self):
        """Determine if the ACL is open to everyone.

        Returns:
            An ACE (instance of timesketch.models.acl.AccessControlEntry) if the
            object is readable by everyone or None if the object is private.
        """
        return self._get_ace(user=None, permission=u'read')

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
            self.AccessControlEntry.permission == u'read',
            self.AccessControlEntry.parent == self).all()
        return set(ace.user for ace in aces)

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
        return self._get_ace(user=user, permission=unicode(permission))

    def grant_permission(self, user, permission):
        """Grant permission to a user with the specific permission.

        Args:
            user: A user (Instance of timesketch.models.user.User)
            permission: Permission as string (read, write or delete)
        """
        if not self._get_ace(user, permission):
            self.acl.append(
                self.AccessControlEntry(
                    user=user, permission=permission))
            db_session.commit()

    def revoke_permission(self, user, permission):
        """Revoke permission to a user with the specific permission.

        Args:
            user: A user (Instance of timesketch.models.user.User)
            permission: Permission as string (read, write or delete)
        """
        for ace in self._get_ace(user, permission):
            self.acl.remove(ace)
        db_session.commit()
