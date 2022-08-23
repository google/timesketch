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

    rule_uuid = Column(Unicode(255))
    rule_yaml = Column(UnicodeText())
    user_id = Column(
        Integer, ForeignKey("user.id")
    )  # who added the rule to the system (TS user)

    def __init__(
        self,
        user,
        rule_yaml=None,
        rule_uuid=None
    ):
        """Initialize the Sigma object.
        Args:
            user: A user (instance of timesketch.models.user.User)
            rule_yaml: yaml content of the rule
            rule_uuid: uuid of the rule
        """
        super().__init__()
        self.user = user
        self.rule_yaml = rule_yaml
        self.rule_uuid = rule_uuid
