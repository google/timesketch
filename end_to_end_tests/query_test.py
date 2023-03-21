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
"""End to end tests of Timesketch query functionality."""

import pandas as pd
from timesketch_api_client import search

from . import interface
from . import manager


class QueryTest(interface.BaseEndToEndTest):
    """End to end tests for query functionality."""

    NAME = "query_test"

    def setup(self):
        """Import test timeline."""
        self.import_timeline("evtx.plaso")

    def test_wildcard_query(self):
        """Wildcard query over all data in the sketch."""
        search_obj = search.Search(self.sketch)
        search_obj.query_string = "*"
        data_frame = search_obj.table
        count = len(data_frame)
        self.assertions.assertEqual(count, 3205)

    def test_specific_queries(self):
        """Test few specific queries."""
        search_obj = search.Search(self.sketch)
        search_obj.query_string = 'message_identifier: "1073748864"'
        search_obj.return_fields = "computer_name,data_type,strings,user_sid"

        data_frame = search_obj.table
        self.assertions.assertEqual(len(data_frame), 204)

        computers = list(data_frame.computer_name.unique())
        self.assertions.assertEqual(len(computers), 1)
        self.assertions.assertEqual(computers[0], "WKS-WIN764BITB.shieldbase.local")

        def extract_strings(row):
            strings = row.strings
            return pd.Series(
                {
                    "service": strings[0],
                    "state_from": strings[1],
                    "state_to": strings[2],
                    "by": strings[3],
                }
            )

        strings_frame = data_frame.apply(extract_strings, axis=1)
        services = set(strings_frame.service.unique())
        expected_set = set(
            ["Background Intelligent Transfer Service", "Windows Modules Installer"]
        )
        self.assertions.assertSetEqual(services, expected_set)

        search_name = "My First Search"
        search_obj.name = search_name
        search_obj.description = "Can it be, is it really?"

        search_obj.save()

        _ = self.sketch.lazyload_data(refresh_cache=True)
        saved_search = None
        for search_obj in self.sketch.list_saved_searches():
            if search_obj.name == search_name:
                saved_search = search_obj
                break

        if search_obj is None:
            raise RuntimeError("Unable to find the saved search.")
        self.assertions.assertEqual(
            saved_search.return_fields,
            "computer_name,data_type,strings,user_sid,datetime",
        )

        self.assertions.assertEqual(
            saved_search.query_string, 'message_identifier: "1073748864"'
        )


manager.EndToEndTestManager.register_test(QueryTest)
