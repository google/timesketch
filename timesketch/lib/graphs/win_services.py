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
"""Graph plugin for Windows services."""

from timesketch.lib.graphs.interface import BaseGraphPlugin
from timesketch.lib.graphs import manager


class WinServiceGraph(BaseGraphPlugin):
    """Graph plugin for Windows services."""

    NAME = "WinService"
    DISPLAY_NAME = "Windows services"

    def generate(self):
        """Generate the graph.

        Returns:
            Graph object instance.
        """
        query = "event_identifier:7045"
        return_fields = ["computer_name", "username", "strings"]

        events = self.event_stream(query_string=query, return_fields=return_fields)

        for event in events:
            computer_name = event["_source"].get("computer_name", "UNKNOWN")
            username = event["_source"].get("username", "UNKNOWN")
            event_strings = event["_source"].get("strings", [])

            # Skip event if we don't have enough data to build the graph.
            try:
                service_name = event_strings[0]
                image_path = event_strings[1]
                service_type = event_strings[2]
                start_type = event_strings[3]
            except IndexError:
                continue

            computer = self.graph.add_node(computer_name, {"type": "computer"})
            user = self.graph.add_node(username, {"type": "user"})
            service = self.graph.add_node(
                service_name, {"type": "winservice", "image_path": image_path}
            )

            self.graph.add_edge(user, service, start_type, event)
            self.graph.add_edge(service, computer, service_type, event)

        self.graph.commit()

        return self.graph


manager.GraphManager.register_graph(WinServiceGraph)
