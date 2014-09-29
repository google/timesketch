# Copyright 2014 Google Inc. All rights reserved.
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
"""Django database model for creating Access Control Lists."""

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User


class AccessControlEntry(models.Model):
    """Model for an access control entry.
    The permission model is simple. You have read, write and delete permissions
    on Django ORM objects.

    The model is using the Django content type framework:
        https://docs.djangoproject.com/en/dev/ref/contrib/contenttypes/

    The content type framework gives us a generic interface to work with
    other Django models.
    """
    user = models.ForeignKey(User, blank=True, null=True)
    permission_read = models.BooleanField(default=False)
    permission_write = models.BooleanField(default=False)
    permission_delete = models.BooleanField(default=False)
    # pylint: disable=no-value-for-parameter
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return 'ACE for %s on %s %s' % (
            self.user, self.content_type, self.content_object)


class AccessControlMixIn(object):
    """MixIn for classes with generic relationship with AccessControlEntry.
    Common functions to manipulate and use the permission system.
    """
    def is_public(self):
        """Determine if the ACL is open to everyone for the specific object.

        Returns:
            Boolean value to indicate if the object is readable by everyone.
        """
        try:
            self.acl.get(user=None, permission_read=True)
            return True
        except ObjectDoesNotExist:
            return False

    def make_public(self, user):
        """Make object public.

        Args:
            user. user object (instance of django.contrib.auth.models.User)
        """
        if not self.can_write(user):
            return
        try:
            ace = self.acl.get(user=None)
            if not ace.read:
                ace.permission_read = True
                ace.save()
        except ObjectDoesNotExist:
            self.acl.create(user=None, permission_read=True)

    def make_private(self, user):
        """Make object private.

        Args:
            user. user object (instance of django.contrib.auth.models.User)
        """
        if not self.can_write(user):
            return
        try:
            ace = self.acl.get(user=None)
            ace.delete()
        except ObjectDoesNotExist:
            pass

    def can_read(self, user):
        """Determine if the user have read access to the specific object.
        1) If the objects owner is the same as the user in the request, or the
           object is public then access is granted.

        2) If the user in the request have an AccessControlEntry for the object
           and the read permission is set to True then access is granted.

        Args:
            user. user object (instance of django.contrib.auth.models.User)
        Returns:
            Boolean value to indicate if the object is readable by user.
        """
        if self.user == user:
            return True
        if self.is_public():
            return True
        try:
            ace = self.acl.get(user=user)
        except ObjectDoesNotExist:
            return False
        if ace.permission_read:
            return True
        return False

    def can_write(self, user):
        """Determine if the user have write access to the object.
        1) If the objects owner is the same as the user in the request
           then access is granted.

        2) If the user in the request have an ACE entry for the object and the
           write permission is set to True then access is granted.

        Args:
            user. user object (instance of django.contrib.auth.models.User)
        Returns:
            Boolean value to indicate if the object is writable by user.
        """
        if self.user == user:
            return True
        try:
            self.acl.get(user=user, permission_write=True)
            return True
        except ObjectDoesNotExist:
            return False

    def get_collaborators(self):
        """Get all users that has read-write access to this sketch.

        Returns:
            A set() of User objects
        """
        collaborators_set = set()
        for ace in self.acl.all():
            if ace.user and not ace.user == self.user:
                collaborators_set.add(ace)
        return collaborators_set
