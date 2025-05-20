# Copyright 2023 Google Inc. All rights reserved.
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
"""Tests for intelligence command."""

import unittest
import mock

from click.testing import CliRunner

# pylint: disable=import-error
from timesketch_api_client import test_lib as api_test_lib

# pylint: enable=import-error

from .. import test_lib
from .intelligence import intelligence_group


class IntelligenceTest(unittest.TestCase):
    """Test Sigma CLI command."""

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.ctx = test_lib.get_cli_context()

    def test_list_intelligence(self):
        """Test the 'intelligence list' command when no intelligence data exists.

        Verifies that the command exits with a non-zero status code and
        prints an appropriate message when the sketch has no intelligence
        attributes.
        """
        runner = CliRunner()
        result = runner.invoke(
            intelligence_group,
            ["list"],
            obj=self.ctx,
        )
        assert result.exit_code == 1
        assert "No intelligence found." in result.output
