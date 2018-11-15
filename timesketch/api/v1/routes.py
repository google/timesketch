# Copyright 2018 Google Inc. All rights reserved.
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
"""URL routes for API resources."""

from __future__ import unicode_literals

from .resources import AggregationResource
from .resources import ExploreResource
from .resources import EventResource
from .resources import EventAnnotationResource
from .resources import EventCreateResource
from .resources import GraphResource
from .resources import SketchResource
from .resources import SketchListResource
from .resources import ViewResource
from .resources import ViewListResource
from .resources import SearchTemplateResource
from .resources import SearchTemplateListResource
from .resources import UploadFileResource
from .resources import TaskResource
from .resources import StoryListResource
from .resources import StoryResource
from .resources import QueryResource
from .resources import CountEventsResource
from .resources import TimelineResource
from .resources import TimelineListResource
from .resources import SearchIndexListResource
from .resources import SearchIndexResource


# Disable error for long line. Readability is more important than line
# length in this case.
# pylint: disable=line-too-long
API_ROUTES = [
    (SketchListResource, '/sketches/'),
    (SketchResource, '/sketches/<int:sketch_id>/'),
    (AggregationResource, '/sketches/<int:sketch_id>/aggregation/'),
    (ExploreResource, '/sketches/<int:sketch_id>/explore/'),
    (EventResource, '/sketches/<int:sketch_id>/event/'),
    (EventAnnotationResource, '/sketches/<int:sketch_id>/event/annotate/'),
    (EventCreateResource, u'/sketches/<int:sketch_id>/event/create/'),
    (ViewListResource, '/sketches/<int:sketch_id>/views/'),
    (ViewResource, '/sketches/<int:sketch_id>/views/<int:view_id>/'),
    (SearchTemplateListResource, '/searchtemplate/'),
    (SearchTemplateResource, '/searchtemplate/<int:searchtemplate_id>/'),
    (UploadFileResource, '/upload/'),
    (TaskResource, '/tasks/'),
    (StoryListResource, '/sketches/<int:sketch_id>/stories/'),
    (StoryResource, '/sketches/<int:sketch_id>/stories/<int:story_id>/'),
    (QueryResource, '/sketches/<int:sketch_id>/explore/query/'),
    (CountEventsResource, '/sketches/<int:sketch_id>/count/'),
    (TimelineListResource, '/sketches/<int:sketch_id>/timelines/'),
    (TimelineResource, '/sketches/<int:sketch_id>/timelines/<int:timeline_id>/'),
    (SearchIndexListResource, '/searchindices/'),
    (SearchIndexResource, '/searchindices/<int:searchindex_id>/'),
    (GraphResource, '/sketches/<int:sketch_id>/explore/graph/')
]
