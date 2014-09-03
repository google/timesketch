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
from django.contrib import admin
from django.contrib.auth.models import User
import random


class Sketch(models.Model):
    """Database model for a Sketch"""
    owner = models.ForeignKey(User)
    collaborators = models.ManyToManyField("Collaborator", blank=True,
                                           null=True)
    acl_public = models.BooleanField(default=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    timelines = models.ManyToManyField("SketchTimeline", blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def get_named_views(self):
        """
        Get named views for this sketch. Used in templates.

        Returns:
            A query set.
        """
        return SavedView.objects.filter(sketch=self).exclude(name="")

    def can_access(self, user):
        if self.owner == user:
            return True
        if self.acl_public:
            return True
        return False

    def __unicode__(self):
        return '%s' % self.title


class Timeline(models.Model):
    """Database model for a timeline."""
    owner = models.ForeignKey(User)
    collaborators = models.ManyToManyField("Collaborator", blank=True,
                                           null=True)
    acl_public = models.BooleanField(default=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    datastore_index = models.CharField(max_length=32)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def can_access(self, user):
        if self.owner == user:
            return True
        if self.acl_public:
            return True
        return False

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
        """
        Picks a random color used when creating a SketchTimeline.

        Returns:
            string
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


class Collaborator(models.Model):
    """Database model for a collaborator."""
    user = models.ForeignKey(User)
    can_edit = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return '%s' % self.user.username


# Register the models so the admin interface can use them.
admin.site.register(Sketch)
admin.site.register(SketchTimeline)
admin.site.register(Timeline)
admin.site.register(EventComment)
admin.site.register(Collaborator)
admin.site.register(SavedView)
