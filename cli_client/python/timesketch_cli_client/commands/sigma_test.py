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
"""Tests for sigma command."""

import unittest

import mock
from click.testing import CliRunner
from timesketch_api_client import test_lib as api_test_lib

from .. import test_lib
from .sigma import sigma_group


class SigmaTest(unittest.TestCase):
    """Test Sigma CLI command."""

    @mock.patch("requests.Session", api_test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.ctx = test_lib.get_cli_context()

    def test_list_sigmarules(self):
        """Test to list Sigma rules."""
        runner = CliRunner()
        result = runner.invoke(
            sigma_group,
            ["list"],
            obj=self.ctx,
        )
        assert 1 is result.exit_code

    def test_describe_sigmarules_missing_rule_uuid(self):
        """Test to describe Sigma rules."""
        runner = CliRunner()
        result = runner.invoke(
            sigma_group,
            ["describe"],
            obj=self.ctx,
        )
        assert 2 is result.exit_code
        assert "Error: Missing option '--rule-uuid'." in result.output
