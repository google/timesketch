# Copyright 2015 Google Inc. All rights reserved.
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
"""This module implements the models for the Timesketch core system."""

from __future__ import unicode_literals

import json
import logging
from uuid import uuid4

from flask import current_app
from flask import url_for

from sqlalchemy import Table
from sqlalchemy import BigInteger
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy import Boolean
from sqlalchemy import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.orm.collections import attribute_mapped_collection

from timesketch.models import BaseModel
from timesketch.models.acl import AccessControlMixin
from timesketch.models.annotations import LabelMixin
from timesketch.models.annotations import CommentMixin
from timesketch.models.annotations import StatusMixin
from timesketch.models.annotations import GenericAttributeMixin
from timesketch.lib.utils import random_color
from timesketch.models import db_session


logger = logging.getLogger("timesketch.sketch")


class Sketch(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Sketch model.

    A Sketch is the collaborative entity in Timesketch. It contains one or more
    timelines that can be grouped and queried on.
    """

    name = Column(Unicode(255))
    description = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey("user.id"))
    timelines = relationship("Timeline", backref="sketch", lazy="select")
    views = relationship("View", backref="sketch", lazy="select")
    events = relationship("Event", backref="sketch", lazy="select")
    stories = relationship("Story", backref="sketch", lazy="select")
    aggregations = relationship("Aggregation", backref="sketch", lazy="select")
    attributes = relationship("Attribute", backref="sketch", lazy="select")
    graphs = relationship("Graph", backref="sketch", lazy="select")
    graphcaches = relationship("GraphCache", backref="sketch", lazy="select")
    aggregationgroups = relationship(
        "AggregationGroup", backref="sketch", lazy="select"
    )
    analysis = relationship("Analysis", backref="sketch", lazy="select")
    analysissessions = relationship("AnalysisSession", backref="sketch", lazy="select")
    searchhistories = relationship("SearchHistory", backref="sketch", lazy="dynamic")
    scenarios = relationship("Scenario", backref="sketch", lazy="dynamic")
    facets = relationship("Facet", backref="sketch", lazy="dynamic")
    questions = relationship("InvestigativeQuestion", backref="sketch", lazy="dynamic")

    @property
    def get_named_aggregations(self):
        """Get named aggregations that don't belong to a group.

        Get named aggregations, i.e. only aggregations that have a name and
        are not part of a group.
        """
        return [
            agg
            for agg in self.aggregations
            if agg.name != "" and not agg.aggregationgroup
        ]

    @property
    def get_named_views(self):
        """Get named views.

        Get named views, i.e. only views that has a name. Views without names
        are used as user state views and should not be visible in the UI.
        """
        views = [
            view
            for view in self.views
            if view.get_status.status != "deleted" and view.name != ""
        ]
        return views

    @property
    def external_url(self):
        """Get external URL for the sketch.

        E.g: https://localhost/sketch/42/

        Returns:
            Full URL to the sketch as string.
        """
        url_host = current_app.config.get("EXTERNAL_HOST_URL", "https://localhost")
        url_path = url_for("sketch_views.overview", sketch_id=self.id)
        return url_host + url_path

    def get_view_urls(self):
        """Get external URL for all views in the sketch.

        Returns:
            Dictionary with url as key and view name as value.
        """

        views = {}
        for view in self.get_named_views:
            url_host = current_app.config.get("EXTERNAL_HOST_URL", "https://localhost")
            url_path = url_for(
                "sketch_views.explore", sketch_id=self.id, view_id=view.id
            )
            url = url_host + url_path
            views[url] = view.name
        return views

    @property
    def active_timelines(self):
        """List timelines that are ready for analysis.

        Returns:
            List of instances of timesketch.models.sketch.Timeline
        """
        _timelines = []
        for timeline in self.timelines:
            timeline_status = timeline.get_status.status
            index_status = timeline.searchindex.get_status.status
            if (timeline_status or index_status) in ("processing", "fail", "archived"):
                continue
            _timelines.append(timeline)
        return _timelines

    def get_active_analysis_sessions(self):
        """List active analysis sessions.

        Returns:
            List of instances of timesketch.models.sketch.AnalysisSession
        """
        active_sessions = []
        for session in self.analysissessions:
            for analysis in session.analyses:
                if analysis.get_status.status in ("PENDING", "STARTED"):
                    active_sessions.append(session)
                    # Break early on first running analysis as this is enough
                    # to mark the session as active.
                    break
        return active_sessions

    @property
    def get_search_templates(self):
        """Get search templates."""
        return SearchTemplate.query.all()

    def get_user_view(self, user):
        """Get view for user, i.e. view with the state for the user/sketch.

        Args:
            user: User (instance of timesketch.models.user.User)

        Returns:
            view: Instance of timesketch.models.sketch.View
        """
        view = (
            View.query.filter(
                View.user == user, View.name == "", View.sketch_id == self.id
            )
            .order_by(View.created_at.desc())
            .first()
        )
        return view


class Timeline(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Timeline model."""

    name = Column(Unicode(255))
    description = Column(UnicodeText())
    color = Column(Unicode(6), default=random_color())
    user_id = Column(Integer, ForeignKey("user.id"))
    searchindex_id = Column(Integer, ForeignKey("searchindex.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    analysis = relationship("Analysis", backref="timeline", lazy="select")
    datasources = relationship("DataSource", backref="timeline", lazy="select")


class SearchIndex(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the SearchIndex model."""

    name = Column(Unicode(255))
    description = Column(UnicodeText())
    index_name = Column(Unicode(255))
    user_id = Column(Integer, ForeignKey("user.id"))
    timelines = relationship("Timeline", backref="searchindex", lazy="dynamic")
    events = relationship("Event", backref="searchindex", lazy="dynamic")


class View(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the View model."""

    name = Column(Unicode(255))
    description = Column(UnicodeText())
    query_string = Column(UnicodeText())
    query_filter = Column(UnicodeText())
    query_dsl = Column(UnicodeText())
    searchtemplate_json = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey("user.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    searchtemplate_id = Column(Integer, ForeignKey("searchtemplate.id"))
    aggregations = relationship("Aggregation", backref="view", lazy="select")
    aggregationgroups = relationship("AggregationGroup", backref="view", lazy="select")

    def validate_filter(self, query_filter=None):
        """Validate the Query Filter.

        Make sure that we have all expected attributes in the query filter
        json string. The filter dictionary evolves over time and this function
        is used to update all filters.

        Args:
            query_filter: The query filter (JSON format or dictionary)

        Returns:
            query_filter: Query filter dictionary serialized to JSON

        """
        DEFAULT_FROM = 0
        DEFAULT_SIZE = 40  # Number of resulting documents to return
        DEFAULT_LIMIT = DEFAULT_SIZE  # Number of resulting documents to return
        DEFAULT_VALUES = {
            "from": DEFAULT_FROM,
            "size": DEFAULT_SIZE,
            "terminate_after": DEFAULT_LIMIT,
            "indices": [],
            "exclude": [],
            "order": "asc",
            "chips": [],
        }
        # If not provided, get the saved filter from the view
        if not query_filter:
            query_filter = self.query_filter

        # Make sure we have the filter as a dictionary
        if not isinstance(query_filter, dict):
            filter_dict = json.loads(query_filter)
        else:
            filter_dict = query_filter

        # Get all missing attributes and set them to their default value
        missing_attributes = list(set(DEFAULT_VALUES.keys()) - set(filter_dict.keys()))
        for key in missing_attributes:
            filter_dict[key] = DEFAULT_VALUES[key]

        return json.dumps(filter_dict, ensure_ascii=False)


class SearchTemplate(
    AccessControlMixin, LabelMixin, StatusMixin, CommentMixin, BaseModel
):
    """Implements the Search Template model."""

    name = Column(Unicode(255))
    short_name = Column(Unicode(255))
    description = Column(UnicodeText())
    query_string = Column(UnicodeText())
    query_filter = Column(UnicodeText())
    query_dsl = Column(UnicodeText())
    template_uuid = Column(Unicode(255), unique=True, default=str(uuid4()))
    template_json = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey("user.id"))
    views = relationship("View", backref="searchtemplate", lazy="select")


class Event(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Event model."""

    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    searchindex_id = Column(Integer, ForeignKey("searchindex.id"))
    document_id = Column(Unicode(255))


class Story(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Story model."""

    title = Column(Unicode(255))
    content = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey("user.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))


class Aggregation(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Aggregation model."""

    name = Column(Unicode(255))
    description = Column(UnicodeText())
    agg_type = Column(Unicode(255))
    parameters = Column(UnicodeText())
    chart_type = Column(Unicode(255))
    user_id = Column(Integer, ForeignKey("user.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    view_id = Column(Integer, ForeignKey("view.id"))
    aggregationgroup_id = Column(Integer, ForeignKey("aggregationgroup.id"))


class AggregationGroup(
    AccessControlMixin, LabelMixin, StatusMixin, CommentMixin, BaseModel
):
    """Implements the Aggregation Group model."""

    name = Column(Unicode(255))
    description = Column(UnicodeText())
    aggregations = relationship(
        "Aggregation", backref="aggregationgroup", lazy="select"
    )
    parameters = Column(UnicodeText())
    orientation = Column(Unicode(40))
    user_id = Column(Integer, ForeignKey("user.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    view_id = Column(Integer, ForeignKey("view.id"))


class Analysis(GenericAttributeMixin, LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the analysis model."""

    name = Column(Unicode(255))
    description = Column(UnicodeText())
    analyzer_name = Column(Unicode(255))
    parameters = Column(UnicodeText())
    result = Column(UnicodeText())
    log = Column(UnicodeText())
    analysissession_id = Column(Integer, ForeignKey("analysissession.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    timeline_id = Column(Integer, ForeignKey("timeline.id"))
    searchindex_id = Column(Integer, ForeignKey("searchindex.id"))


class AnalysisSession(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the analysis session model."""

    user_id = Column(Integer, ForeignKey("user.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    analyses = relationship("Analysis", backref="analysissession", lazy="select")


class Attribute(BaseModel):
    """Implements the attribute model."""

    user_id = Column(Integer, ForeignKey("user.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    name = Column(UnicodeText())
    ontology = Column(UnicodeText())
    values = relationship("AttributeValue", backref="attribute", lazy="select")


class AttributeValue(BaseModel):
    """Implements the attribute value model."""

    user_id = Column(Integer, ForeignKey("user.id"))
    attribute_id = Column(Integer, ForeignKey("attribute.id"))
    value = Column(UnicodeText())


class Graph(LabelMixin, CommentMixin, BaseModel):
    """Implements the graph model."""

    user_id = Column(Integer, ForeignKey("user.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    name = Column(UnicodeText())
    description = Column(UnicodeText())
    graph_config = Column(UnicodeText())
    graph_elements = Column(UnicodeText())
    graph_thumbnail = Column(UnicodeText())
    num_nodes = Column(Integer)
    num_edges = Column(Integer)


class GraphCache(BaseModel):
    """Implements the graph cache model."""

    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    graph_plugin = Column(UnicodeText())
    graph_config = Column(UnicodeText())
    graph_elements = Column(UnicodeText())
    num_nodes = Column(Integer)
    num_edges = Column(Integer)


class DataSource(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the datasource model."""

    timeline_id = Column(Integer, ForeignKey("timeline.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    provider = Column(UnicodeText())
    context = Column(UnicodeText())
    file_on_disk = Column(UnicodeText())
    file_size = Column(BigInteger())
    original_filename = Column(UnicodeText())
    data_label = Column(UnicodeText())
    error_message = Column(UnicodeText(), default="")
    total_file_events = Column(BigInteger(), default=0)

    def set_total_file_events(self, total_file_events):
        self.total_file_events = total_file_events
        db_session.add(self)
        db_session.commit()

    def set_error_message(self, error_message):
        self.error_message = error_message
        db_session.add(self)
        db_session.commit()

    @property
    def get_total_file_events(self):
        return self.total_file_events

    @property
    def get_file_on_disk(self):
        return self.file_on_disk

    @property
    def get_status(self):
        return self.status[0].status


# Association table for the many-to-many relationship between SearchHistory
# and Event.
association_table = Table(
    "searchhistory_event",
    BaseModel.metadata,
    Column("searchhistory_id", Integer, ForeignKey("searchhistory.id")),
    Column("event_id", Integer, ForeignKey("event.id")),
)


class SearchHistory(LabelMixin, BaseModel):
    """Implements the SearchHistory model."""

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey(id))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    scenario_id = Column(Integer, ForeignKey("scenario.id"))
    facet_id = Column(Integer, ForeignKey("facet.id"))
    question_id = Column(Integer, ForeignKey("investigativequestion.id"))
    approach_id = Column(Integer, ForeignKey("investigativequestionapproach.id"))
    description = Column(UnicodeText())
    query_string = Column(UnicodeText())
    query_filter = Column(UnicodeText())
    query_dsl = Column(UnicodeText())
    query_result_count = Column(BigInteger())
    query_time = Column(BigInteger())
    events = relationship("Event", secondary=association_table)
    children = relationship(
        "SearchHistory",
        # Cascade deletions
        cascade="all, delete-orphan",
        backref=backref("parent", remote_side=id),
        collection_class=attribute_mapped_collection("id"),
    )

    @staticmethod
    def build_node_dict(node_dict, node):
        node_dict["id"] = node.id
        node_dict["description"] = node.description
        node_dict["query_result_count"] = node.query_result_count
        node_dict["query_time"] = node.query_time
        node_dict["labels"] = node.get_labels
        node_dict["created_at"] = node.created_at
        node_dict["parent"] = node.parent_id
        node_dict["query_string"] = node.query_string
        node_dict["query_filter"] = node.query_filter
        node_dict["query_dsl"] = node.query_dsl
        node_dict["scenario"] = node.scenario_id
        node_dict["facet"] = node.facet_id
        node_dict["question"] = node.question_id
        node_dict["children"] = []
        return node_dict

    def build_tree(self, node, node_dict, recurse=True):
        """Recursive function to generate full search history tree.

        Args:
            node (SearchHistory): SearchHistory object as root node.
            node_dict (dict): Dictionary to use for recursion.
            recurse (bool): If the function should recurse on all children.

        Returns:
            Dictionary with a SearchHistory tree.
        """
        if not isinstance(node_dict, dict):
            raise ValueError("node_dict must be a dictionary")

        node_dict = self.build_node_dict(node_dict, node)
        children = node.children.values()
        if children and recurse:
            for child in children:
                child_dict = {}
                child.build_tree(child, child_dict)
                node_dict["children"].append(child_dict)
        else:
            return node_dict

        return node_dict


class Scenario(LabelMixin, StatusMixin, CommentMixin, GenericAttributeMixin, BaseModel):
    """Implements the Scenario model.

    A Timesketch scenario describes the type of the sketch. A scenario has
    one or many facets (investigations).

    A scenario is created from a YAML specification that is provided by the
    system. This YAML file is used to create and bootstrap sketches.
    """

    name = Column(UnicodeText())
    display_name = Column(UnicodeText())
    description = Column(UnicodeText())
    summary = Column(UnicodeText())
    dfiq_identifier = Column(UnicodeText())
    uuid = Column(UnicodeText())
    spec_json = Column(UnicodeText())
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    facets = relationship("Facet", backref="scenario", lazy="select")
    questions = relationship("InvestigativeQuestion", backref="scenario", lazy="select")
    search_histories = relationship("SearchHistory", backref="scenario", lazy="select")


class FacetTimeFrame(BaseModel):
    """Implements the FacetTimeFrame model.

    A timeframe is used to set the scope for the facet. This information
    is used when automatically generate queries and other helper functions.
    """

    start_time = Column(TIMESTAMP(timezone=True))
    end_time = Column(TIMESTAMP(timezone=True))
    description = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey("user.id"))
    facet_id = Column(Integer, ForeignKey("facet.id"))


# Association tables for the many-to-many relationship for a conclusion.
facetconclusion_story_association_table = Table(
    "facetconclusion_story",
    BaseModel.metadata,
    Column("facetconclusion_id", Integer, ForeignKey("facetconclusion.id")),
    Column("story_id", Integer, ForeignKey("story.id")),
)

facetconclusion_view_association_table = Table(
    "facetconclusion_view",
    BaseModel.metadata,
    Column("facetconclusion_id", Integer, ForeignKey("facetconclusion.id")),
    Column("view_id", Integer, ForeignKey("view.id")),
)

facetconclusion_graph_association_table = Table(
    "facetconclusion_graph",
    BaseModel.metadata,
    Column("facetconclusion_id", Integer, ForeignKey("facetconclusion.id")),
    Column("graph_id", Integer, ForeignKey("graph.id")),
)

facetconclusion_aggregation_association_table = Table(
    "facetconclusion_aggregation",
    BaseModel.metadata,
    Column("facetconclusion_id", Integer, ForeignKey("facetconclusion.id")),
    Column("aggregation_id", Integer, ForeignKey("aggregation.id")),
)


class FacetConclusion(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the FacetConclusion model.

    A conslusion is the result of an investigation (facet). It can be created
    both by a human as well as automated by the system.

    Together with a conclusion there can be evidence and pointers to supportive
    resources such as saved searches, graphs, aggregations and stories.
    """

    conclusion = Column(UnicodeText())
    automated = Column(Boolean(), default=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    facet_id = Column(Integer, ForeignKey("facet.id"))
    stories = relationship("Story", secondary=facetconclusion_story_association_table)
    saved_searches = relationship(
        "View", secondary=facetconclusion_view_association_table
    )
    saved_graphs = relationship(
        "Graph", secondary=facetconclusion_graph_association_table
    )
    saved_aggregations = relationship(
        "Aggregation", secondary=facetconclusion_aggregation_association_table
    )


# Association table for the many-to-many relationship for timelines in an
# investigation.
facet_timeline_association_table = Table(
    "facet_timeline",
    BaseModel.metadata,
    Column("facet_id", Integer, ForeignKey("facet.id")),
    Column("timeline_id", Integer, ForeignKey("timeline.id")),
)


class Facet(LabelMixin, StatusMixin, CommentMixin, GenericAttributeMixin, BaseModel):
    """Implements the Facet model.

    A facet is a collection of investigative questions.

    In order to help the user as well as aid in automation it is
    possible to set the scope for the facet. The scope consist of
    timeframes of interest, timelines and supplied parameters (key/value).
    """

    name = Column(UnicodeText())
    display_name = Column(UnicodeText())
    description = Column(UnicodeText())
    dfiq_identifier = Column(UnicodeText())
    uuid = Column(UnicodeText())
    spec_json = Column(UnicodeText())
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    scenario_id = Column(Integer, ForeignKey("scenario.id"))
    timeframes = relationship("FacetTimeFrame", backref="facet", lazy="select")
    timelines = relationship("Timeline", secondary=facet_timeline_association_table)
    questions = relationship("InvestigativeQuestion", backref="facet", lazy="select")
    conclusions = relationship("FacetConclusion", backref="facet", lazy="select")
    search_histories = relationship("SearchHistory", backref="facet", lazy="select")


# Association tables for the many-to-many relationship for a question conclusion.
questionconclusion_story_association_table = Table(
    "investigativequestionconclusion_story",
    BaseModel.metadata,
    Column(
        "investigativequestionconclusion_id",
        Integer,
        ForeignKey("investigativequestionconclusion.id"),
    ),
    Column("story_id", Integer, ForeignKey("story.id")),
)

questionconclusion_view_association_table = Table(
    "investigativequestionconclusion_view",
    BaseModel.metadata,
    Column(
        "investigativequestionconclusion_id",
        Integer,
        ForeignKey("investigativequestionconclusion.id"),
    ),
    Column("view_id", Integer, ForeignKey("view.id")),
)

questionconclusion_graph_association_table = Table(
    "investigativequestionconclusion_graph",
    BaseModel.metadata,
    Column(
        "investigativequestionconclusion_id",
        Integer,
        ForeignKey("investigativequestionconclusion.id"),
    ),
    Column("graph_id", Integer, ForeignKey("graph.id")),
)

questionconclusion_aggregation_association_table = Table(
    "investigativequestionconclusion_aggregation",
    BaseModel.metadata,
    Column(
        "investigativequestionconclusion_id",
        Integer,
        ForeignKey("investigativequestionconclusion.id"),
    ),
    Column("aggregation_id", Integer, ForeignKey("aggregation.id")),
)


class InvestigativeQuestionConclusion(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the InvestigativeQuestionConclusion model.

    A conslusion is the result of a investigative question. It can be created
    both by a human as well as automated by the system.

    Together with a conclusion there can be evidence and pointers to supportive
    resources such as saved searches, graphs, aggregations and stories.
    """

    conclusion = Column(UnicodeText())
    automated = Column(Boolean(), default=False)
    user_id = Column(Integer, ForeignKey("user.id"))
    investigativequestion_id = Column(Integer, ForeignKey("investigativequestion.id"))
    stories = relationship(
        "Story", secondary=questionconclusion_story_association_table
    )
    saved_searches = relationship(
        "View", secondary=questionconclusion_view_association_table
    )
    saved_graphs = relationship(
        "Graph", secondary=questionconclusion_graph_association_table
    )
    saved_aggregations = relationship(
        "Aggregation", secondary=questionconclusion_aggregation_association_table
    )


class InvestigativeQuestion(
    LabelMixin, StatusMixin, CommentMixin, GenericAttributeMixin, BaseModel
):
    """Implements the InvestigativeQuestion model.

    An Investigative Question is the smallest component of an investigation.
    """

    name = Column(UnicodeText())
    display_name = Column(UnicodeText())
    description = Column(UnicodeText())
    dfiq_identifier = Column(UnicodeText())
    uuid = Column(UnicodeText())
    spec_json = Column(UnicodeText())
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    scenario_id = Column(Integer, ForeignKey("scenario.id"))
    facet_id = Column(Integer, ForeignKey("facet.id"))
    approaches = relationship(
        "InvestigativeQuestionApproach",
        backref="investigativequestion",
        lazy="select",
    )
    conclusions = relationship(
        "InvestigativeQuestionConclusion",
        backref="investigativequestion",
        lazy="select",
    )
    search_histories = relationship(
        "SearchHistory", backref="investigativequestion", lazy="select"
    )


# Association tables for the many-to-many relationships for an approach.
approach_searchtemplate_association_table = Table(
    "investigativequestionapproach_searchtemplate",
    BaseModel.metadata,
    Column(
        "investigativequestionapproach_id",
        Integer,
        ForeignKey("investigativequestionapproach.id"),
    ),
    Column("searchtemplate_id", Integer, ForeignKey("searchtemplate.id")),
)

approach_sigmarule_association_table = Table(
    "investigativequestionapproach_sigmarule",
    BaseModel.metadata,
    Column(
        "investigativequestionapproach_id",
        Integer,
        ForeignKey("investigativequestionapproach.id"),
    ),
    Column("sigmarule_id", Integer, ForeignKey("sigmarule.id")),
)


class InvestigativeQuestionApproach(
    LabelMixin, StatusMixin, CommentMixin, GenericAttributeMixin, BaseModel
):
    """Implements the Investigative Question Approach model.

    An approach is the smallest component of an investigation.
    """

    name = Column(UnicodeText())
    display_name = Column(UnicodeText())
    description = Column(UnicodeText())
    dfiq_identifier = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey("user.id"))
    spec_json = Column(UnicodeText())
    investigativequestion_id = Column(Integer, ForeignKey("investigativequestion.id"))
    search_templates = relationship(
        "SearchTemplate", secondary=approach_searchtemplate_association_table
    )
    sigma_rules = relationship(
        "SigmaRule", secondary=approach_sigmarule_association_table
    )
    search_histories = relationship(
        "SearchHistory", backref="investigativequestionapproach", lazy="select"
    )
