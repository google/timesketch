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
"""Tests for the sigma model."""

from __future__ import unicode_literals

from timesketch.lib.testlib import ModelBaseTest
from timesketch.models import BaseModel
from timesketch.models.sigma import Sigma


class SigmaModelTest(ModelBaseTest):
    """Tests the sigma model"""

    def test_sigma_model(self):
        """Test that the test sigma rule has the expected data stored
        in the database.
        """
        expected_result = frozenset([])
        self._test_db_object(expected_result=expected_result, model_cls=Sigma)

    def test_set_active(self):
        """Test setting a Sigma rule to active"""
        # TODO(jaegeral): implement
        self.assertTrue(False)
