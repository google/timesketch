# Copyright 2020 Google Inc. All rights reserved.
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
"""End to end tests of Timesketch client functionality."""

from . import interface
from . import manager


class ClientTest(interface.BaseEndToEndTest):
    """End to end tests for client functionality."""

    NAME = 'client_test'

    def test_client(self):
        """Client tests."""
        expected_user = 'test'
        user = self.api.current_user
        self.assertions.assertEqual(user.username, expected_user)
        self.assertions.assertEqual(user.is_admin, False)
        self.assertions.assertEqual(user.is_active, True)

        sketch_name = 'Testing'
        sketch_description = 'This is truly a foobar'
        new_sketch = self.api.create_sketch(
            name=sketch_name, description=sketch_description)

        self.assertions.assertEqual(new_sketch.name, sketch_name)
        self.assertions.assertEqual(
            new_sketch.description, sketch_description)

        first_sketch = self.api.get_sketch(1)
        self.assertions.assertEqual(
            self.sketch.name, first_sketch.name)

        sketches = list(self.api.list_sketches())
        self.assertions.assertEqual(len(sketches), 2)

        for index in self.api.list_searchindices():
            self.assertions.assertTrue(bool(index.name))


manager.EndToEndTestManager.register_test(ClientTest)
