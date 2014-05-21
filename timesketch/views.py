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
"""This module implements timesketch Django views."""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from timesketch.models import Sketch
from timesketch.models import Timeline
from timesketch.models import SavedView


@login_required
def home_view(request):
    """Renders the available sketches for the user."""
    mine = Sketch.objects.filter(owner=request.user).order_by("-created")
    public = Sketch.objects.filter(acl_public=True).exclude(owner=request.user)
    return render(request, 'timesketch/home.html',
      {"my_sketches": mine, "public_sketches": public})


@login_required
def sketch_view(request, sketch_id):
    """Renders specific sketch."""  
    sketch = Sketch.objects.get(id=sketch_id)
    timelines = Timeline.objects.all()
    views = SavedView.objects.filter(sketch=sketch)
    views = views.exclude(name="").order_by("-created")
    return render(request, 'timesketch/sketch.html',
                  {"sketch": sketch, "timelines": timelines, "views": views})


@login_required
def explore_view(request, sketch_id):
    """Renders the search interface."""
    sketch = Sketch.objects.get(id=sketch_id)
    view = request.GET.get('view', 0)
    timelines = [t.timeline.datastore_index for t in sketch.timelines.all()]
    timelines = ",".join(timelines)
    return render(request, 'timesketch/explore.html', {"timelines": timelines, 
      "sketch": sketch, "view": view})


@login_required
def event_view(request, index_id, event_id):
    """Renders the event page. This is used for ng-include in the tamplates."""
    return render(request, 'timesketch/event.html', {"index_id": index_id,
      "event_id": event_id})
