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

from .resources.aggregation import (
    AggregationExploreResource,
    AggregationGroupListResource,
    AggregationGroupResource,
    AggregationInfoResource,
    AggregationListResource,
    AggregationResource,
)
from .resources.analysis import (
    AnalysisResource,
    AnalyzerRunResource,
    AnalyzerSessionActiveListResource,
    AnalyzerSessionResource,
)
from .resources.archive import SketchArchiveResource
from .resources.attribute import AttributeResource
from .resources.contextlinks import ContextLinkConfigResource
from .resources.datafinder import DataFinderResource
from .resources.datasource import DataSourceListResource, DataSourceResource
from .resources.event import (
    CountEventsResource,
    EventAddAttributeResource,
    EventAnnotationResource,
    EventCreateResource,
    EventResource,
    EventTaggingResource,
    EventUnTagResource,
    MarkEventsWithTimelineIdentifier,
)
from .resources.explore import (
    ExploreResource,
    QueryResource,
    SearchHistoryResource,
    SearchHistoryTreeResource,
)
from .resources.graph import (
    GraphCacheResource,
    GraphListResource,
    GraphPluginListResource,
    GraphResource,
)
from .resources.information import VersionResource
from .resources.intelligence import TagMetadataResource
from .resources.llm_summarize import LLMSummarizeResource
from .resources.nl2q import Nl2qResource
from .resources.scenarios import (
    FacetListResource,
    QuestionConclusionListResource,
    QuestionConclusionResource,
    QuestionListResource,
    QuestionOrphanListResource,
    QuestionResource,
    QuestionTemplateListResource,
    QuestionWithFacetListResource,
    QuestionWithScenarioListResource,
    ScenarioListResource,
    ScenarioResource,
    ScenarioStatusResource,
    ScenarioTemplateListResource,
)
from .resources.searchindex import SearchIndexListResource, SearchIndexResource
from .resources.searchtemplate import (
    SearchTemplateListResource,
    SearchTemplateParseResource,
    SearchTemplateResource,
)
from .resources.session import SessionResource
from .resources.settings import SystemSettingsResource
from .resources.sigma import (
    SigmaRuleByTextResource,
    SigmaRuleListResource,
    SigmaRuleResource,
)
from .resources.sketch import SketchListResource, SketchResource
from .resources.story import StoryListResource, StoryResource
from .resources.task import TaskResource
from .resources.timeline import (
    TimelineFieldsResource,
    TimelineListResource,
    TimelineResource,
)
from .resources.unfurl import UnfurlResource
from .resources.upload import UploadFileResource
from .resources.user import (
    CollaboratorResource,
    GroupListResource,
    LoggedInUserResource,
    UserListResource,
    UserResource,
    UserSettingsResource,
)
from .resources.view import ViewListResource, ViewResource

# Disable error for long line. Readability is more important than line
# length in this case.

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
    (
        TimelineFieldsResource,
        "/sketches/<int:sketch_id>/timelines/<int:timeline_id>/fields/",
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
    (LLMSummarizeResource, "/sketches/<int:sketch_id>/events/summary/"),
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
