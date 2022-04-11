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
"""Graph plugin for Chrome downloads."""

from timesketch.lib.graphs.interface import BaseGraphPlugin
from timesketch.lib.graphs import manager


class ChromeDownloadsGraph(BaseGraphPlugin):
    """Graph plugin for Chrome downloads and executions.

    This plugin will try to match any downloaded files with Windows prefetch
    executions.
    """

    NAME = "ChromeDownloads"
    DISPLAY_NAME = "Chrome downloads"

    def generate(self):
        """Generate the graph.

        Returns:
            Graph object instance.
        """
        query = 'data_type:"chrome:history:file_downloaded"'
        return_fields = ["hostname", "received_bytes", "full_path", "url", "domain"]

        chrome_events = self.event_stream(
            query_string=query, return_fields=return_fields
        )

        for chrome_event in chrome_events:
            computer_name = chrome_event["_source"].get("hostname", "")
            full_path = chrome_event["_source"].get("full_path", "")
            received_bytes = chrome_event["_source"].get("received_bytes", "")
            url = chrome_event["_source"].get("url", "")
            domain = chrome_event["_source"].get("domain", "")

            # Note: If any component of the path contains a \, it will be split
            # split, potentially wrong split. No data will be lost, but the
            # file node will have part of the path as the filename.
            # TODO: Revisit this and see if we can make it more robust.
            if "\\" in full_path:
                separator = "\\"
            else:
                separator = "/"

            filename = full_path.split(separator)[-1]
            computer = self.graph.add_node(computer_name, {"type": "computer"})

            # If full patch is missing, set url as label.
            if not full_path:
                full_path = url
                filename = f"UNKNOWN file download from {domain}"

            file = self.graph.add_node(
                filename,
                {
                    "full_path": full_path,
                    "received_bytes": received_bytes,
                    "type": "file",
                },
            )

            edge_label = f"Downloaded {received_bytes} bytes"
            self.graph.add_edge(computer, file, edge_label, chrome_event)

            # Get prefetch events that matches the filename.
            prefetch_query = f'executable:"*{filename}"'
            prefetch_return_fields = ["executable", "hostname"]
            prefetch_events = self.event_stream(
                query_string=prefetch_query,
                return_fields=prefetch_return_fields,
                scroll=False,
            )
            for prefetch_event in prefetch_events:
                computer_name = prefetch_event["_source"].get("hostname")
                executable_name = prefetch_event["_source"].get("executable")
                computer = self.graph.add_node(computer_name, {"type": "computer"})
                executable = self.graph.add_node(executable_name, {"type": "file"})
                self.graph.add_edge(computer, executable, "Executed", prefetch_event)

        self.graph.commit()

        return self.graph


manager.GraphManager.register_graph(ChromeDownloadsGraph)
