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

import json

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
    user_id = Column(Integer, ForeignKey(u'user.id'))
    timelines = relationship(u'Timeline', backref=u'sketch', lazy=u'select')
    views = relationship(u'View', backref=u'sketch', lazy=u'select')
    events = relationship(u'Event', backref=u'sketch', lazy=u'select')
    stories = relationship(u'Story', backref=u'sketch', lazy=u'select')

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
    def get_named_views(self):
        """
        Get named views, i.e. only views that has a name. Views without names
        are used as user state views and should not be visible in the UI.
        """
        views = [
            view for view in self.views
            if view.get_status.status != u'deleted' and view.name != u''
        ]
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
            if (timeline_status or index_status) in [u'processing', u'fail']:
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
        view = View.query.filter(View.user == user, View.name == u'',
                                 View.sketch_id == self.id).order_by(
                                     View.created_at.desc()).first()
        return view


class Timeline(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Timeline model."""
    name = Column(Unicode(255))
    description = Column(UnicodeText())
    color = Column(Unicode(6))
    user_id = Column(Integer, ForeignKey(u'user.id'))
    searchindex_id = Column(Integer, ForeignKey(u'searchindex.id'))
    sketch_id = Column(Integer, ForeignKey(u'sketch.id'))

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
    user_id = Column(Integer, ForeignKey(u'user.id'))
    timelines = relationship(
        u'Timeline', backref=u'searchindex', lazy=u'dynamic')
    events = relationship(u'Event', backref=u'searchindex', lazy=u'dynamic')

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
    query_string = Column(UnicodeText())
    query_filter = Column(UnicodeText())
    query_dsl = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey(u'user.id'))
    sketch_id = Column(Integer, ForeignKey(u'sketch.id'))
    searchtemplate_id = Column(Integer, ForeignKey(u'searchtemplate.id'))

    def __init__(self,
                 name,
                 sketch,
                 user,
                 searchtemplate=None,
                 query_string=None,
                 query_filter=None,
                 query_dsl=None):
        """Initialize the View object.

        Args:
            name: The name of the timeline
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            user: A user (instance of timesketch.models.user.User)
            searchtemplate: Instance of timesketch.models.sketch.SearchTemplate
            query_string: The query string
            query_filter: The filter to apply (JSON format as string)
            query_dsl: A query DSL document (JSON format as string)
        """
        super(View, self).__init__()
        self.name = name
        self.sketch = sketch
        self.user = user
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
            u'time_start': None,
            u'time_end': None,
            u'limit': DEFAULT_LIMIT,
            u'from': DEFAULT_FROM,
            u'size': DEFAULT_SIZE,
            u'indices': [],
            u'exclude': [],
            u'order': u'asc'
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
    query_string = Column(UnicodeText())
    query_filter = Column(UnicodeText())
    query_dsl = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey(u'user.id'))
    views = relationship(u'View', backref=u'searchtemplate', lazy=u'select')

    def __init__(self,
                 name,
                 user,
                 query_string=None,
                 query_filter=None,
                 query_dsl=None):
        """Initialize the Search Template object.

        Args:
            name: The name of the timeline
            user: A user (instance of timesketch.models.user.User)
            query_string: The query string
            query_filter: The filter to apply (JSON format as string)
            query_dsl: A query DSL document (JSON format as string)
        """
        super(SearchTemplate, self).__init__()
        self.name = name
        self.user = user
        self.query_string = query_string
        if not query_filter:
            filter_template = {
                u'exclude': [],
                u'indices': u'_all',
                u'time_start': None,
                u'time_end': None,
                u'limit': 40,
                u'from': 0,
                u'order': u'asc',
                u'size': u'40'
            }
            query_filter = json.dumps(filter_template, ensure_ascii=False)
        self.query_filter = query_filter
        self.query_dsl = query_dsl


class Event(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Event model."""
    sketch_id = Column(Integer, ForeignKey(u'sketch.id'))
    searchindex_id = Column(Integer, ForeignKey(u'searchindex.id'))
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
    user_id = Column(Integer, ForeignKey(u'user.id'))
    sketch_id = Column(Integer, ForeignKey(u'sketch.id'))

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
