# Copyright 2022 Google Inc. All rights reserved.
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
"""This module implements the sigma model."""

from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import Unicode
from sqlalchemy import UnicodeText

from timesketch.models import BaseModel
from timesketch.models.annotations import LabelMixin
from timesketch.models.annotations import CommentMixin
from timesketch.models.annotations import StatusMixin
from timesketch.models.annotations import GenericAttributeMixin


class SigmaRule(
    BaseModel, LabelMixin, StatusMixin, CommentMixin, GenericAttributeMixin
):
    """Implements the SigmaRule model.
    Status mixin will be used to track the status of a rule:
        - stable: may be used in production systems, analyzers or dashboards
        - test: almost stable, could require some fine tuning, not for analyzers
        - experimental: can lead to false positives and is noisy, but can reveal
            interesting events, not for analyzers
        - deprecated: is replaced by another rule, not for analyzers
        - unsupported: can not be used in the current state, not for analyzers
    """

    title = Column(UnicodeText())
    description = Column(UnicodeText())
    rule_uuid = Column(Unicode(255), unique=True)
    rule_yaml = Column(UnicodeText())
    user_id = Column(Integer, ForeignKey("user.id"))
