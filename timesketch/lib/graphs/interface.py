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
"""Interface for graphs."""

from flask import current_app
from timesketch.lib.datastores.elastic import ElasticsearchDataStore


class BaseGraph(object):
    """Base class for a graph."""

    # Name that the graph will be registered as.
    NAME = 'name'

    def __init__(self):
        """Initialize the chart object.

        Args:

        Raises:
            RuntimeError if values or encoding is missing from data.
        """
        self.datastore = ElasticsearchDataStore(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])

    def event_stream(
            self, query_string=None, query_filter=None, query_dsl=None,
            indices=None, return_fields=None, scroll=True):
        """Search ElasticSearch.

        Args:
            query_string: Query string.
            query_filter: Dictionary containing filters to apply.
            query_dsl: Dictionary containing Elasticsearch DSL query.
            indices: List of indices to query.
            return_fields: List of fields to return.
            scroll: Boolean determining whether we support scrolling searches
                or not. Defaults to True.

        Returns:
            Generator of Event objects.

        Raises:
            ValueError: if neither query_string or query_dsl is provided.
        """
        if not (query_string or query_dsl):
            raise ValueError('Both query_string and query_dsl are missing')

        # Make sure we always return tag, human_readable and emoji attributes.
        return_fields.extend(['tag', 'human_readable', '__ts_emojis'])
        return_fields = list(set(return_fields))

        # Refresh the index to make sure it is searchable.
        for index in indices:
            self.datastore.client.indices.refresh(index=index)

        event_generator = self.datastore.search_stream(
            query_string=query_string,
            query_filter={},
            query_dsl=query_dsl,
            indices=indices,
            return_fields=return_fields,
            enable_scroll=scroll,
        )
        return event_generator

    def generate(self):
        """Entry point for the graph."""
        raise NotImplementedError
