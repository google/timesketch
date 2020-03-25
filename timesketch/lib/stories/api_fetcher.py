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

from flask import current_app
import pandas as pd

from timesketch.lib.stories import interface

from timesketch.lib.aggregators import manager as aggregator_manager
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.models.sketch import Aggregation
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import View


class ApiDataFetcher(interface.DataFetcher):
    """Data Fetcher for an API story exporter."""

    def __init__(self):
        """Initialize the data fetcher."""
        super(ApiDataFetcher, self).__init__()
        self._datastore = ElasticsearchDataStore(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])

    def get_aggregation(self, agg_dict):
        """Returns an aggregation object from an aggregation dict.

        Args:
            agg_dict (dict): a dictionary containing information
                about the stored aggregation.

        Returns:
            An aggregation object (instance of AggregationResult) from a
            saved aggregation or None if not found.
        """
        aggregation_id = agg_dict.get('id')
        if not aggregation_id:
            return None

        aggregation = Aggregation.query.get(aggregation_id)
        if not aggregation:
            return None

        try:
            agg_class = aggregator_manager.AggregatorManager.get_aggregator(
                aggregation.agg_type)
        except KeyError:
            return None

        if not agg_class:
            return pd.DataFrame()
        aggregator = agg_class(sketch_id=self._sketch_id)
        return aggregator.run(aggregation.parameters)

    def get_view(self, view_dict):
        """Returns a data frame from a view dict.

        Args:
            view_dict (dict): a dictionary containing information
                about the stored view.

        Returns:
            A pandas DataFrame with the results from a view aggregation.
        """
        view_id = view_dict.get('id')
        if not view_id:
            return pd.DataFrame()

        view = View.query.get(view_id)
        if not view:
            return pd.DataFrame()

        if not view.query_string and not view.query_dsl:
            return pd.DataFrame()

        query_filter = view.query_filter
        if query_filter and isinstance(query_filter, str):
            query_filter = json.loads(query_filter)
        elif not query_filter:
            query_filter = {'indices': '_all', 'size': 100}

        if view.query_dsl:
            query_dsl = json.loads(view.query_dsl)
        else:
            query_dsl = None

        sketch = Sketch.query.get_with_acl(self._sketch_id)
        sketch_indices = [
            t.searchindex.index_name
            for t in sketch.active_timelines
        ]

        results = self._datastore.search_stream(
            sketch_id=self._sketch_id,
            query_string=view.query_string,
            query_filter=query_filter,
            query_dsl=query_dsl,
            indices=sketch_indices,
        )
        result_list = [x.get('_source') for x in results]
        return pd.DataFrame(result_list)
