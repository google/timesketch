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
    # JSON encoded dictionary with specification for the scenario.
    scenario_spec_json = Column(UnicodeText())
    investigations = relationship(
        'Investigation', backref='scenario', lazy='select')


class Investigation(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Investigation model."""
    name = Column(UnicodeText())
    display_name = Column(UnicodeText())    
    description = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    # JSON encoded dictionary with specification for the investigation.
    investigation_spec_json = Column(UnicodeText())
    timeframes = relationship(
        'InvestigationTimeframe', backref='investigation', lazy='select')
    timelines = relationship(
        'Timeline', backref='investigation', lazy='select')
    questions = relationship(
        'InvestigativeQuestion', backref='investigation', lazy='select')
    conclusions = relationship(
        'Conclusion', backref='investigation', lazy='select')

class InvestigationTimeframe(BaseModel):
    """Implements the InvestigationTimeframe model."""
    start_time = Column(UnicodeText())
    end_time = Column(UnicodeText())
    investigation_id = Column(Integer, ForeignKey('investigation.id'))

class InvestigativeQuestion(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the InvestigativeQuestion model."""
    name = Column(UnicodeText())
    display_name = Column(UnicodeText())
    description = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    investigation_id = Column(Integer, ForeignKey('investigation.id'))
    # JSON encoded dictionary with specification for the question.
    question_spec_json = Column(UnicodeText())
    # JSON encoded dictionary with parameters/values. This will be used in e.g
    # the data_finder as re_perameters.
    parameters_json = Column(UnicodeText())
    conclusions = relationship(
        'Conclusion', backref='investigativequestion', lazy='select')


class Conclusion(LabelMixin, StatusMixin, CommentMixin, BaseModel):
    """Implements the Conclusion model."""
    conclusion = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    answer_simple = Column(Boolean(), default=False)
    answer_analyzer = Column(Boolean(), default=False)
    # Support for the conclusion (optional).
    stories = relationship('Story', backref='conclusion', lazy='select')
    searches = relationship('View', backref='conclusion', lazy='select')
    graphs = relationship('Graph', backref='conclusion', lazy='select')
    aggregations = relationship(
        'Aggregations', backref='conclusion', lazy='select')
