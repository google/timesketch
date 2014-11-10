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
# ToDo: Clean up the models (see github issue #25)

import random

from django.db import models
from django.contrib.contenttypes.generic import GenericRelation
from django.contrib.auth.models import User

from timesketch.apps.acl.models import AccessControlEntry
from timesketch.apps.acl.models import AccessControlMixIn


class Sketch(AccessControlMixIn, models.Model):
    """Database model for a Sketch entry."""
    user = models.ForeignKey(User)
    acl = GenericRelation(AccessControlEntry)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def timelines(self):
        """
        Get timelines for this sketch. This is used in both Django views and
        templates.

        Returns:
            A Django QuerySet for SketchTimeline.
        """
        return SketchTimeline.objects.filter(sketch=self)

    # ToDo: Make this a property
    def get_named_views(self):
        """
        Get named saved views for this sketch.

        Returns:
            A Django QuerySet for SavedView.
        """
        return SavedView.objects.filter(sketch=self).exclude(name="")

    def __unicode__(self):
        return '%s' % self.title


class Timeline(AccessControlMixIn, models.Model):
    """Database model for a timeline."""
    user = models.ForeignKey(User)
    acl = GenericRelation(AccessControlEntry)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    datastore_index = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s' % self.title


class SketchTimeline(models.Model):
    """Database model for annotating a timeline."""
    user = models.ForeignKey(User)
    sketch = models.ForeignKey(Sketch)
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
            String. HEX color as string
        """
        colors = ['ECEEE1', 'A8DACF', 'F0D697', 'D8D692', 'F2B7DC', '9798DE']
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
