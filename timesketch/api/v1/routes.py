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
from .resources.analysis import AnalyzerSessionActiveListResource
from .resources.analysis import AnalyzerSessionResource
from .resources.attribute import AttributeResource
from .resources.explore import ExploreResource
from .resources.explore import SearchHistoryResource
from .resources.explore import SearchHistoryTreeResource
from .resources.datafinder import DataFinderResource
from .resources.datasource import DataSourceResource
from .resources.datasource import DataSourceListResource
from .resources.event import EventResource
from .resources.event import EventAnnotationResource
from .resources.event import EventCreateResource
from .resources.event import EventTaggingResource
from .resources.event import EventUnTagResource
from .resources.event import EventAddAttributeResource
from .resources.event import CountEventsResource
from .resources.event import MarkEventsWithTimelineIdentifier
from .resources.sketch import SketchResource
from .resources.sketch import SketchListResource
from .resources.archive import SketchArchiveResource
from .resources.information import VersionResource
from .resources.view import ViewResource
from .resources.view import ViewListResource
from .resources.searchtemplate import SearchTemplateResource
from .resources.searchtemplate import SearchTemplateParseResource
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
from .resources.user import UserResource
from .resources.user import UserSettingsResource
from .resources.user import GroupListResource
from .resources.user import CollaboratorResource
from .resources.user import LoggedInUserResource
from .resources.sigma import SigmaRuleResource
from .resources.sigma import SigmaRuleListResource
from .resources.sigma import SigmaRuleByTextResource
from .resources.graph import GraphListResource
from .resources.graph import GraphResource
from .resources.graph import GraphPluginListResource
from .resources.graph import GraphCacheResource
from .resources.intelligence import TagMetadataResource
from .resources.contextlinks import ContextLinkConfigResource
from .resources.unfurl import UnfurlResource
from .resources.nl2q import Nl2qResource
from .resources.settings import SystemSettingsResource

from .resources.scenarios import ScenarioTemplateListResource
from .resources.scenarios import ScenarioListResource
from .resources.scenarios import ScenarioResource
from .resources.scenarios import ScenarioStatusResource
from .resources.scenarios import FacetListResource
from .resources.scenarios import QuestionOrphanListResource
from .resources.scenarios import QuestionWithScenarioListResource
from .resources.scenarios import QuestionWithFacetListResource
from .resources.scenarios import QuestionTemplateListResource
from .resources.scenarios import QuestionListResource
from .resources.scenarios import QuestionResource
from .resources.scenarios import QuestionConclusionListResource
from .resources.scenarios import QuestionConclusionResource


