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
    EXPORT_FORMAT = 'markdown'

    def export_story(self):
        """Export the story as a markdown."""
        return_strings = []
        for line in self._data_lines:
            if isinstance(line, str):
                return_strings.append(line)
                continue

            return_strings.append(
                tabulate.tabulate(line, tablefmt='pipe', headers='keys'))

        return '\n\n'.join(return_strings)


manager.StoryExportManager.register_exporter(MarkdownStoryExporter)
