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
    EXPORT_FORMAT = ''

    def __init__(self):
        """Initialize the exporter."""
        self._data_lines = []
        self._data_fetcher = None

    @property
    def data(self):
        """Returns the data."""
        return self.export_story()

    def export_story(self):
        """Export the story in the format."""
        raise NotImplementedError

    def from_string(self, json_string):
        """Feed the exporter with a JSON string."""
        blocks = json.loads(json_string)
        if not isinstance(blocks, (list, tuple)):
            return

        for block in blocks:
            self.from_dict(block)

    def from_dict(self, block):
        """Feed the exporter with a single block dict."""
        component = block.get('componentName', 'N/A')
        properties = block.get('componentProps', {})

        if not self._data_fetcher:
            return

        if not component:
            self._data_lines.append(block.get('content', ''))
        elif component == 'TsViewEventList':
            self._data_lines.append(
                self._data_fetcher.get_view(properties.get('view')))
        elif component == 'TsAggregationEventList':
            self._data_lines.append(
                self._data_fetcher.get_aggregation(
                    properties.get('aggregation')))

    def reset(self):
        """Reset the story."""
        self._data_lines = []

    def set_data_fetcher(self, data_fetcher):
        """Set the data fetcher.

        Args:
            data_fetcher (DataFetcher): set the data fetcher.
        """
        self._data_fetcher = data_fetcher

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
        """Returns a data frame from an aggregation dict.

        Args:
            agg_dict (dict): a dictionary containing information
                about the stored aggregation.

        Returns:
            A pandas DataFrame with the results from a saved aggregation.
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
