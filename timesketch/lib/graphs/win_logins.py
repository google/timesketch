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
"""Graph plugin for Windows logins."""

from timesketch.lib.graphs.interface import BaseGraphPlugin
from timesketch.lib.graphs import manager


class WinLoginsGraph(BaseGraphPlugin):
    """Graph plugin for Windows logins."""

    NAME = "WinLogins"
    DISPLAY_NAME = "Windows logins"

    def generate(self):
        """Generate the graph.

        Returns:
            Graph object instance.
        """
        query = "tag:logon-event"
        return_fields = ["computer_name", "username", "logon_type", "logon_process"]

        events = self.event_stream(query_string=query, return_fields=return_fields)

        for event in events:
            computer_name = event["_source"].get("computer_name")
            username = event["_source"].get("username")
            logon_type = event["_source"].get("logon_type")

            computer = self.graph.add_node(computer_name, {"type": "computer"})
            user = self.graph.add_node(username, {"type": "user"})
            self.graph.add_edge(user, computer, logon_type, event)

        self.graph.commit()

        return self.graph


manager.GraphManager.register_graph(WinLoginsGraph)
