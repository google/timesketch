# Copyright 2021 Google Inc. All rights reserved.
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
"""This module implements the models for the Timesketch scenario system."""

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Boolean
from sqlalchemy import UnicodeText
from sqlalchemy.orm import relationship

from timesketch.models import BaseModel
from timesketch.models.annotations import LabelMixin
from timesketch.models.annotations import CommentMixin
from timesketch.models.annotations import StatusMixin


class Scenario(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Scenario model."""
    name = Column(UnicodeText())
    display_name = Column(UnicodeText())    
    description = Column(UnicodeText())
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    investigations = relationship(
        'Investigation', backref='scenario', lazy='select')


class Investigation(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Investigation model."""
    name = Column(UnicodeText())
    display_name = Column(UnicodeText())    
    description = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    timeframes = Column(UnicodeText())
    timelines = relationship(
        'Timeline', backref='investigation', lazy='select')
    questions = relationship(
        'InvestigativeQuestion', backref='investigation', lazy='select')
    conclutions = relationship(
        'Conclusion', backref='investigativequestion', lazy='select')



class InvestigativeQuestion(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the InvestigativeQuestion model."""
    name = Column(UnicodeText())
    display_name = Column(UnicodeText())
    description = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    investigation_id = Column(Integer, ForeignKey('investigation.id'))

    # Data source definition names to feed into the data_finder. These are
    # data sources that needs to be present in order to answer the question.
    data_sources = Column(UnicodeText())

    # JSON encoded dictionary with parameters/values. This will be used in e.g
    # the data_finder as re_perameters.
    parameters = Column(UnicodeText())

    # JSON encoded dictionary with the specification from the question YAML.
    question_spec = Column(UnicodeText())

    # Pointers to helpful supportive functions that aim at helping the analyst
    # get started with the work on answering the question.
    # TODO: Add aggregation templates (as soon as they exist)
    analyzers = Column(UnicodeText())
    graphs = Column(UnicodeText())
    sigmarules = Column(UnicodeText())
    searchtemplates = relationship(
        'SearchTemplate', backref='investigativequestion', lazy='select')

    conclutions = relationship(
        'Conclusion', backref='investigativequestion', lazy='select')


class Conclusion(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Conclusion model."""
    conclusion = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    answer_simple = Column(Boolean(), default=False)
    answer_analyzer = Column(Boolean(), default=False)
    
    # Optional supportive data for transparency and reasoning.
    stories = relationship('Story', backref='conclusion', lazy='select')
    saved_searches = relationship('View', backref='conclusion', lazy='select')
    saved_graphs = relationship('Graph', backref='conclusion', lazy='select')
    saved_aggregations = relationship(
        'Aggregations', backref='conclusion', lazy='select')