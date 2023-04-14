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

    def __init__(self, name, description, user):
        """Initialize the Sketch object.

        Args:
            name: The name of the sketch
            description: Description of the sketch
            user: A user (instance of timesketch.models.user.User)
        """
        super().__init__()
        self.name = name
        self.description = description
        self.user = user

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
    color = Column(Unicode(6))
    user_id = Column(Integer, ForeignKey("user.id"))
    searchindex_id = Column(Integer, ForeignKey("searchindex.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    analysis = relationship("Analysis", backref="timeline", lazy="select")
    datasources = relationship("DataSource", backref="timeline", lazy="select")

    def __init__(
        self,
        name,
        user,
        sketch,
        searchindex,
        color=None,
        description=None,
    ):
        """Initialize the Timeline object.

        Args:
            name: The name of the timeline
            user: A user (instance of timesketch.models.user.User)
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            searchindex: A searchindex
                (instance of timesketch.models.sketch.SearchIndex)
            color: Color for the timeline in HEX as string (e.g. F1F1F1F1)
            description: The description for the timeline
        """
        super().__init__()
        self.name = name
        self.description = description

        if not color:
            color = random_color()

        self.color = color
        self.user = user
        self.sketch = sketch
        self.searchindex = searchindex


class SearchIndex(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the SearchIndex model."""

    name = Column(Unicode(255))
    description = Column(UnicodeText())
    index_name = Column(Unicode(255))
    user_id = Column(Integer, ForeignKey("user.id"))
    timelines = relationship("Timeline", backref="searchindex", lazy="dynamic")
    events = relationship("Event", backref="searchindex", lazy="dynamic")

    def __init__(self, name, description, index_name, user):
        """Initialize the SearchIndex object.

        Args:
            name: The name of the timeline
            description: The description for the timeline
            index_name: The name of the searchindex
            user: A user (instance of timesketch.models.user.User)
        """
        super().__init__()
        self.name = name
        self.description = description
        self.index_name = index_name
        self.user = user


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

    def __init__(
        self,
        name,
        sketch,
        user,
        description=None,
        searchtemplate=None,
        query_string=None,
        query_filter=None,
        query_dsl=None,
        searchtemplate_json=None,
    ):
        """Initialize the View object.

        Args:
            name: The name of the timeline
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            user: A user (instance of timesketch.models.user.User)
            description (str): Description of the view
            searchtemplate: Instance of timesketch.models.sketch.SearchTemplate
            query_string: The query string
            query_filter: The filter to apply (JSON format as string)
            query_dsl: A query DSL document (JSON format as string)
            searchtemplate_json: The search template used (JSON format as string)
        """
        super().__init__()
        self.name = name
        self.sketch = sketch
        self.user = user
        self.description = description
        self.searchtemplate = searchtemplate
        self.query_string = query_string
        self.query_filter = query_filter
        self.query_dsl = query_dsl
        self.searchtemplate_json = searchtemplate_json

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
    template_uuid = Column(Unicode(255), unique=True)
    template_json = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey("user.id"))
    views = relationship("View", backref="searchtemplate", lazy="select")

    def __init__(
        self,
        name,
        user=None,
        short_name=None,
        description=None,
        query_string=None,
        query_filter=None,
        query_dsl=None,
        template_uuid=None,
        template_json=None,
    ):
        """Initialize the Search Template object.

        Args:
            name: The human readable name of the template
            user: A user (instance of timesketch.models.user.User)
            short_name: The name of the template (snake case)
            description (str): Description of the search template
            query_string: The query string
            query_filter: The filter to apply (JSON format as string)
            query_dsl: A query DSL document (JSON format as string)
            template_uuid: UUID of the template
            template_json: Specification of the template (JSON format as string)
        """
        super().__init__()
        self.name = name
        self.user = user
        if not short_name:
            short_name = name.replace(" ", "_").lower()
        self.short_name = short_name
        self.description = description
        self.query_string = query_string
        if not query_filter:
            filter_template = {
                "exclude": [],
                "indices": "_all",
                "terminate_after": 40,
                "order": "asc",
                "size": "40",
            }
            query_filter = json.dumps(filter_template, ensure_ascii=False)
        self.query_filter = query_filter
        self.query_dsl = query_dsl
        if not template_uuid:
            template_uuid = str(uuid4())
        self.template_uuid = template_uuid
        self.template_json = template_json


class Event(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Event model."""

    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    searchindex_id = Column(Integer, ForeignKey("searchindex.id"))
    document_id = Column(Unicode(255))

    def __init__(self, sketch, searchindex, document_id):
        """Initialize the Event object.

        Args:
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            searchindex: A searchindex
                (instance of timesketch.models.sketch.SearchIndex)
            document_id = String with the datastore document ID
        """
        super().__init__()
        self.sketch = sketch
        self.searchindex = searchindex
        self.document_id = document_id


class Story(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Story model."""

    title = Column(Unicode(255))
    content = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey("user.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))

    def __init__(self, title, content, sketch, user):
        """Initialize the Story object.

        Args:
            title: The title of the story
            content: Content of the story
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            user: A user (instance of timesketch.models.user.User)
        """
        super().__init__()
        self.title = title
        self.content = content
        self.sketch = sketch
        self.user = user


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

    def __init__(
        self,
        name,
        description,
        agg_type,
        parameters,
        chart_type,
        user,
        sketch,
        view=None,
        aggregationgroup=None,
    ):
        """Initialize the Aggregation object.

        Args:
            name (str): Name of the aggregation
            description (str): Description of the aggregation
            agg_type (str): Aggregation plugin type
            parameters (str): JSON serialized dict with aggregation parameters
            chart_type (str): Chart plugin type
            user (User): The user who created the aggregation
            sketch (Sketch): The sketch that the aggregation is bound to
            view (View): Optional, the view that the aggregation is bound to
            aggregationgroup (AggregationGroup): Optional, an AggregationGroup
                that the aggregation is bound to.
        """
        super().__init__()
        self.name = name
        self.description = description
        self.agg_type = agg_type
        self.aggregationgroup = aggregationgroup
        self.parameters = parameters
        self.chart_type = chart_type
        self.user = user
        self.sketch = sketch
        self.view = view


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

    def __init__(
        self,
        name,
        description,
        user,
        sketch,
        aggregations=None,
        parameters="",
        orientation="",
        view=None,
    ):
        """Initialize the AggregationGroup object.

        Args:
            name (str): Name of the aggregation
            description (str): Description of the aggregation
            user (User): The user who created the aggregation
            sketch (Sketch): The sketch that the aggregation is bound to
            aggregations (Aggregation): List of aggregation objects.
            parameters (str): A JSON formatted dict with parameters for
                charting.
            orientation (str): Describes how charts should be joined together.
            view (View): Optional: The view that the aggregation is bound to
        """
        super().__init__()
        self.name = name
        self.description = description
        self.aggregations = aggregations or []
        self.parameters = parameters
        self.orientation = orientation
        self.user = user
        self.sketch = sketch
        self.view = view


class Analysis(LabelMixin, StatusMixin, CommentMixin, BaseModel):
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

    def __init__(
        self,
        name,
        description,
        analyzer_name,
        parameters,
        user,
        sketch,
        timeline=None,
        searchindex=None,
        result=None,
    ):
        """Initialize the Analysis object.

        Args:
            name (str): Name of the analysis
            description (str): Description of the analysis
            analyzer_name (str): Name of the analyzer
            parameters (str): JSON serialized dict with analyser parameters
            user (User): The user who created the aggregation
            sketch (Sketch): The sketch that the aggregation is bound to
            timeline (Timeline): Timeline the analysis was run on
            searchindex (SearchIndex): SearchIndex the analysis was run on
            result (str): Result report of the analysis
        """
        super().__init__()
        self.name = name
        self.description = description
        self.analyzer_name = analyzer_name
        self.parameters = parameters
        self.user = user
        self.sketch = sketch
        self.timeline = timeline
        self.searchindex = searchindex
        self.result = result
        self.log = ""


class AnalysisSession(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the analysis session model."""

    user_id = Column(Integer, ForeignKey("user.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    analyses = relationship("Analysis", backref="analysissession", lazy="select")

    def __init__(self, user, sketch):
        """Initialize the AnalysisSession object.

        Args:
            user (User): The user who created the aggregation
            sketch (Sketch): The sketch that the aggregation is bound to
        """
        super().__init__()
        self.user = user
        self.sketch = sketch


class Attribute(BaseModel):
    """Implements the attribute model."""

    user_id = Column(Integer, ForeignKey("user.id"))
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    name = Column(UnicodeText())
    ontology = Column(UnicodeText())
    values = relationship("AttributeValue", backref="attribute", lazy="select")

    def __init__(self, user, sketch, name, ontology):
        """Initialize the Attribute object.

        Args:
            user (User): The user who created the attribute
            sketch (Sketch): The sketch that the attribute is bound to
            name (str): the name of the attribute.
            ontology (str): The ontology of the value, The values that can
                be used are defined in timesketch/lib/ontology.py (ONTOLOGY).
        """
        super().__init__()
        self.user = user
        self.sketch = sketch
        self.name = name
        self.ontology = ontology


class AttributeValue(BaseModel):
    """Implements the attribute value model."""

    user_id = Column(Integer, ForeignKey("user.id"))
    attribute_id = Column(Integer, ForeignKey("attribute.id"))
    value = Column(UnicodeText())

    def __init__(self, user, attribute, value):
        """Initialize the Attribute value object.

        Args:
            user (User): The user who created the attribute value.
            attribute (Attribute): The attribute this value is bound to.
            value (str): a string that contains the value for the attribute.
                The ontology could influence how this will be cast when
                interpreted.
        """
        super().__init__()
        self.user = user
        self.attribute = attribute
        self.value = value


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

    def __init__(
        self,
        user,
        sketch,
        name,
        description=None,
        graph_config=None,
        graph_elements=None,
        graph_thumbnail=None,
        num_nodes=None,
        num_edges=None,
    ):
        """Initialize the Graph object.

        Args:
            user (User): The user who created the graph.
            sketch (Sketch): The sketch that the graph is bound to.
            name (str): Name of the graph.
            description (str): Description of the graph.
            graph_config (dict): Config used when generating the graph.
            graph_elements (str): Graph in json string format.
            graph_thumbnail (str): Image of graph in Base64 format.
            num_nodes (int): Number of nodes in the graph.
            num_edges (int): Number of edges in the graph.
        """
        super().__init__()
        self.user = user
        self.sketch = sketch
        self.name = name
        self.description = description
        self.graph_config = graph_config
        self.graph_elements = graph_elements
        self.graph_thumbnail = graph_thumbnail
        self.num_nodes = num_nodes
        self.num_edges = num_edges


class GraphCache(BaseModel):
    """Implements the graph cache model."""

    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    graph_plugin = Column(UnicodeText())
    graph_config = Column(UnicodeText())
    graph_elements = Column(UnicodeText())
    num_nodes = Column(Integer)
    num_edges = Column(Integer)

    def __init__(
        self,
        sketch,
        graph_plugin=None,
        graph_config=None,
        graph_elements=None,
        num_nodes=None,
        num_edges=None,
    ):
        """Initialize the GraphCache object.

        Args:
            sketch (Sketch): The sketch that the graph is bound to.
            graph_plugin (str): Name of the graph plugin that was used.
            graph_config (dict): Config used when generating the graph.
            graph_elements (str): Graph in json string format.
            num_nodes (int): Number of nodes in the graph.
            num_edges (int): Number of edges in the graph.
        """
        super().__init__()
        self.sketch = sketch
        self.graph_plugin = graph_plugin
        self.graph_config = graph_config
        self.graph_elements = graph_elements
        self.num_nodes = num_nodes
        self.num_edges = num_edges


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
    error_message = Column(UnicodeText())
    total_file_events = Column(BigInteger())

    def __init__(
        self,
        timeline,
        user,
        provider,
        context,
        file_on_disk,
        file_size,
        original_filename,
        data_label,
        error_message="",
        total_file_events=0,
    ):  # pylint: disable=too-many-arguments
        """Initialize the DataSource object.

        Args:
            timeline (Timeline): Timeline that this datasource is part of.
            user (User): The user who imported the data.
            provider (str): Name of the application that collected the data.
            context (str): Context on how the data was collected.
            file_on_disk (str): Path to uploaded file.
            file_size (int): Size on disk for uploaded file.
            original_filename (str): Original filename for uploaded file.
            data_label (str): Data label for the uploaded data.
            error_message (str): Optional error message in case the data source
                did not successfully import.
        """
        super().__init__()
        self.timeline = timeline
        self.user = user
        self.provider = provider
        self.context = context
        self.file_on_disk = file_on_disk
        self.file_size = file_size
        self.original_filename = original_filename
        self.data_label = data_label
        self.error_message = error_message
        self.total_file_events = total_file_events

    def set_total_file_events(self, total_file_events):
        self.total_file_events = total_file_events
        db_session.commit()

    def set_error_message(self, error_message):
        self.error_message = error_message
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

    def __init__(
        self,
        user,
        sketch,
        description=None,
        query_string=None,
        query_filter=None,
        query_dsl=None,
        parent=None,
    ):
        """ "Initialize the SearchHistory object

        Args:
            user (User): The user who owns the search history.
            sketch (Sketch): The sketch for the search history.
            description (str): Description for the search history entry.
            query_string (str): The query string.
            query_filter (str): The filter to apply (JSON format as string).
            query_dsl (str): A query DSL document (JSON format as string).
            parent (SearchHistory): Reference to parent search history entry.
        """
        self.user = user
        self.sketch = sketch
        self.description = description
        self.query_string = query_string
        self.query_filter = query_filter
        self.query_dsl = query_dsl
        self.parent = parent

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
    spec_json = Column(UnicodeText())
    sketch_id = Column(Integer, ForeignKey("sketch.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    facets = relationship("Facet", backref="scenario", lazy="select")

    def __init__(
        self,
        name,
        display_name,
        dfiq_identifier,
        sketch,
        user,
        spec_json,
        description=None,
    ):
        """Initialize the Scenario object.

        Args:
            name (str): The name of the scenario
            display_name (str): The display name of the scenario
            dfiq_identifier (str): DFIQ identifier for scenario
            sketch (timesketch.models.sketch.Sketch): A sketch
            user (timesketch.models.user.User): A user
            spec_json (str): Scenario specification from YAML
            description (str): Description of the scenario
        """
        super().__init__()
        self.name = name
        self.display_name = display_name
        self.dfiq_identifier = dfiq_identifier
        self.sketch = sketch
        self.user = user
        self.spec_json = spec_json
        self.description = description


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

    def __init__(self, start_time, end_time, facet, user=None, description=None):
        """Initialize the InvestigationTimeFrame object.

        Args:
            start_time (datetime): Timezone-aware UTC datetime object.
            end_time (datetime): Timezone-aware UTC datetime object.
            facet (Facet): Facet for this time frame
            description (str): Description of the timeframe (optional)
        """
        super().__init__()
        self.start_time = start_time
        self.end_time = end_time
        self.facet = facet
        self.user = user
        self.description = description


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

    def __init__(self, conclusion, user, facet, automated=False):
        """Initialize the InvestigationConclusion object.

        Args:
            conclusion (str): The conclusion of the investigation
            user (User): A user
            facet (Facet): Facet for this conclusion
            automated (bool): Indicate if conclusion was automated
        """
        super().__init__()
        self.conclusion = conclusion
        self.user = user
        self.facet = facet
        self.automated = automated


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
    spec_json = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey("user.id"))
    scenario_id = Column(Integer, ForeignKey("scenario.id"))
    timeframes = relationship("FacetTimeFrame", backref="facet", lazy="select")
    timelines = relationship("Timeline", secondary=facet_timeline_association_table)
    questions = relationship("InvestigativeQuestion", backref="facet", lazy="select")
    conclusions = relationship("FacetConclusion", backref="facet", lazy="select")

    def __init__(
        self, name, display_name, dfiq_identifier, user, spec_json, description=None
    ):
        """Initialize the Facet object.

        Args:
            name (str): The name of the investigation
            display_name (str): The display name of the investigation
            dfiq_identifier (str): DFIQ identifier for facet
            user (User): A userinvestigationconclusion
            scenario (Scenario): The Scenario this investigation belongs to
            spec_json (str): Investigation specification
            description (str): Description of the investigation
        """
        super().__init__()
        self.name = name
        self.display_name = display_name
        self.dfiq_identifier = dfiq_identifier
        self.user = user
        self.spec_json = spec_json
        self.description = description


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

    def __init__(self, user, investigativequestion, conclusion=None, automated=False):
        """Initialize the QuestionConclusion object.

        Args:
            conclusion (str): The conclusion of the question
            user (timesketch.models.user.User): A user
            investigativequestion (InvestigativeQuestion): A question
            automated (bool): Indicate if conclusion was automated
        """
        super().__init__()
        self.user = user
        self.investigativequestion = investigativequestion
        self.conclusion = conclusion
        self.automated = automated


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
    user_id = Column(Integer, ForeignKey("user.id"))
    spec_json = Column(UnicodeText())
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

    def __init__(
        self, name, display_name, dfiq_identifier, user, spec_json, description=None
    ):
        """Initialize the InvestigativeQuestion object.

        Args:
            name (str): The name of the question
            display_name (str): The display name of the question
            dfiq_identifier (str): DFIQ identifier for question
            user (timesketch.models.user.User): A user
            spec_json (str): Question specification
            description (str): Description of the question
        """
        super().__init__()
        self.name = name
        self.display_name = display_name
        self.dfiq_identifier = dfiq_identifier
        self.user = user
        self.spec_json = spec_json
        self.description = description


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

    def __init__(
        self, name, display_name, dfiq_identifier, user, spec_json, description=None
    ):
        """Initialize the InvestigativeQuestion object.

        Args:
            name (str): The name of the question
            display_name (str): The display name of the question
            dfiq_identifier (str): DFIQ identifier for approach
            user (timesketch.models.user.User): A user
            spec_json (str): Question specification
            description (str): Description of the question
        """
        super().__init__()
        self.name = name
        self.display_name = display_name
        self.dfiq_identifier = dfiq_identifier
        self.user = user
        self.spec_json = spec_json
        self.description = description
