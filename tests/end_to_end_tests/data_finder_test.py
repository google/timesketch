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
"""End to end tests of Timesketch data finder functionality."""

from . import interface
from . import manager


class DataFinderTest(interface.BaseEndToEndTest):
    """End to end tests for data finder functionality."""

    NAME = "data_finder_test"

    def setup(self):
        """Import test timeline."""
        self.import_timeline("evtx_part.csv")

    def test_data_finder(self):
        """Test the data finder."""
        results = self.sketch.run_data_finder(
            start_date="2010-01-01T00:00:00",
            end_date="2010-06-30T12:00:00",
            rule_names=["test_data_finder"],
        )

        result_dict = results[0]
        self.assertions.assertFalse(result_dict.get("test_data_finder")[0])

        results = self.sketch.run_data_finder(
            start_date="2012-03-10T00:00:00",
            end_date="2012-03-30T12:00:00",
            rule_names=["test_data_finder"],
        )

        result_dict = results[0]
        self.assertions.assertTrue(result_dict.get("test_data_finder")[0])
        self.assertions.assertTrue(
            result_dict.get("test_data_finder")[1].startswith("Data disc")
        )


manager.EndToEndTestManager.register_test(DataFinderTest)
