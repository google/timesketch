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

from .resources.aggregation import AggregationGroupResource
from .resources.aggregation import AggregationGroupListResource
from .resources.aggregation import AggregationListResource
from .resources.aggregation import AggregationExploreResource
from .resources.aggregation import AggregationInfoResource
from .resources.aggregation import AggregationResource
from .resources.analysis import AnalysisResource
from .resources.analysis import AnalyzerRunResource
from .resources.analysis import AnalyzerSessionResource
from .resources.explore import ExploreResource
from .resources.event import EventResource
from .resources.event import EventAnnotationResource
from .resources.event import EventCreateResource
from .resources.event import EventTaggingResource
from .resources.event import CountEventsResource
from .resources.sketch import SketchResource
from .resources.sketch import SketchListResource
from .resources.archive import SketchArchiveResource
from .resources.view import ViewResource
from .resources.view import ViewListResource
from .resources.searchtemplate import SearchTemplateResource
from .resources.searchtemplate import SearchTemplateListResource
from .resources.upload import UploadFileResource
from .resources.task import TaskResource
from .resources.story import StoryListResource
from .resources.story import StoryResource
from .resources.explore import QueryResource
from .resources.timeline import TimelineResource
from .resources.timeline import TimelineListResource
from .resources.searchindex import SearchIndexListResource
from .resources.searchindex import SearchIndexResource
from .resources.session import SessionResource
from .resources.user import UserListResource
from .resources.user import GroupListResource
from .resources.user import CollaboratorResource
from .resources.user import LoggedInUserResource


# Disable error for long line. Readability is more important than line
# length in this case.
# pylint: disable=line-too-long
API_ROUTES = [
    (SketchListResource, '/sketches/'),
    (SketchResource, '/sketches/<int:sketch_id>/'),
    (SketchArchiveResource, '/sketches/<int:sketch_id>/archive/'),
    (AnalysisResource, '/sketches/<int:sketch_id>/timelines/<int:timeline_id>/analysis/'),
    (AnalyzerRunResource, '/sketches/<int:sketch_id>/analyzer/'),
    (AnalyzerSessionResource, '/sketches/<int:sketch_id>/analyzer/sessions/<int:session_id>/'),
    (AggregationListResource, '/sketches/<int:sketch_id>/aggregation/'),
    (AggregationGroupResource, '/sketches/<int:sketch_id>/aggregation/group/<int:group_id>/'),
    (AggregationGroupListResource, '/sketches/<int:sketch_id>/aggregation/group/'),
    (AggregationExploreResource, '/sketches/<int:sketch_id>/aggregation/explore/'),
    (AggregationInfoResource, '/aggregation/info/'),
    (AggregationResource, '/sketches/<int:sketch_id>/aggregation/<int:aggregation_id>/'),
    (ExploreResource, '/sketches/<int:sketch_id>/explore/'),
    (EventResource, '/sketches/<int:sketch_id>/event/'),
    (EventTaggingResource, '/sketches/<int:sketch_id>/event/tagging/'),
    (EventAnnotationResource, '/sketches/<int:sketch_id>/event/annotate/'),
    (EventCreateResource, '/sketches/<int:sketch_id>/event/create/'),
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
    (SessionResource, '/sketches/<int:sketch_id>/explore/sessions/<string:timeline_index>'),
    (UserListResource, '/users/'),
    (GroupListResource, '/groups/'),
    (CollaboratorResource, '/sketches/<int:sketch_id>/collaborators/'),
    (LoggedInUserResource, '/users/me/')
]
