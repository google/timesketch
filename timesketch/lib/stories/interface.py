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
"""This file contains the interface for a story exporter."""

from __future__ import unicode_literals

import json


class StoryExporter(object):
    """Interface for a story exporter."""

    # String representing the output format of the story.
    EXPORT_FORMAT = ""

    def __init__(self):
        """Initialize the exporter."""
        self._creation_date = ""
        # List of Dict objects, two keys: type, value.
        self._data_lines = []
        self._data_fetcher = None
        self._story_author = "N/A"
        self._story_exporter = "N/A"
        self._story_title = "Unknown Title"

    @property
    def data(self):
        """Returns the exported story.

        Returns:
            The story in the exported format as defined in EXPORT_FORMAT.
        """
        return self.export_story()

    def export_story(self):
        """Export the story in the format."""
        raise NotImplementedError

    def from_string(self, json_string):
        """Feed the exporter with a JSON string.

        Args:
            json_string: JSON formatted string.
        """
        blocks = json.loads(json_string)
        if not isinstance(blocks, (list, tuple)):
            return

        for block in blocks:
            self.from_block_dict(block)

    def from_block_dict(self, block):
        """Feed the exporter with a single block dict.

        Args:
            block: single block dict from the story.
        """
        component = block.get("componentName", "N/A")
        properties = block.get("componentProps", {})

        if not self._data_fetcher:
            return

        if not component:
            self._data_lines.append({"type": "text", "value": block.get("content", "")})
        elif component == "TsViewEventList":
            self._data_lines.append(
                {
                    "type": "dataframe",
                    "value": self._data_fetcher.get_view(properties.get("view")),
                }
            )
        elif component == "TsAggregationCompact":
            self._data_lines.append(
                {
                    "type": "aggregation",
                    "value": self._data_fetcher.get_aggregation(
                        properties.get("aggregation")
                    ),
                }
            )
        elif component == "TsAggregationGroupCompact":
            self._data_lines.append(
                {
                    "type": "chart",
                    "value": self._data_fetcher.get_aggregation_group(
                        properties.get("aggregation_group")
                    ),
                }
            )

    def reset(self):
        """Reset story by removing all blocks.

        This function can be called to clear all blocks in the story
        and feed it again with new blocks.
        """
        self._data_lines = []

    def set_creation_date(self, creation_date):
        """Set the creation date of the story.

        Args:
            creation_date (str): string with the creation date of the story.
        """
        if creation_date:
            self._creation_date = creation_date

    def set_data_fetcher(self, data_fetcher):
        """Set the data fetcher.

        Args:
            data_fetcher (DataFetcher): set the data fetcher.
        """
        self._data_fetcher = data_fetcher

    def set_author(self, user):
        """Set the username of the user creating the story.

        Args:
            user (str): the username of the story's author.
        """
        if user:
            self._story_author = user
        else:
            self._story_author = "System"

    def set_exporter(self, user):
        """Sets the username of the person exporting the story.

        Args:
            user (str): the username of the user exporting the
                story.
        """
        if user:
            self._story_exporter = user

    def set_title(self, title):
        """Set the title of the story."""
        if title:
            self._story_title = title

    def __enter__(self):
        """Make it possible to use "with" statement."""
        self.reset()
        return self

    # pylint: disable=unused-argument
    def __exit__(self, exception_type, exception_value, traceback):
        """Make it possible to use "with" statement."""
        self.reset()


class DataFetcher(object):
    """A data fetcher interface."""

    def __init__(self):
        """Initialize the data fetcher."""
        self._sketch_id = 0

    def get_aggregation(self, agg_dict):
        """Returns an aggregation object from an aggregation dict.

        Args:
            agg_dict (dict): a dictionary containing information
                about the stored aggregation.

        Returns:
            A dict with metadata information as well as the aggregation
            object (instance of AggregationResult) from a saved aggregation
            or an empty dict if not found.
        """
        raise NotImplementedError

    def get_aggregation_group(self, agg_dict):
        """Returns an aggregation object from an aggregation group dict.

        Args:
            agg_dict (dict): a dictionary containing information
                about the stored aggregation group.

        Returns:
            A dict that contains metadata about the aggregation group
            as well as a chart object (instance of altair.Chart)
            with the combined chart object from the group.
        """
        raise NotImplementedError

    def get_view(self, view_dict):
        """Returns a data frame from a view dict.

        Args:
            view_dict (dict): a dictionary containing information
                about the stored view.

        Returns:
            A pandas DataFrame with the results from a view aggregation.
        """
        raise NotImplementedError

    def set_sketch_id(self, sketch_id):
        """Set the sketch id."""
        self._sketch_id = sketch_id
