# Copyright 2014 Google Inc. All rights reserved.
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
"""Datastore abstraction."""

import abc


class DataStore(object):
    """Abstract datastore."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def search(self, sketch_id, query_string, query_filter, query_dsl, indices,
               aggregations, return_results, return_fields, enable_scroll):
        """Return search results.

        Args:
            sketch_id: Integer of sketch primary key
            query: Query string
            query_filter: Dictionary containing filters to apply
            query_dsl: Dictionary containing Elasticsearch DSL query
            indices: List of indices to query
            aggregations: Dict of Elasticsearch aggregations
            return_results: Boolean indicating if results should be returned
            return_fields: List of fields to return
            enable_scroll: If Elasticsearch scroll API should be used
        """

    @abc.abstractmethod
    def get_event(self, searchindex_id, event_id):
        """Get single event from the datastore.

        Args:
            searchindex_id: String of ElasticSearch index id
            event_id: String of ElasticSearch event id
        """

    @abc.abstractmethod
    def set_label(self,
                  searchindex_id,
                  event_id,
                  event_type,
                  sketch_id,
                  user_id,
                  label,
                  toggle=False):
        """Add label to an event.

        Args:
            searchindex_id: String of ElasticSearch index id
            event_id: String of ElasticSearch event id
            sketch_id: Integer of sketch primary key
            user_id: Integer of user primary key
            label: String with the name of the label
            toggle: Optional boolean value if the label should be toggled
            (add/remove). The default is False.
        """
