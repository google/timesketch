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
"""Tests for sketch command."""

import unittest
import mock

from click.testing import CliRunner

from timesketch_api_client import test_lib as api_test_lib

from .. import test_lib
from .sketch import sketch_group


class SketchTest(unittest.TestCase):
    """Test Sketch."""

    @mock.patch('requests.Session', api_test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        self.ctx = test_lib.get_cli_context()

    def test_list_sketches(self):
        """Test to list sketches."""
        runner = CliRunner()
        result = runner.invoke(sketch_group, ['list'], obj=self.ctx)
        assert result.output == '1 test\n'

    def test_describe_sketch(self):
        """Test to get details for a sketch."""
        runner = CliRunner()
        result = runner.invoke(sketch_group, ['describe'], obj=self.ctx)
        assert result.output == 'Name: test\nDescription: test\n'
