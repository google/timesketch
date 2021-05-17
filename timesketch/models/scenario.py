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

from __future__ import unicode_literals

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import UnicodeText
from sqlalchemy.orm import relationship

from timesketch.models import BaseModel
from timesketch.models.annotations import LabelMixin
from timesketch.models.annotations import CommentMixin
from timesketch.models.annotations import StatusMixin


class Scenario(BaseModel):
    """Implements the Scenario model."""
    name = Column(UnicodeText())
    display_name = Column(UnicodeText())    
    description = Column(UnicodeText())
    sketch_id = Column(Integer, ForeignKey('sketch.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    investigations = relationship(
        'Investigation', backref='scenario', lazy='select')


class Investigation(BaseModel):
    """Implements the Investigation model."""
    name = Column(UnicodeText())
    display_name = Column(UnicodeText())    
    description = Column(UnicodeText())
    conclusion = Column(UnicodeText())
    timeframes = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    timelines = relationship(
        'Timeline', backref='investigation', lazy='select')
    questions = relationship(
        'InvestigationQuestion', backref='investigation', lazy='select')


class InvestigativeQuestion(BaseModel):
    """Implements the InvestigativeQuestion model."""
    name = Column(UnicodeText())
    display_name = Column(UnicodeText())
    description = Column(UnicodeText())
    conclusion = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey('user.id'))
    investigation_id = Column(Integer, ForeignKey('investigation.id'))
    # Helpful assets
    searchtemplates = relationship(
        'SearchTemplate', backref='investigationquestion', lazy='select')
    # There are no database models for analyzers and graphs. Reference them
    # by name instead.
    analyzers = Column(UnicodeText())
    graphs = Column(UnicodeText())