# Disable error for long line. Readability is more important than line
# length in this case.
# pylint: disable=line-too-long
API_ROUTES = [
    (SketchListResource, "/sketches/"),
    (SketchResource, "/sketches/<int:sketch_id>/"),
    (SketchArchiveResource, "/sketches/<int:sketch_id>/archive/"),
    (
        AnalysisResource,
        "/sketches/<int:sketch_id>/timelines/<int:timeline_id>/analysis/",
    ),
    (AnalyzerRunResource, "/sketches/<int:sketch_id>/analyzer/"),
    (
        AnalyzerSessionActiveListResource,
        "/sketches/<int:sketch_id>/analyzer/sessions/active/",
    ),
    (
        AnalyzerSessionResource,
        "/sketches/<int:sketch_id>/analyzer/sessions/<int:session_id>/",
    ),
    (AggregationListResource, "/sketches/<int:sketch_id>/aggregation/"),
    (
        AggregationGroupResource,
        "/sketches/<int:sketch_id>/aggregation/group/<int:group_id>/",
    ),
    (
        AggregationGroupListResource,
        "/sketches/<int:sketch_id>/aggregation/group/",
    ),
    (
        AggregationExploreResource,
        "/sketches/<int:sketch_id>/aggregation/explore/",
    ),
    (AggregationInfoResource, "/aggregation/info/"),
    (
        AggregationResource,
        "/sketches/<int:sketch_id>/aggregation/<int:aggregation_id>/",
    ),
    (ExploreResource, "/sketches/<int:sketch_id>/explore/"),
    (SearchHistoryResource, "/sketches/<int:sketch_id>/searchhistory/"),
    (
        SearchHistoryTreeResource,
        "/sketches/<int:sketch_id>/searchhistorytree/",
    ),
    (EventResource, "/sketches/<int:sketch_id>/event/"),
    (EventAddAttributeResource, "/sketches/<int:sketch_id>/event/attributes/"),
    (EventTaggingResource, "/sketches/<int:sketch_id>/event/tagging/"),
    (EventUnTagResource, "/sketches/<int:sketch_id>/event/untag/"),
    (EventAnnotationResource, "/sketches/<int:sketch_id>/event/annotate/"),
    (EventCreateResource, "/sketches/<int:sketch_id>/event/create/"),
    (
        MarkEventsWithTimelineIdentifier,
        "/sketches/<int:sketch_id>/event/add_timeline_id/",
    ),
    (ViewListResource, "/sketches/<int:sketch_id>/views/"),
    (AttributeResource, "/sketches/<int:sketch_id>/attribute/"),
    (ViewResource, "/sketches/<int:sketch_id>/views/<int:view_id>/"),
    (SearchTemplateListResource, "/searchtemplates/"),
    (SearchTemplateResource, "/searchtemplates/<int:searchtemplate_id>/"),
    (
        SearchTemplateParseResource,
        "/searchtemplates/<int:searchtemplate_id>/parse/",
    ),
    (UploadFileResource, "/upload/"),
    (TaskResource, "/tasks/"),
    (StoryListResource, "/sketches/<int:sketch_id>/stories/"),
    (StoryResource, "/sketches/<int:sketch_id>/stories/<int:story_id>/"),
    (QueryResource, "/sketches/<int:sketch_id>/explore/query/"),
    (CountEventsResource, "/sketches/<int:sketch_id>/count/"),
    (TimelineListResource, "/sketches/<int:sketch_id>/timelines/"),
    (
        TimelineResource,
        "/sketches/<int:sketch_id>/timelines/<int:timeline_id>/",
    ),
    (SearchIndexListResource, "/searchindices/"),
    (SearchIndexResource, "/searchindices/<int:searchindex_id>/"),
    (
        SessionResource,
        "/sketches/<int:sketch_id>/explore/sessions/<string:timeline_index>",
    ),
    (UserListResource, "/users/"),
    (GroupListResource, "/groups/"),
    (CollaboratorResource, "/sketches/<int:sketch_id>/collaborators/"),
    (VersionResource, "/version/"),
    (SigmaRuleListResource, "/sigmarules/"),
    (SigmaRuleResource, "/sigmarules/<string:rule_uuid>/"),
    (SigmaRuleByTextResource, "/sigmarules/text/"),
    (LoggedInUserResource, "/users/me/"),
    (UserSettingsResource, "/users/me/settings/"),
    (UserResource, "/users/<int:user_id>/"),
    (GraphListResource, "/sketches/<int:sketch_id>/graphs/"),
    (GraphResource, "/sketches/<int:sketch_id>/graphs/<int:graph_id>/"),
    (GraphPluginListResource, "/graphs/"),
    (GraphCacheResource, "/sketches/<int:sketch_id>/graph/"),
    (DataSourceListResource, "/sketches/<int:sketch_id>/datasource/"),
    (
        DataSourceResource,
        "/sketches/<int:sketch_id>/datasource/<int:datasource_id>/",
    ),
    (DataFinderResource, "/sketches/<int:sketch_id>/data/find/"),
    (TagMetadataResource, "/intelligence/tagmetadata/"),
    (ContextLinkConfigResource, "/contextlinks/"),
    (UnfurlResource, "/unfurl/"),
    (Nl2qResource, "/sketches/<int:sketch_id>/nl2q/"),
    (SystemSettingsResource, "/settings/"),
    # Scenario templates
    (ScenarioTemplateListResource, "/scenarios/"),
    # Scenarios
    (ScenarioListResource, "/sketches/<int:sketch_id>/scenarios/"),
    (ScenarioResource, "/sketches/<int:sketch_id>/scenarios/<int:scenario_id>/"),
    (
        ScenarioStatusResource,
        "/sketches/<int:sketch_id>/scenarios/<int:scenario_id>/status/",
    ),
    # Facets
    (
        FacetListResource,
        "/sketches/<int:sketch_id>/scenarios/<int:scenario_id>/facets/",
    ),
    # (FacetResource, "/sketches/<int:sketch_id>/facets/<int:facet_id>/"),
    # Questions
    (QuestionOrphanListResource, "/sketches/<int:sketch_id>/questions/"),
    (
        QuestionWithScenarioListResource,
        "/sketches/<int:sketch_id>/scenarios/<int:scenario_id>/questions/",
    ),
    (
        QuestionWithFacetListResource,
        "/sketches/<int:sketch_id>/scenarios/<int:scenario_id>/facets/<int:facet_id>/questions/",
    ),
    (QuestionTemplateListResource, "/questions/"),
    (QuestionListResource, "/sketches/<int:sketch_id>/questions/"),
    (QuestionResource, "/sketches/<int:sketch_id>/questions/<int:question_id>/"),
    (
        QuestionConclusionListResource,
        "/sketches/<int:sketch_id>/questions/<int:question_id>/conclusions/",
    ),
    (
        QuestionConclusionResource,
        "/sketches/<int:sketch_id>/questions/<int:question_id>/conclusions/<int:conclusion_id>/",
    ),
]
