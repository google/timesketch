# Copyright 2015 Google Inc. All rights reserved.
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
"""ElasticSearch datastore."""

import json
import logging

from uuid import uuid4

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.exceptions import ConnectionError
from flask import abort

from timesketch.lib import datastore
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND


# Setup logging
es_logger = logging.getLogger(u'elasticsearch')
es_logger.addHandler(logging.NullHandler())


class ElasticSearchDataStore(datastore.DataStore):
    """Implements the datastore."""
    def __init__(self, host=u'127.0.0.1', port=9200):
        """Create a Elasticsearch client."""
        super(ElasticSearchDataStore, self).__init__()
        self.client = Elasticsearch([
            {u'host': host, u'port': port}
        ])

    @staticmethod
    def build_query(sketch_id, query_string, query_filter, query_dsl,
            aggregations=None):
        """Build Elasticsearch DSL query.

        Args:
            sketch_id: Integer of sketch primary key
            query_string: Query string
            query_filter: Dictionary containing filters to apply
            query_dsl: Dictionary containing Elasticsearch DSL query
            aggregations: Dict of Elasticsearch aggregations

        Returns:
            Elasticsearch DSL query as a dictionary
        """

        # If we don't have a Query DSL from the user construct a query_string
        # query DSL.
        if not query_dsl:
            query_dsl = {
                u'query': {
                    u'filtered': {
                        u'query': {
                            u'query_string': {
                                u'query': query_string
                            }
                        }
                    }
                }
            }

        # Make sure we are sorting.
        if not query_dsl.get(u'sort', None):
            query_dsl[u'sort'] = {
                u'datetime': query_filter.get(u'order', u'asc')
            }

        # Remove any aggregation coming from user supplied Query DSL. We have
        # no way to display this data in a good way today.
        # TODO: Revisit this and figure out if we can display the data.
        if query_dsl.get(u'aggregations', None):
            del query_dsl[u'aggregations']

    def search(
            self, sketch_id, query_string, query_filter, query_dsl, indices,
            aggregations=None, return_results=True):
        """Search ElasticSearch. This will take a query string from the UI
        together with a filter definition. Based on this it will execute the
        search request on ElasticSearch and get result back.

        Args:
            sketch_id: Integer of sketch primary key
            query_string: Query string
            query_filter: Dictionary containing filters to apply
            query_dsl: Dictionary containing Elasticsearch DSL query
            indices: List of indices to query
            aggregations: Dict of Elasticsearch aggregations
            return_results: Boolean indicating if results should be returned

        Returns:
            Set of event documents in JSON format
        """

        # Limit the number of returned documents.
        DEFAULT_LIMIT = 500  # Maximum events to return
        LIMIT_RESULTS = query_filter.get(u'limit', DEFAULT_LIMIT)

        if query_dsl:
            return self.client.search(
                body=json.loads(query_dsl), index=list(indices),
                size=LIMIT_RESULTS, _source_include=[
                    u'datetime', u'timestamp', u'message', u'timestamp_desc',
                    u'timesketch_label', u'tag'])

        if not indices:
            return {u'hits': {u'hits': [], u'total': 0}, u'took': 0}

        if not query_string:
            query_string = u''

        query_dict = {
            u'query': {
                u'filtered': {
                    u'query': {
                        u'query_string': {
                            u'query': query_string
                        }
                    }
                }
            },
            u'sort': {
                u'datetime': query_filter.get(u'order', u'asc')
            }
        }

        if query_filter.get(u'star', None):
            del query_dict[u'query'][u'filtered'][u'query']
            query_dict[u'query'][u'filtered'][u'filter'] = {
                u'nested': {
                    u'path': u'timesketch_label',
                    u'filter': {
                        u'bool': {
                            u'must': [
                                {
                                    u'term': {
                                        u'timesketch_label.name': u'__ts_star'
                                    }
                                },
                                {
                                    u'term': {
                                        u'timesketch_label.sketch_id': sketch_id
                                    }
                                }
                            ]
                        }
                    }
                }
            }

        if query_filter.get(u'events', None):
            events = query_filter[u'events']
            indices = {event[u'index'] for event in events}
            events_list = [event[u'event_id'] for event in events]
            del query_dict[u'query']
            query_dict[u'query'] = {
                u'ids': {
                    u'values': events_list
                }
            }

        if query_filter.get(u'time_start', None):
            query_dict[u'query'][u'filtered'][u'filter'] = {
                u'range': {
                    u'datetime': {
                        u'gte': query_filter[u'time_start'],
                        u'lte': query_filter[u'time_end']
                    }
                }
            }

        if query_filter.get(u'exclude', None):
            query_dict[u'filter'] = {
                u'not': {
                    u'terms': {
                        u'data_type': query_filter[u'exclude']
                    }
                }
            }

        data_type_aggregation = {
            u'data_type': {
                u'terms': {
                    u'field': u'data_type',
                    u'size': 0}
            }
        }

        if aggregations:
            if isinstance(aggregations, dict):
                if query_filter.get(u'exclude', None):
                    aggregations = {
                        u'exclude': {
                            u'filter': {
                                u'not': {
                                    u'terms': {
                                        u'data_type': query_filter[u'exclude']
                                    }
                                }
                            },
                            u'aggregations': aggregations
                        },
                        u'data_type': data_type_aggregation[u'data_type']
                    }
                query_dict[u'aggregations'] = aggregations
        else:
            query_dict[u'aggregations'] = data_type_aggregation

        # Default search type for elasticsearch is query_then_fetch.
        if return_results:
            search_type = u'query_then_fetch'
        else:
            search_type = u'count'

        # Suppress the lint error because elasticsearch-py adds parameters
        # to the function with a decorator and this makes pylint sad.
        # pylint: disable=unexpected-keyword-arg
        return self.client.search(
            body=query_dict, index=list(indices), size=LIMIT_RESULTS,
            search_type=search_type, _source_include=[
                u'datetime', u'timestamp', u'message', u'timestamp_desc',
                u'timesketch_label', u'tag'])

    def get_event(self, searchindex_id, event_id):
        """Get one event from the datastore.

        Args:
            searchindex_id: String of ElasticSearch index id
            event_id: String of ElasticSearch event id

        Returns:
            Event document in JSON format
        """
        try:
            # Suppress the lint error because elasticsearch-py adds parameters
            # to the function with a decorator and this makes pylint sad.
            # pylint: disable=unexpected-keyword-arg
            return self.client.get(
                index=searchindex_id, id=event_id,
                _source_exclude=[u'timesketch_label'])
        except NotFoundError:
            abort(HTTP_STATUS_CODE_NOT_FOUND)

    def set_label(
            self, searchindex_id, event_id, event_type, sketch_id, user_id,
            label, toggle=False):
        """Set label on event in the datastore.

        Args:
            searchindex_id: String of ElasticSearch index id
            event_id: String of ElasticSearch event id
            event_type: String of ElasticSearch document type
            sketch_id: Integer of sketch primary key
            user_id: Integer of user primary key
            label: String with the name of the label
            toggle: Optional boolean value if the label should be toggled
            (add/remove). The default is False.
        """
        doc = self.client.get(index=searchindex_id, id=event_id)
        try:
            doc[u'_source'][u'timesketch_label']
        except KeyError:
            doc = {u'doc': {u'timesketch_label': []}}
            self.client.update(
                index=searchindex_id, doc_type=event_type, id=event_id,
                body=doc)

        if toggle:
            script_string = (
                u'if(ctx._source.timesketch_label.contains'
                u'(timesketch_label)) {ctx._source.timesketch_label'
                u'.remove(timesketch_label)} else {ctx._source.'
                u'timesketch_label += timesketch_label}')
        else:
            script_string = (
                u'if( ! ctx._source.timesketch_label.contains'
                u'(timesketch_label)) {ctx._source.timesketch_label'
                u'+= timesketch_label}')
        script = {
            u'script': script_string,
            u'params': {
                u'timesketch_label': {
                    u'name': str(label),
                    u'user_id': user_id,
                    u'sketch_id': sketch_id
                }
            }
        }
        self.client.update(
            index=searchindex_id, id=event_id, doc_type=event_type,
            body=script)

    def create_index(
            self, index_name=uuid4().hex, doc_type=u'generic_event'):
        """Create index with Timesketch settings.

        Args:
            index_name: Name of the index. Default is a generated UUID.
            doc_type: Name of the document type. Default id generic_event.

        Returns:
            Index name in string format.
            Document type in string format.
        """
        _document_mapping = {
            doc_type: {
                u'properties': {
                    u'timesketch_label': {
                        u'type': u'nested'
                    }
                }
            }
        }

        if not self.client.indices.exists(index_name):
            try:
                self.client.indices.create(
                    index=index_name, body={u'mappings': _document_mapping})
            except ConnectionError:
                raise RuntimeError(u'Unable to connect to Timesketch backend.')
        # We want to return unicode here to keep SQLalchemy happy.
        index_name = unicode(index_name.decode(encoding=u'utf-8'))
        doc_type = unicode(doc_type.decode(encoding=u'utf-8'))
        return index_name, doc_type
