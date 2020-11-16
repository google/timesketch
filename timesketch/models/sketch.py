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

from flask import current_app
from flask import url_for

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText
from sqlalchemy.orm import relationship

from timesketch.models import BaseModel
from timesketch.models.acl import AccessControlMixin
from timesketch.models.annotations import LabelMixin
from timesketch.models.annotations import CommentMixin
from timesketch.models.annotations import StatusMixin
from timesketch.lib.utils import random_color


class Sketch(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin,
             BaseModel):
    """Implements the Sketch model.

    A Sketch is the collaborative entity in Timesketch. It contains one or more
    timelines that can be grouped and queried on.
    """
    name = Column(Unicode(255))
    description = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    timelines = relationship('Timeline', backref='sketch', lazy='select')
    views = relationship('View', backref='sketch', lazy='select')
    events = relationship('Event', backref='sketch', lazy='select')
    stories = relationship('Story', backref='sketch', lazy='select')
    aggregations = relationship('Aggregation', backref='sketch', lazy='select')
    attributes = relationship('Attribute', backref='sketch', lazy='select')
    graphs = relationship('Graph', backref='sketch', lazy='select')
    graphcaches = relationship('GraphCache', backref='sketch', lazy='select')
    aggregationgroups = relationship(
        'AggregationGroup', backref='sketch', lazy='select')
    analysis = relationship('Analysis', backref='sketch', lazy='select')

    def __init__(self, name, description, user):
        """Initialize the Sketch object.

        Args:
            name: The name of the sketch
            description: Description of the sketch
            user: A user (instance of timesketch.models.user.User)
        """
        super(Sketch, self).__init__()
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
            agg for agg in self.aggregations
            if agg.name != '' and not agg.aggregationgroup
        ]

    @property
    def get_named_views(self):
        """Get named views.

        Get named views, i.e. only views that has a name. Views without names
        are used as user state views and should not be visible in the UI.
        """
        views = [
            view for view in self.views
            if view.get_status.status != 'deleted' and view.name != ''
        ]
        return views

    @property
    def external_url(self):
        """Get external URL for the sketch.

        E.g: https://localhost/sketch/42/

        Returns:
            Full URL to the sketch as string.
        """
        url_host = current_app.config.get(
            'EXTERNAL_HOST_URL', 'https://localhost')
        url_path = url_for('sketch_views.overview', sketch_id=self.id)
        return url_host + url_path

    def get_view_urls(self):
        """Get external URL for all views in the sketch.

        Returns:
            Dictionary with url as key and view name as value.
        """

        views = {}
        for view in self.get_named_views:
            url_host = current_app.config.get(
                'EXTERNAL_HOST_URL', 'https://localhost')
            url_path = url_for(
                'sketch_views.explore', sketch_id=self.id, view_id=view.id)
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
            if (timeline_status or index_status) in (
                    'processing', 'fail', 'archived'):
                continue
            _timelines.append(timeline)
        return _timelines

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
        view = View.query.filter(View.user == user, View.name == '',
                                 View.sketch_id == self.id).order_by(
                                     View.created_at.desc()).first()
        return view


