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

from django.contrib import admin
from timesketch.apps.sketch.models import AccessControlEntry
from timesketch.apps.sketch.models import EventComment
from timesketch.apps.sketch.models import SavedView
from timesketch.apps.sketch.models import Sketch
from timesketch.apps.sketch.models import SketchTimeline
from timesketch.apps.sketch.models import Timeline


# Register your models here.
admin.site.register(Sketch)
admin.site.register(SketchTimeline)
admin.site.register(Timeline)
admin.site.register(EventComment)
admin.site.register(SavedView)
admin.site.register(AccessControlEntry)
