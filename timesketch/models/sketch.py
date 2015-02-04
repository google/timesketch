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

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import relationship

from timesketch.models import BaseModel
from timesketch.models.acl import AccessControlMixin
from timesketch.models.annotations import LabelMixin
from timesketch.models.annotations import CommentMixin
from timesketch.models.annotations import StatusMixin
from timesketch.lib.utils import random_color


class Sketch(AccessControlMixin, LabelMixin, StatusMixin, BaseModel):
    """Implements the Sketch model.

    A Sketch is the collaborative entity in Timesketch. It contains one or more
    timelines that can be grouped and queried on.
    """
    name = Column(String(255))
    description = Column(Text())
    user_id = Column(Integer, ForeignKey('user.id'))
    timelines = relationship('Timeline', backref='sketch', lazy='select')
    views = relationship('View', backref='sketch', lazy='select')
    events = relationship('Event', backref='sketch', lazy='select')

    def __init__(self, name, description, user):
        """Initialize the Sketch object.

        Args:
            name: The name of the sketch
            description: Description of the sketch
            user: A user (instance of timesketch.models.user.User)
        """
        self.name = name
        self.description = description
        self.user = user

    @property
    def get_named_views(self):
        """
        Get named views, i.e. only views that has a name. Views without names
        are used as user state views and should not be visible in the UI.
        """
        return View.query.filter(View.sketch == self, View.name != '')


class Timeline(StatusMixin, BaseModel):
    """Implements the Timeline model."""
    name = Column(String(255))
    description = Column(Text())
    color = Column(String(6))
    user_id = Column(Integer, ForeignKey('user.id'))
    searchindex_id = Column(Integer, ForeignKey('searchindex.id'))
    sketch_id = Column(Integer, ForeignKey('sketch.id'))

    def __init__(
            self, name, user, sketch, searchindex, color=None,
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
        self.name = name
        self.description = description

        if not color:
            self.color = random_color()

        self.color = color
        self.user = user
        self.sketch = sketch
        self.searchindex = searchindex


class SearchIndex(AccessControlMixin, LabelMixin, BaseModel):
    """Implements the SearchIndex model."""
    name = Column(String(255))
    description = Column(Text())
    index_name = Column(String(255))
    user_id = Column(Integer, ForeignKey('user.id'))
    timelines = relationship(
        'Timeline', backref='searchindex', lazy='dynamic')
    events = relationship(
        'Event', backref='searchindex', lazy='dynamic')

    def __init__(self, name, description, index_name, user):
        """Initialize the SearchIndex object.

        Args:
            name: The name of the timeline
            description: The description for the timeline
            index_name: The name of the searchindex
            user: A user (instance of timesketch.models.user.User)
        """
        self.name = name
        self.description = description
        self.index_name = index_name
        self.user = user


class View(AccessControlMixin, LabelMixin, BaseModel):
    """Implements the View model."""
    name = Column(String(255))
    query_string = Column(String(255))
    query_filter = Column(Text())
    user_id = Column(Integer, ForeignKey('user.id'))
    sketch_id = Column(Integer, ForeignKey('sketch.id'))

    def __init__(self, name, query_string, query_filter, sketch, user):
        """Initialize the View object.

        Args:
            name: The name of the timeline
            query_string: The query string
            query_filter: The filter to apply (JSON format as string)
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            user: A user (instance of timesketch.models.user.User)
        """
        self.name = name
        self.query_string = query_string
        self.query_filter = query_filter
        self.sketch = sketch
        self.user = user


class Event(LabelMixin, CommentMixin, BaseModel):
    """Implements the Event model."""
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    searchindex_id = Column(Integer, ForeignKey('searchindex.id'))
    document_id = Column(String(255))

    def __init__(self, sketch, searchindex, document_id):
        """Initialize the Event object.

        Args:
            sketch: A sketch (instance of timesketch.models.sketch.Sketch)
            searchindex: A searchindex
                (instance of timesketch.models.sketch.SearchIndex)
            document_id = String with the datastore document ID
        """
        self.sketch = sketch
        self.searchindex = searchindex
        self.document_id = document_id
