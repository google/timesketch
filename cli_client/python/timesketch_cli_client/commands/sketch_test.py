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

import mock
import unittest

from click.testing import CliRunner

from timesketch_api_client import test_lib
from timesketch_api_client import client

from ..cli import TimesketchCli
from .sketch import sketch_group


class SketchTest(unittest.TestCase):
    """Test Sketch object."""

    @mock.patch('requests.Session', test_lib.mock_session)
    def setUp(self):
        """Setup test case."""
        api_client = client.TimesketchApi('http://127.0.0.1', 'test', 'test')
        self.ctx = TimesketchCli(api_client=api_client, sketch_from_flag=1)

    def test_list_sketches(self):
        runner = CliRunner()
        result = runner.invoke(sketch_group, ['list'], obj=self.ctx)
        assert result.output == '1 test\n'

    def test_describe_sketch(self):
        runner = CliRunner()
        result = runner.invoke(sketch_group, ['describe'], obj=self.ctx)
        assert result.output == 'Name: test\nDescription: test\n'
