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

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib import admin
import os
from PIL import Image


class UserProfile(models.Model):
    user = models.OneToOneField(User)
    avatar = models.ImageField(upload_to="avatars", null=True, blank=True)

    def resize_avatar(self):
        if self.avatar:
            filename = self.avatar.path
            image = Image.open(filename)
            image.thumbnail((50, 50), Image.ANTIALIAS)
            image.save(filename)

    def get_avatar_url(self):
        """
        Return avatar URL to use in templates.
        """
        if not self.avatar:
            return settings.STATIC_URL + "img/avatar_unknown.jpg"
        image = os.path.basename(self.avatar.url)
        #if image == "avatar_unknown.jpg":
        #    return settings.STATIC_URL + "img/avatar_unknown.jpg"
        return settings.MEDIA_URL + "avatars/" + image

    def __unicode__(self):
        return '%s' % self.user.username


def create_user_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = UserProfile.objects.create(user=instance)
        user_profile.save()


def update_user_profile(sender, instance, created, **kwargs):
    if not created:
        instance.resize_avatar()


post_save.connect(create_user_profile, sender=User)
post_save.connect(update_user_profile, sender=UserProfile)

admin.site.register(UserProfile)