class Timeline(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Timeline model."""
    name = Column(Unicode(255))
    description = Column(UnicodeText())
    color = Column(Unicode(6))
    user_id = Column(Integer, ForeignKey('user.id'))
    searchindex_id = Column(Integer, ForeignKey('searchindex.id'))
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    analysis = relationship('Analysis', backref='timeline', lazy='select')

    def __init__(self,
                 name,
                 user,
                 sketch,
                 searchindex,
                 color=None,
                 description=None):
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
        super(Timeline, self).__init__()
        self.name = name
        self.description = description

        if not color:
            color = random_color()

        self.color = color
        self.user = user
        self.sketch = sketch
        self.searchindex = searchindex


class SearchIndex(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin,
                  BaseModel):
    """Implements the SearchIndex model."""
    name = Column(Unicode(255))
    description = Column(UnicodeText())
    index_name = Column(Unicode(255))
    user_id = Column(Integer, ForeignKey('user.id'))
    timelines = relationship(
        'Timeline', backref='searchindex', lazy='dynamic')
    events = relationship('Event', backref='searchindex', lazy='dynamic')

    def __init__(self, name, description, index_name, user):
        """Initialize the SearchIndex object.

        Args:
            name: The name of the timeline
            description: The description for the timeline
            index_name: The name of the searchindex
            user: A user (instance of timesketch.models.user.User)
        """
        super(SearchIndex, self).__init__()
        self.name = name
        self.description = description
        self.index_name = index_name
        self.user = user


class View(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin,
           BaseModel):
    """Implements the View model."""
    name = Column(Unicode(255))
    description = Column(UnicodeText())
    query_string = Column(UnicodeText())
    query_filter = Column(UnicodeText())
    query_dsl = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    searchtemplate_id = Column(Integer, ForeignKey('searchtemplate.id'))
    aggregations = relationship('Aggregation', backref='view', lazy='select')
    aggregationgroups = relationship(
        'AggregationGroup', backref='view', lazy='select')

    def __init__(self,
                 name,
                 sketch,
                 user,
                 description=None,
                 searchtemplate=None,
                 query_string=None,
                 query_filter=None,
                 query_dsl=None):
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
        """
        super(View, self).__init__()
        self.name = name
        self.sketch = sketch
        self.user = user
        self.description = description
        self.searchtemplate = searchtemplate
        self.query_string = query_string
        self.query_filter = query_filter
        self.query_dsl = query_dsl

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
        DEFAULT_SIZE = 40 # Number of resulting documents to return
        DEFAULT_LIMIT = DEFAULT_SIZE  # Number of resulting documents to return
        DEFAULT_VALUES = {
            'time_start': None,
            'time_end': None,
            'from': DEFAULT_FROM,
            'size': DEFAULT_SIZE,
            'terminate_after': DEFAULT_LIMIT,
            'indices': [],
            'exclude': [],
            'order': 'asc',
            'chips': []
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
        missing_attributes = list(
            set(DEFAULT_VALUES.keys()) - set(filter_dict.keys()))
        for key in missing_attributes:
            filter_dict[key] = DEFAULT_VALUES[key]

        return json.dumps(filter_dict, ensure_ascii=False)


class SearchTemplate(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin,
                     BaseModel):
    """Implements the Search Template model."""
    name = Column(Unicode(255))
    description = Column(UnicodeText())
    query_string = Column(UnicodeText())
    query_filter = Column(UnicodeText())
    query_dsl = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    views = relationship('View', backref='searchtemplate', lazy='select')

    def __init__(self,
                 name,
                 user,
                 description=None,
                 query_string=None,
                 query_filter=None,
                 query_dsl=None):
        """Initialize the Search Template object.

        Args:
            name: The name of the timeline
            user: A user (instance of timesketch.models.user.User)
            description (str): Description of the search template
            query_string: The query string
            query_filter: The filter to apply (JSON format as string)
            query_dsl: A query DSL document (JSON format as string)
        """
        super(SearchTemplate, self).__init__()
        self.name = name
        self.user = user
        self.description = description
        self.query_string = query_string
        if not query_filter:
            filter_template = {
                'exclude': [],
                'indices': '_all',
                'time_start': None,
                'time_end': None,
                'terminate_after': 40,
                'from': 0,
                'order': 'asc',
                'size': '40'
            }
            query_filter = json.dumps(filter_template, ensure_ascii=False)
        self.query_filter = query_filter
        self.query_dsl = query_dsl


class Event(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Event model."""
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    searchindex_id = Column(Integer, ForeignKey('searchindex.id'))
    document_id = Column(Unicode(255))

    def __init__(self, sketch, searchindex, document_id):
        """Initialize the Event object.

        Args:
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            searchindex: A searchindex
                (instance of timesketch.models.sketch.SearchIndex)
            document_id = String with the datastore document ID
        """
        super(Event, self).__init__()
        self.sketch = sketch
        self.searchindex = searchindex
        self.document_id = document_id


class Story(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin,
            BaseModel):
    """Implements the Story model."""
    title = Column(Unicode(255))
    content = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    sketch_id = Column(Integer, ForeignKey('sketch.id'))

    def __init__(self, title, content, sketch, user):
        """Initialize the Story object.

        Args:
            title: The title of the story
            content: Content of the story
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            user: A user (instance of timesketch.models.user.User)
        """
        super(Story, self).__init__()
        self.title = title
        self.content = content
        self.sketch = sketch
        self.user = user


class Aggregation(AccessControlMixin, LabelMixin, StatusMixin, CommentMixin,
                  BaseModel):
    """Implements the Aggregation model."""
    name = Column(Unicode(255))
    description = Column(UnicodeText())
    agg_type = Column(Unicode(255))
    parameters = Column(UnicodeText())
    chart_type = Column(Unicode(255))
    user_id = Column(Integer, ForeignKey('user.id'))
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    view_id = Column(Integer, ForeignKey('view.id'))
    aggregationgroup_id = Column(Integer, ForeignKey('aggregationgroup.id'))

    def __init__(self, name, description, agg_type, parameters, chart_type,
                 user, sketch, view=None, aggregationgroup=None):
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
        super(Aggregation, self).__init__()
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
        AccessControlMixin, LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Aggregation Group model."""
    name = Column(Unicode(255))
    description = Column(UnicodeText())
    aggregations = relationship(
        'Aggregation', backref='aggregationgroup', lazy='select')
    parameters = Column(UnicodeText())
    orientation = Column(Unicode(40))
    user_id = Column(Integer, ForeignKey('user.id'))
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    view_id = Column(Integer, ForeignKey('view.id'))

    def __init__(
            self, name, description, user, sketch, aggregations=None,
            parameters='', orientation='', view=None):
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
        super(AggregationGroup, self).__init__()
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
    analysissession_id = Column(Integer, ForeignKey('analysissession.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    timeline_id = Column(Integer, ForeignKey('timeline.id'))
    searchindex_id = Column(Integer, ForeignKey('searchindex.id'))

    def __init__(self, name, description, analyzer_name, parameters, user,
                 sketch, timeline=None, searchindex=None, result=None):
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
        super(Analysis, self).__init__()
        self.name = name
        self.description = description
        self.analyzer_name = analyzer_name
        self.parameters = parameters
        self.user = user
        self.sketch = sketch
        self.timeline = timeline
        self.searchindex = searchindex
        self.result = result
        self.log = ''


class AnalysisSession(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the analysis session model."""
    user_id = Column(Integer, ForeignKey('user.id'))
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    analyses = relationship(
        'Analysis', backref='analysissession', lazy='select')

    def __init__(self, user, sketch):
        """Initialize the AnalysisSession object.

        Args:
            user (User): The user who created the aggregation
            sketch (Sketch): The sketch that the aggregation is bound to
        """
        super(AnalysisSession, self).__init__()
        self.user = user
        self.sketch = sketch


class Attribute(BaseModel):
    """Implements the attribute model."""
    user_id = Column(Integer, ForeignKey('user.id'))
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    name = Column(UnicodeText())
    ontology = Column(UnicodeText())
    values = relationship(
        'AttributeValue', backref='attribute', lazy='select')

    def __init__(self, user, sketch, name, ontology):
        """Initialize the Attribute object.

        Args:
            user (User): The user who created the attribute
            sketch (Sketch): The sketch that the attribute is bound to
            name (str): the name of the attribute.
            ontology (str): The ontology of the value, The values that can
                be used are defined in timesketch/lib/ontology.py (ONTOLOGY).
        """
        super(Attribute, self).__init__()
        self.user = user
        self.sketch = sketch
        self.name = name
        self.ontology = ontology


class AttributeValue(BaseModel):
    """Implements the attribute value model."""
    user_id = Column(Integer, ForeignKey('user.id'))
    attribute_id = Column(Integer, ForeignKey('attribute.id'))
    value = Column(UnicodeText())

    def __init__(
            self, user, attribute, value):
        """Initialize the Attribute value object.

        Args:
            user (User): The user who created the attribute value.
            attribute (Attribute): The attribute this value is bound to.
            value (str): a string that contains the value for the attribute.
                The ontology could influence how this will be cast when
                interpreted.
        """
        super(AttributeValue, self).__init__()
        self.user = user
        self.attribute = attribute
        self.value = value


class Graph(LabelMixin, CommentMixin, BaseModel):
    """Implements the graph model."""
    user_id = Column(Integer, ForeignKey('user.id'))
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    name = Column(UnicodeText())
    description = Column(UnicodeText())
    graph_config = Column(UnicodeText())
    graph_elements = Column(UnicodeText())
    graph_thumbnail = Column(UnicodeText())
    num_nodes = Column(Integer)
    num_edges = Column(Integer)

    def __init__(self, user, sketch, name, description=None, graph_config=None,
                 graph_elements=None, graph_thumbnail=None, num_nodes=None,
                 num_edges=None):
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
        super(Graph, self).__init__()
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
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    graph_plugin = Column(UnicodeText())
    graph_config = Column(UnicodeText())
    graph_elements = Column(UnicodeText())
    num_nodes = Column(Integer)
    num_edges = Column(Integer)

    def __init__(self, sketch, graph_plugin=None, graph_config=None,
                 graph_elements=None, num_nodes=None, num_edges=None):
        """Initialize the GraphCache object.

        Args:
            sketch (Sketch): The sketch that the graph is bound to.
            graph_plugin (str): Name of the graph plugin that was used.
            graph_config (dict): Config used when generating the graph.
            graph_elements (str): Graph in json string format.
            num_nodes (int): Number of nodes in the graph.
            num_edges (int): Number of edges in the graph.
        """
        super(GraphCache, self).__init__()
        self.sketch = sketch
        self.graph_plugin = graph_plugin
        self.graph_config = graph_config
        self.graph_elements = graph_elements
        self.num_nodes = num_nodes
        self.num_edges = num_edges
