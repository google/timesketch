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
"""This file contains a markdown story exporter."""

from __future__ import unicode_literals

import tabulate

from timesketch.lib.stories import interface
from timesketch.lib.stories import manager


class MarkdownStoryExporter(interface.StoryExporter):
    """Markdown story exporter."""

    # String representing the output format of the story.
    EXPORT_FORMAT = "markdown"

    # Number of rows of a DataFrame to include at the top of a markdown table.
    _DATAFRAM_HEADER_ROWS = 20

    # Number of rows of a DataFrame to include as a trailer of a table.
    _DATAFRAM_TAIL_ROWS = 5

    # The number of rows
    def _dataframe_to_markdown(self, data_frame):
        """Returns a markdown formatted string from a pandas DataFrame."""
        nr_rows, _ = data_frame.shape
        if not nr_rows:
            return "*<empty table>*"

        if nr_rows <= (self._DATAFRAM_HEADER_ROWS + self._DATAFRAM_TAIL_ROWS):
            return tabulate.tabulate(data_frame, tablefmt="pipe", headers="keys")

        return_lines = []
        return_lines.append(
            tabulate.tabulate(
                data_frame[: self._DATAFRAM_HEADER_ROWS],
                tablefmt="pipe",
                headers="keys",
            )
        )
        return_lines.append("| ... |")
        return_lines.append(
            tabulate.tabulate(
                data_frame[-self._DATAFRAM_TAIL_ROWS :], tablefmt="pipe", headers="keys"
            )
        )
        return "\n".join(return_lines)

    def export_story(self):
        """Export the story as a markdown."""
        return_strings = []
        for line_dict in self._data_lines:
            line_type = line_dict.get("type", "")
            if line_type == "text":
                return_strings.append(line_dict.get("value", ""))

            elif line_type == "aggregation":
                aggregation_data = line_dict.get("value")
                aggregation = aggregation_data.get("aggregation")
                if not aggregation:
                    return_strings.append("**Unable to fetch aggregation data**")
                    continue
                return_strings.append(
                    self._dataframe_to_markdown(aggregation.to_pandas())
                )

            elif line_type == "dataframe":
                return_strings.append(
                    self._dataframe_to_markdown(line_dict.get("value"))
                )

            elif line_type == "chart":
                return_strings.append("*<unable_to_display_chart_objects>*")

        return "\n\n".join(return_strings)


manager.StoryExportManager.register_exporter(MarkdownStoryExporter)
