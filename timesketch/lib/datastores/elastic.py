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
"""Elasticsearch datastore."""

from collections import Counter
import json
import logging

from uuid import uuid4

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from elasticsearch.exceptions import ConnectionError
from flask import abort

from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND

# Setup logging
es_logger = logging.getLogger(u'elasticsearch')
es_logger.addHandler(logging.NullHandler())
es_logger.setLevel(logging.WARNING)

ADD_LABEL_SCRIPT = """
if (ctx._source.timesketch_label == null) {
    ctx._source.timesketch_label = new ArrayList()
}
if( ! ctx._source.timesketch_label.contains (params.timesketch_label)) {
    ctx._source.timesketch_label.add(params.timesketch_label)
}
"""

TOGGLE_LABEL_SCRIPT = """
if (ctx._source.timesketch_label == null) {
    ctx._source.timesketch_label = new ArrayList()
}
if(ctx._source.timesketch_label.contains(params.timesketch_label)) {
    for (int i = 0; i < ctx._source.timesketch_label.size(); i++) {
      if (ctx._source.timesketch_label[i] == params.timesketch_label) {
        ctx._source.timesketch_label.remove(i)
      }
      i++;
    }
} else {
    ctx._source.timesketch_label.add(params.timesketch_label)
}
"""


class ElasticsearchDataStore(object):
    """Implements the datastore."""

    # Number of events to queue up when bulk inserting events.
    DEFAULT_FLUSH_INTERVAL = 1000
    DEFAULT_SIZE = 100
    DEFAULT_LIMIT = DEFAULT_SIZE  # Max events to return
    DEFAULT_FROM = 0
    DEFAULT_STREAM_LIMIT = 10000  # Max events to return when streaming results

    def __init__(self, host=u'127.0.0.1', port=9200):
        """Create a Elasticsearch client."""
        super(ElasticsearchDataStore, self).__init__()
        self.client = Elasticsearch([{u'host': host, u'port': port}])
        self.import_counter = Counter()
        self.import_events = []

    @staticmethod
    def _build_label_query(sketch_id, label_name):
        """Build Elasticsearch query for Timesketch labels.

        Args:
            sketch_id: Integer of sketch primary key.
            label_name: Name of the label to search for.

        Returns:
            Elasticsearch query as a dictionary.
        """
        query_dict = {
            u'query': {
                u'nested': {
                    u'query': {
                        u'bool': {
                            u'must': [{
                                u'term': {
                                    u'timesketch_label.name': label_name
                                }
                            }, {
                                u'term': {
                                    u'timesketch_label.sketch_id': sketch_id
                                }
                            }]
                        }
                    },
                    u'path': u'timesketch_label'
                }
            }
        }
        return query_dict

    @staticmethod
    def _build_events_query(events):
        """Build Elasticsearch query for one or more document ids.

        Args:
            events: List of Elasticsearch document IDs.

        Returns:
            Elasticsearch query as a dictionary.
        """
        events_list = [event[u'event_id'] for event in events]
        query_dict = {u'query': {u'ids': {u'values': events_list}}}
        return query_dict

    @staticmethod
    def _build_field_aggregator(field_name):
        """Build Elasticsearch query for aggregation based on field.

        Args:
            field_name: Field to aggregate.

        Returns:
            Elasticsearch aggregation as a dictionary.
        """
        field_aggregation = {
            u'field_aggregation': {
                u'terms': {
                    u'field': u'{0:s}.keyword'.format(field_name)
                }
            }
        }
        return field_aggregation

    def build_query(self,
                    sketch_id,
                    query_string,
                    query_filter,
                    query_dsl,
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
        if not query_dsl:
            if query_filter.get(u'star', None):
                query_dsl = self._build_label_query(sketch_id, u'__ts_star')

            if query_filter.get(u'events', None):
                events = query_filter[u'events']
                query_dsl = self._build_events_query(events)

            if not query_dsl:
                query_dsl = {
                    u'query': {
                        u'bool': {
                            u'must': [{
                                u'query_string': {
                                    u'query': query_string
                                }
                            }]
                        }
                    }
                }
            if query_filter.get(u'time_start', None):
                # TODO(jberggren): Add support for multiple time ranges.
                query_dsl[u'query'][u'bool'][u'filter'] = {
                    u'bool': {
                        u'should': [{
                            u'range': {
                                u'datetime': {
                                    u'gte': query_filter[u'time_start'],
                                    u'lte': query_filter[u'time_end']
                                }
                            }
                        }]
                    }
                }
            if query_filter.get(u'from', None):
                query_dsl[u'from'] = query_filter[u'from']
            if query_filter.get(u'size', None):
                query_dsl[u'size'] = query_filter[u'size']
            if query_filter.get(u'exclude', None):
                query_dsl[u'post_filter'] = {
                    u'bool': {
                        u'must_not': {
                            u'terms': {
                                u'data_type': query_filter[u'exclude']
                            }
                        }
                    }
                }
        else:
            query_dsl = json.loads(query_dsl)

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

        # Add any pre defined aggregations
        if aggregations:
            # post_filter happens after aggregation so we need to move the
            # filter to the query instead.
            if query_dsl.get(u'post_filter', None):
                query_dsl[u'query'][u'bool'][u'filter'] = query_dsl[
                    u'post_filter']
                query_dsl.pop(u'post_filter', None)
            query_dsl[u'aggregations'] = aggregations
        return query_dsl

    def search(self,
               sketch_id,
               query_string,
               query_filter,
               query_dsl,
               indices,
               count=False,
               aggregations=None,
               return_fields=None,
               enable_scroll=False):
        """Search ElasticSearch. This will take a query string from the UI
        together with a filter definition. Based on this it will execute the
        search request on ElasticSearch and get result back.

        Args:
            sketch_id: Integer of sketch primary key
            query_string: Query string
            query_filter: Dictionary containing filters to apply
            query_dsl: Dictionary containing Elasticsearch DSL query
            indices: List of indices to query
            count: Boolean indicating if we should only return result count
            aggregations: Dict of Elasticsearch aggregations
            return_fields: List of fields to return
            enable_scroll: If Elasticsearch scroll API should be used

        Returns:
            Set of event documents in JSON format
        """

        scroll_timeout = None
        if enable_scroll:
            scroll_timeout = u'1m'  # Default to 1 minute scroll timeout

        # Exit early if we have no indices to query
        if not indices:
            return {u'hits': {u'hits': [], u'total': 0}, u'took': 0}

        # Check if we have specific events to fetch and get indices.
        if query_filter.get(u'events', None):
            indices = {
                event[u'index']
                for event in query_filter[u'events']
                if event[u'index'] in indices
            }

        query_dsl = self.build_query(sketch_id, query_string, query_filter,
                                     query_dsl, aggregations)

        # Default search type for elasticsearch is query_then_fetch.
        search_type = u'query_then_fetch'

        # Only return how many documents matches the query.
        if count:
            del query_dsl[u'sort']
            count_result = self.client.count(
                body=query_dsl, index=list(indices))
            return count_result.get(u'count', 0)

        if not return_fields:
            # Suppress the lint error because elasticsearch-py adds parameters
            # to the function with a decorator and this makes pylint sad.
            # pylint: disable=unexpected-keyword-arg
            return self.client.search(
                body=query_dsl,
                index=list(indices),
                search_type=search_type,
                scroll=scroll_timeout)

        # Suppress the lint error because elasticsearch-py adds parameters
        # to the function with a decorator and this makes pylint sad.
        # pylint: disable=unexpected-keyword-arg
        return self.client.search(
            body=query_dsl,
            index=list(indices),
            search_type=search_type,
            _source_include=return_fields,
            scroll=scroll_timeout)

    def search_stream(
            self, sketch_id=None, query_string=None, query_filter=None,
            query_dsl=None, indices=None, return_fields=None):
        """Search ElasticSearch. This will take a query string from the UI
        together with a filter definition. Based on this it will execute the
        search request on ElasticSearch and get result back.

        Args :
            sketch_id: Integer of sketch primary key
            query_string: Query string
            query_filter: Dictionary containing filters to apply
            query_dsl: Dictionary containing Elasticsearch DSL query
            indices: List of indices to query
            return_fields: List of fields to return

        Returns:
            Generator of event documents in JSON format
        """

        if not query_filter.get(u'limit'):
            query_filter[u'limit'] = self.DEFAULT_STREAM_LIMIT

        result = self.search(
            sketch_id=sketch_id,
            query_string=query_string,
            query_dsl=query_dsl,
            query_filter=query_filter,
            indices=indices,
            return_fields=return_fields,
            enable_scroll=True)

        scroll_id = result[u'_scroll_id']
        scroll_size = result[u'hits'][u'total']

        for event in result[u'hits'][u'hits']:
            yield event

        while scroll_size > 0:
            # pylint: disable=unexpected-keyword-arg
            result = self.client.scroll(scroll_id=scroll_id, scroll=u'1m')
            scroll_id = result[u'_scroll_id']
            scroll_size = len(result[u'hits'][u'hits'])
            for event in result[u'hits'][u'hits']:
                yield event

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
                index=searchindex_id,
                id=event_id,
                _source_exclude=[u'timesketch_label'])
        except NotFoundError:
            abort(HTTP_STATUS_CODE_NOT_FOUND)

    def count(self, indices):
        """Count number of documents.

        Args:
            indices: List of indices.

        Returns:
            Number of documents.
        """
        if not indices:
            return 0
        result = self.client.count(index=indices)
        return result.get(u'count', 0)

    def set_label(self, searchindex_id, event_id, event_type, sketch_id,
                  user_id, label, toggle=False, single_update=True):
        """Set label on event in the datastore.

        Args:
            searchindex_id: String of ElasticSearch index id
            event_id: String of ElasticSearch event id
            event_type: String of ElasticSearch document type
            sketch_id: Integer of sketch primary key
            user_id: Integer of user primary key
            label: String with the name of the label
            toggle: Optional boolean value if the label should be toggled
            single_update: Boolean if the label should be indexed immediately.
            (add/remove). The default is False.

        Returns:
            Dict with updated document body, or None if this is a single update.
        """
        # Elasticsearch painless script.
        update_body = {
            u'script': {
                u'lang': u'painless',
                u'source': ADD_LABEL_SCRIPT,
                u'params': {
                    u'timesketch_label': {
                        u'name': str(label),
                        u'user_id': user_id,
                        u'sketch_id': sketch_id
                    }
                }
            }
        }

        if toggle:
            update_body[u'script'][u'source'] = TOGGLE_LABEL_SCRIPT

        if not single_update:
            script = update_body[u'script']
            return dict(
                source=script[u'source'], lang=script[u'lang'],
                params=script[u'params']
            )

        doc = self.client.get(index=searchindex_id, id=event_id)
        try:
            doc[u'_source'][u'timesketch_label']
        except KeyError:
            doc = {u'doc': {u'timesketch_label': []}}
            self.client.update(
                index=searchindex_id,
                doc_type=event_type,
                id=event_id,
                body=doc)

        self.client.update(
            index=searchindex_id,
            id=event_id,
            doc_type=event_type,
            body=update_body)

        return None

    def create_index(self, index_name=uuid4().hex, doc_type=u'generic_event'):
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

    def delete_index(self, index_name):
        """Delete Elasticsearch index.

        Args:
            index_name: Name of the index to delete.
        """
        if self.client.indices.exists(index_name):
            try:
                self.client.indices.delete(index=index_name)
            except ConnectionError as e:
                raise RuntimeError(
                    u'Unable to connect to Timesketch backend: {}'.format(e)
                )

    def import_event(
            self, index_name, event_type, event=None,
            event_id=None, flush_interval=DEFAULT_FLUSH_INTERVAL):
        """Add event to Elasticsearch.

        Args:
            flush_interval: Number of events to queue up before indexing
            index_name: Name of the index in Elasticsearch
            event_type: Type of event (e.g. plaso_event)
            event: Event dictionary
            event_id: Event Elasticsearch ID
        """
        if event:
            # Make sure we have decoded strings in the event dict.
            event = {
                k.decode(u'utf8'): (v.decode(u'utf8')
                                    if isinstance(v, basestring) else v)
                for k, v in event.items()
            }

            # Header needed by Elasticsearch when bulk inserting.
            header = {
                u'index': {
                    u'_index': index_name,
                    u'_type': event_type
                }
            }
            update_header = {
                u'update': {
                    u'_index': index_name,
                    u'_type': event_type,
                    u'_id': event_id
                }
            }

            if event_id:
                # Event has "lang" defined if there is a script used for import.
                if event.get(u'lang'):
                    event = {u'script': event}
                else:
                    event = {u'doc': event}
                header = update_header

            self.import_events.append(header)
            self.import_events.append(event)
            self.import_counter[u'events'] += 1

            if self.import_counter[u'events'] % int(flush_interval) == 0:
                self.client.bulk(body=self.import_events)
                self.import_events = []
        else:
            # Import the remaining events in the queue.
            if self.import_events:
                self.client.bulk(body=self.import_events)

        return self.import_counter[u'events']

    def flush_queued_events(self):
        if self.import_events:
            self.client.bulk(body=self.import_events)

    @property
    def version(self):
        """Get Elasticsearch version.

        Returns:
          Version number as a string.
        """
        version_info = self.client.info().get(u'version')
        return version_info.get(u'number')
