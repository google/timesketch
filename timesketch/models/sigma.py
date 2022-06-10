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


class Sigma(
    BaseModel, LabelMixin, StatusMixin, CommentMixin, GenericAttributeMixin
):
    """Implements the Sigma model."""

    uuid = Column(Unicode(255), unique=True)
    rule_yaml = Column(UnicodeText())
    user_id = Column(
        Integer, ForeignKey("user.id")
    )  # who added the rule to the system (TS user)
    es_query = Column(UnicodeText())  # (auto generated / updated from parser)

    def __init__(self, rule_uuid, user, rule_yaml=None):
        """Initialize the Sigma object.

        Args:
            rule_uuid: UUID for the rule
            rule_yaml: Name of the rule
        """
        super().__init__()
        self.rule_uuid = rule_uuid
        self.user = user
        self.es_query = ""
        if not rule_yaml:
            self.rule_yaml = ""
