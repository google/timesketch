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
"""This module implements timesketch Django database models."""

from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.generic import GenericRelation
from django.core.exceptions import ObjectDoesNotExist
import random


class Sketch(models.Model):
    """Database model for a Sketch"""
    owner = models.ForeignKey(User)
    acl = GenericRelation('AccessControlEntry')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    timelines = models.ManyToManyField("SketchTimeline", blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def is_public(self):
        """Determine if this sketch is readable to anyone.

        Returns:
            True or False
        """
        return ace_is_public(self)

    def make_public(self, user):
        """Make the sketch public.

        Args:
            user. django.contrib.auth.models.User object
        """
        ace_make_public(self, user)

    def make_private(self, user):
        """Make the sketch private.

        Args:
            user. django.contrib.auth.models.User object
        """
        ace_make_private(self, user)

    def can_read(self, user):
        """Determine if user can access this sketch.

        Args:
            user. django.contrib.auth.models.User object
        Returns:
            True or False
        """
        return ace_can_read(self, user)

    def collaborators(self):
        """Function to get all users that has rw access to this sketch.

        Returns:
            A set() of User objects
        """
        collaborators_set = set()
        for ace in self.acl.all():
            if ace.user and not ace.user == self.owner:
                collaborators_set.add(ace)
        return collaborators_set

    def __unicode__(self):
        return '%s' % self.title


class Timeline(models.Model):
    """Database model for a timeline."""
    owner = models.ForeignKey(User)
    acl = GenericRelation('AccessControlEntry')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    datastore_index = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def is_public(self):
        """Determine if this timeline is readable to anyone.

        Returns:
            True or False
        """
        return ace_is_public(self)

    def make_public(self, user):
        """Make the timeline public.

        Args:
            user. django.contrib.auth.models.User object
        """
        ace_make_public(self, user)

    def make_private(self, user):
        """Make the timeline private.

        Args:
            user. django.contrib.auth.models.User object
        """
        ace_make_private(self, user)

    def can_read(self, user):
        """Determine if user can access this timeline.

        Args:
            user. django.contrib.auth.models.User object
        Returns:
            True or False
        """
        return ace_can_read(self, user)

    def __unicode__(self):
        return '%s' % self.title


class SketchTimeline(models.Model):
    """Database model for annotating a timeline."""
    timeline = models.ForeignKey(Timeline)
    color = models.CharField(max_length=6, default="FFFFFF")
    visible = models.BooleanField(default=True)
    deleted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @staticmethod
    def generate_color():
        """Picks a random color used when creating a SketchTimeline.

        Returns:
            String
        """
        colors = ["ECEEE1", "A8DACF", "F0D697", "D8D692", "F2B7DC", "9798DE"]
        return random.choice(colors)

    def __unicode__(self):
        return '%s' % self.timeline.title


class EventComment(models.Model):
    """Database model for a event comment."""
    user = models.ForeignKey(User)
    body = models.TextField(null=False, blank=False)
    sketch = models.ForeignKey(Sketch)
    datastore_id = models.CharField(max_length=255)
    datastore_index = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s' % self.datastore_id


class SavedView(models.Model):
    """Database model for a saved view."""
    user = models.ForeignKey(User)
    sketch = models.ForeignKey(Sketch)
    query = models.CharField(max_length=255)
    filter = models.TextField()
    name = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s %s %s %s' % (self.created, self.user, self.sketch,
                                self.name)


class AccessControlEntry(models.Model):
    """Model for an access control entry."""
    user = models.ForeignKey(User, blank=True, null=True)
    # Permissions
    permission_read = models.BooleanField(default=False)
    permission_write = models.BooleanField(default=False)
    permission_delete = models.BooleanField(default=False)
    # contentypes for generic relations
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey()
    #
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return 'ACE for %s on %s %s' % (self.user, self.content_type,
                                        self.content_object)


def ace_is_public(obj):
    """Function to determine if the ACL is open to everyone for the specific
    object.

    Args:
        obj. django.db model object
    Returns:
        True or False
    """
    # ACE without any user is used as the public ACE.
    try:
        obj.acl.get(user=None, permission_read=True)
        return True
    except ObjectDoesNotExist:
        return False


def ace_make_public(obj, user):
    """Function to make object public.

    Args:
        obj. django.db model object
        user. django.contrib.auth.models.User object
    """
    # First see if the user is allowed to make this change.
    if not ace_can_write(obj, user):
        return
    try:
        ace = obj.acl.get(user=None)
        if not ace.read:
            ace.permission_read = True
            ace.save()
    except ObjectDoesNotExist:
        obj.acl.create(user=None, permission_read=True)


def ace_make_private(obj, user):
    """Function to make object private.

    Args:
        obj. django.db model object
        user. django.contrib.auth.models.User object
    """
    # First see if the user is allowed to make this change.
    if not ace_can_write(obj, user):
        return
    try:
        ace = obj.acl.get(user=None)
        ace.delete()
    except ObjectDoesNotExist:
        pass


def ace_can_read(obj, user):
    """Function to determine if the user have read access to the specific object.

    Args:
        obj. django.db model object
        user. django.contrib.auth.models.User object
    Returns:
        True or False
    """
    # Is the objects owner is same as user or the object is public then access
    # is granted.
    if obj.owner == user:
        return True
    if ace_is_public(obj):
        return True
    # Private object. If we have a ACE for the user on this object and that ACE
    # has read rights. If so, then access is granted.
    try:
        ace = obj.acl.get(user=user)
    except ObjectDoesNotExist:
        return False
    if ace.permission_read:
        return True
    return False


def ace_can_write(obj, user):
    """Function to determine if the user have write access to the object.

    Args:
        obj. django.db model object
        user. django.contrib.auth.models.User object
    Returns:
        True or False
    """
    # Is the objects owner is same as user or the object is public then write
    # access is granted.
    if obj.owner == user:
        return True
    # Private object. If we have a ACE for the user on this object and that ACE
    # has write rights. If so, then access is granted.
    try:
        obj.acl.get(user=user, permission_write=True)
        return True
    except ObjectDoesNotExist:
        return False
