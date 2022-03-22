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

import datetime
import markdown


from timesketch.lib.stories import interface
from timesketch.lib.stories import manager


class HTMLStoryExporter(interface.StoryExporter):
    """HTML story exporter."""

    # String representing the output format of the story.
    EXPORT_FORMAT = "html"

    # Number of rows of a DataFrame to include at the top of a markdown table.
    _DATAFRAME_HEADER_ROWS = 30

    HTML_HEADER = (
        "<html>"
        "    <head>"
        '<script src="https://cdn.jsdelivr.net/npm/vega@5"></script>'
        '<script src="https://cdn.jsdelivr.net/npm/vega-lite@4"></script>'
        ' <script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script>'
        " </head>"
        " <body>"
    )

    HTML_FOOTER = "</body></html>"

    def _data_frame_to_html(self, data_frame):
        """Returns a HTML formatted string from a pandas DataFrame."""
        nr_rows, _ = data_frame.shape
        if not nr_rows:
            return "<b>empty table</b>"

        if nr_rows <= self._DATAFRAME_HEADER_ROWS:
            return data_frame.to_html(index=False)

        html_code = data_frame.to_html(
            index=False, max_rows=self._DATAFRAME_HEADER_ROWS
        )
        return (
            "{0:s}\n<b>...</b><br/>"
            "<i>Table contains more records than are displayed. "
            "Only the first {1:d} records out of total {2:d} are "
            "printed out. View the full view in Timesketch to get all "
            "the results.</i>"
        ).format(html_code, self._DATAFRAME_HEADER_ROWS, nr_rows)

    def export_story(self):
        """Export the story as HTML."""
        return_strings = [self.HTML_HEADER]

        return_strings.append("<h1>{0:s}</h1>".format(self._story_title))
        date_now = datetime.datetime.utcnow()
        return_strings.append(
            "Story Metadata:<br/><ul><li><b>Creation Date:</b> {0:s}</li>"
            "<li><b>Created by:</b> {1:s}</li>"
            "<li><b>Report Generated:</b> {2:s}</li>"
            "<li><b>Report Exported by:</b> {3:s}</li></ul>".format(
                self._creation_date,
                self._story_author,
                date_now.isoformat(),
                self._story_exporter,
            )
        )

        md = markdown.Markdown()

        chart_number = 1
        charts = []
        for line_dict in self._data_lines:
            line_type = line_dict.get("type", "")
            if line_type == "text":
                return_strings.append(md.convert(line_dict.get("value", "")))

            elif line_type == "aggregation":
                data_dict = line_dict.get("value")
                agg_obj = data_dict.get("aggregation")
                chart_type = data_dict.get("chart_type")
                if chart_type == "table":
                    df = agg_obj.to_pandas()
                    return_strings.append(self._data_frame_to_html(df))
                else:
                    parameters = data_dict.get("parameters", {})
                    title = parameters.get("title", data_dict.get("name"))
                    chart_color = parameters.get("chart_color")

                    chart = agg_obj.to_chart(
                        chart_name=chart_type,
                        chart_title=title,
                        interactive=True,
                        color=chart_color,
                        as_chart=True,
                    )

                    charts.append(chart)
                    return_strings.append(
                        '<div id="vis{0:d}"></div>'.format(chart_number)
                    )
                    chart_number += 1

            elif line_type == "dataframe":
                return_strings.append(self._data_frame_to_html(line_dict.get("value")))

            elif line_type == "chart":
                data_dict = line_dict.get("value")
                chart = data_dict.get("chart")

                charts.append(chart)
                return_strings.append('<div id="vis{0:d}"></div>'.format(chart_number))
                chart_number += 1

        if charts:
            return_strings.append('<script type="text/javascript">')
            for index, chart in enumerate(charts):
                vis_nr = index + 1
                return_strings.append(
                    "vegaEmbed('#vis{0:d}', {1:s})."
                    "catch(console.error);".format(vis_nr, chart.to_json(indent=None))
                )
            return_strings.append("</script>")

        return_strings.append("</body></html>")
        return "\n\n".join(return_strings)


manager.StoryExportManager.register_exporter(HTMLStoryExporter)
