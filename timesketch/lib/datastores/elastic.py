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
from __future__ import unicode_literals

from collections import Counter
import codecs
import json
import logging
import socket

from uuid import uuid4

import six

from dateutil import parser, relativedelta
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionTimeout
from elasticsearch.exceptions import NotFoundError
from elasticsearch.exceptions import RequestError
# pylint: disable=redefined-builtin
from elasticsearch.exceptions import ConnectionError
from flask import abort

from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND

# Setup logging
es_logger = logging.getLogger('timesketch.elasticsearch')
es_logger.setLevel(logging.WARNING)

UPDATE_LABEL_SCRIPT = """
if (ctx._source.timesketch_label == null) {
    ctx._source.timesketch_label = new ArrayList()
}
if (params.remove == true) {
    ctx._source.timesketch_label.removeIf(label -> label.name == params.timesketch_label.name && label.sketch_id == params.timesketch_label.sketch_id);
} else {
    if( ! ctx._source.timesketch_label.contains (params.timesketch_label)) {
        ctx._source.timesketch_label.add(params.timesketch_label)
    }
}
"""

TOGGLE_LABEL_SCRIPT = """
if (ctx._source.timesketch_label == null) {
    ctx._source.timesketch_label = new ArrayList()
}
boolean removedLabel = ctx._source.timesketch_label.removeIf(label -> label.name == params.timesketch_label.name && label.sketch_id == params.timesketch_label.sketch_id);
if (!removedLabel) {
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
    DEFAULT_STREAM_LIMIT = 5000 # Max events to return when streaming results

    def __init__(self, host='127.0.0.1', port=9200):
        """Create a Elasticsearch client."""
        super().__init__()
        self._error_container = {}
        self.client = Elasticsearch([{'host': host, 'port': port}])
        self.import_counter = Counter()
        self.import_events = []

    @staticmethod
    def _build_labels_query(sketch_id, labels):
        """Build Elasticsearch query for Timesketch labels.

        Args:
            sketch_id: Integer of sketch primary key.
            labels: List of label names.

        Returns:
            Elasticsearch query as a dictionary.
        """
        label_query = {
            'bool': {
                'must': []
            }
        }

        for label in labels:
            nested_query = {
                'nested': {
                    'query': {
                        'bool': {
                            'must': [{
                                'term': {
                                    'timesketch_label.name.keyword': label
                                }
                            }, {
                                'term': {
                                    'timesketch_label.sketch_id': sketch_id
                                }
                            }]
                        }
                    },
                    'path': 'timesketch_label'
                }
            }
            label_query['bool']['must'].append(nested_query)
        return label_query

    @staticmethod
    def _build_events_query(events):
        """Build Elasticsearch query for one or more document ids.

        Args:
            events: List of Elasticsearch document IDs.

        Returns:
            Elasticsearch query as a dictionary.
        """
        events_list = [event['event_id'] for event in events]
        query_dict = {'query': {'ids': {'values': events_list}}}
        return query_dict

    @staticmethod
    def _convert_to_time_range(interval):
        """Convert an interval timestamp into start and end dates.

        Args:
            interval: Time frame representation

        Returns:
            Start timestamp in string format.
            End timestamp in string format.
        """
        # return ('2018-12-05T00:00:00', '2018-12-05T23:59:59')
        TS_FORMAT = '%Y-%m-%dT%H:%M:%S'
        get_digits = lambda s: int(''.join(filter(str.isdigit, s)))
        get_alpha = lambda s: ''.join(filter(str.isalpha, s))

        ts_parts = interval.split(' ')
        # The start date could be 1 or 2 first items
        start = ' '.join(ts_parts[0:len(ts_parts)-2])
        minus = get_digits(ts_parts[-2])
        plus = get_digits(ts_parts[-1])
        interval = get_alpha(ts_parts[-1])

        start_ts = parser.parse(start)

        rd = relativedelta.relativedelta
        if interval == 's':
            start_range = start_ts - rd(seconds=minus)
            end_range = start_ts + rd(seconds=plus)
        elif interval == 'm':
            start_range = start_ts - rd(minutes=minus)
            end_range = start_ts + rd(minutes=plus)
        elif interval == 'h':
            start_range = start_ts - rd(hours=minus)
            end_range = start_ts + rd(hours=plus)
        elif interval == 'd':
            start_range = start_ts - rd(days=minus)
            end_range = start_ts + rd(days=plus)
        else:
            raise RuntimeError('Unable to parse the timestamp: '
                               + str(interval))

        return start_range.strftime(TS_FORMAT), end_range.strftime(TS_FORMAT)

    def build_query(self, sketch_id, query_string, query_filter, query_dsl=None,
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

        if query_dsl:
            if not isinstance(query_dsl, dict):
                query_dsl = json.loads(query_dsl)
            # Remove any aggregation coming from user supplied Query DSL.
            # We have no way to display this data in a good way today.
            if query_dsl.get('aggregations', None):
                del query_dsl['aggregations']
            return query_dsl

        if query_filter.get('events', None):
            events = query_filter['events']
            return self._build_events_query(events)

        query_dsl = {
            'query': {
                'bool': {
                    'must': [],
                    'must_not': [],
                    'filter': []
                }
            }
        }

        # TODO: Remove when old UI has been deprecated.
        if query_filter.get('star', None):
            label_query = self._build_labels_query(sketch_id, ['__ts_star'])
            query_string = '*'
            query_dsl['query']['bool']['must'].append(label_query)

        # TODO: Remove when old UI has been deprecated.
        if query_filter.get('time_start', None):
            query_dsl['query']['bool']['filter'] = [{
                'bool': {
                    'should': [{
                        'range': {
                            'datetime': {
                                'gte': query_filter['time_start'],
                                'lte': query_filter['time_end']
                            }
                        }
                    }]
                }
            }]

        if query_string:
            query_dsl['query']['bool']['must'].append(
                {'query_string': {'query': query_string}})

        # New UI filters
        if query_filter.get('chips', None):
            labels = []
            must_filters = query_dsl['query']['bool']['must']
            must_not_filters = query_dsl['query']['bool']['must_not']
            datetime_ranges = {
                'bool': {
                    'should': [],
                    'minimum_should_match': 1
                }
            }

            for chip in query_filter['chips']:
                # Exclude chips that the user disabled
                if not chip.get('active', True):
                    continue

                if chip['type'] == 'label':
                    labels.append(chip['value'])

                elif chip['type'] == 'term':
                    term_filter = {
                        'match_phrase': {
                            '{}'.format(chip['field']): {
                                'query': "{}".format(chip['value'])
                            }
                        }
                    }

                    if chip['operator'] == 'must':
                        must_filters.append(term_filter)

                    elif chip['operator'] == 'must_not':
                        must_not_filters.append(term_filter)

                elif chip['type'].startswith('datetime'):
                    range_filter = lambda start, end: {
                        'range': {
                            'datetime': {
                                'gte': start,
                                'lte': end
                            }
                        }
                    }
                    if chip['type'] == 'datetime_range':
                        start, end = chip['value'].split(',')
                    elif chip['type'] == 'datetime_interval':
                        start, end = self._convert_to_time_range(chip['value'])
                    else:
                        continue
                    datetime_ranges['bool']['should'].append(
                        range_filter(start, end))

            label_filter = self._build_labels_query(sketch_id, labels)
            must_filters.append(label_filter)
            must_filters.append(datetime_ranges)

        # Pagination
        if query_filter.get('from', None):
            query_dsl['from'] = query_filter['from']

        # Number of events to return
        if query_filter.get('size', None):
            query_dsl['size'] = query_filter['size']

        # Make sure we are sorting.
        if not query_dsl.get('sort', None):
            query_dsl['sort'] = {
                'datetime': query_filter.get('order', 'asc')
            }

        # Add any pre defined aggregations
        if aggregations:
            # post_filter happens after aggregation so we need to move the
            # filter to the query instead.
            if query_dsl.get('post_filter', None):
                query_dsl['query']['bool']['filter'] = query_dsl[
                    'post_filter']
                query_dsl.pop('post_filter', None)
            query_dsl['aggregations'] = aggregations

        return query_dsl

    def search(self, sketch_id, query_string, query_filter, query_dsl, indices,
               count=False, aggregations=None, return_fields=None,
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
            scroll_timeout = '1m'  # Default to 1 minute scroll timeout

        # Exit early if we have no indices to query
        if not indices:
            return {'hits': {'hits': [], 'total': 0}, 'took': 0}

        # Check if we have specific events to fetch and get indices.
        if query_filter.get('events', None):
            indices = {
                event['index']
                for event in query_filter['events']
                if event['index'] in indices
            }

        query_dsl = self.build_query(sketch_id, query_string, query_filter,
                                     query_dsl, aggregations)

        # Default search type for elasticsearch is query_then_fetch.
        search_type = 'query_then_fetch'

        # Only return how many documents matches the query.
        if count:
            del query_dsl['sort']
            count_result = self.client.count(
                body=query_dsl, index=list(indices))
            return count_result.get('count', 0)

        if not return_fields:
            # Suppress the lint error because elasticsearch-py adds parameters
            # to the function with a decorator and this makes pylint sad.
            # pylint: disable=unexpected-keyword-arg
            return self.client.search(
                body=query_dsl,
                index=list(indices),
                search_type=search_type,
                scroll=scroll_timeout)

        # The argument " _source_include" changed to "_source_includes" in
        # ES version 7. This check add support for both version 6 and 7 clients.
        # pylint: disable=unexpected-keyword-arg
        try:
            if self.version.startswith('6'):
                _search_result = self.client.search(
                    body=query_dsl,
                    index=list(indices),
                    search_type=search_type,
                    _source_include=return_fields,
                    scroll=scroll_timeout)
            else:
                _search_result = self.client.search(
                    body=query_dsl,
                    index=list(indices),
                    search_type=search_type,
                    _source_includes=return_fields,
                    scroll=scroll_timeout)
        except RequestError as e:
            root_cause = e.info.get('error', {}).get('root_cause')
            if root_cause:
                error_items = []
                for cause in root_cause:
                    error_items.append(
                        '[{0:s}] {1:s}'.format(
                            cause.get('type', ''), cause.get('reason', '')))
                cause = ', '.join(error_items)
            else:
                cause = str(e)

            es_logger.error(
                'Unable to run search query: {0:s}'.format(cause),
                exc_info=True)
            raise ValueError(cause) from e

        return _search_result

    def search_stream(self, sketch_id=None, query_string=None,
                      query_filter=None, query_dsl=None, indices=None,
                      return_fields=None, enable_scroll=True):
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
            enable_scroll: Boolean determing whether scrolling is enabled.

        Returns:
            Generator of event documents in JSON format
        """

        if not query_filter.get('size'):
            query_filter['size'] = self.DEFAULT_STREAM_LIMIT

        if not query_filter.get('terminate_after'):
            query_filter['terminate_after'] = self.DEFAULT_STREAM_LIMIT

        result = self.search(
            sketch_id=sketch_id,
            query_string=query_string,
            query_dsl=query_dsl,
            query_filter=query_filter,
            indices=indices,
            return_fields=return_fields,
            enable_scroll=enable_scroll)

        if enable_scroll:
            scroll_id = result['_scroll_id']
            scroll_size = result['hits']['total']
        else:
            scroll_id = None
            scroll_size = 0

        # Elasticsearch version 7.x returns total hits as a dictionary.
        # TODO: Refactor when version 6.x has been deprecated.
        if isinstance(scroll_size, dict):
            scroll_size = scroll_size.get('value', 0)

        for event in result['hits']['hits']:
            yield event

        while scroll_size > 0:
            # pylint: disable=unexpected-keyword-arg
            result = self.client.scroll(scroll_id=scroll_id, scroll='5m')
            scroll_id = result['_scroll_id']
            scroll_size = len(result['hits']['hits'])
            for event in result['hits']['hits']:
                yield event

    def get_filter_labels(self, sketch_id, indices):
        """Aggregate labels for a sketch.

        Args:
            sketch_id: The Sketch ID
            indices: List of indices to aggregate on

        Returns:
            List with label names.
        """
        # This is a workaround to return all labels by setting the max buckets
        # to something big. If a sketch has more than this amount of labels
        # the list will be incomplete but it should be uncommon to have >10k
        # labels in a sketch.
        max_labels = 10000

        # pylint: disable=line-too-long
        aggregation = {
            'aggs': {
                'nested': {
                    'nested': {
                        'path': 'timesketch_label'
                    },
                    'aggs': {
                        'inner': {
                            'filter': {
                                'bool': {
                                    'must': [{
                                        'term': {
                                            'timesketch_label.sketch_id': sketch_id
                                        }
                                    }]
                                }
                            },
                            'aggs': {
                                'labels': {
                                    'terms': {
                                        'size': max_labels,
                                        'field': 'timesketch_label.name.keyword'
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        labels = []
        # pylint: disable=unexpected-keyword-arg
        result = self.client.search(index=indices, body=aggregation, size=0)
        buckets = result.get(
            'aggregations', {}).get('nested', {}).get('inner', {}).get(
                'labels', {}).get('buckets', [])
        for bucket in buckets:
            # Filter out special labels like __ts_star etc.
            if bucket['key'].startswith('__'):
                continue
            labels.append(bucket['key'])
        return labels

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
            if self.version.startswith('6'):
                event = self.client.get(
                    index=searchindex_id,
                    id=event_id,
                    doc_type='_all',
                    _source_exclude=['timesketch_label'])
            else:
                event = self.client.get(
                    index=searchindex_id,
                    id=event_id,
                    doc_type='_all',
                    _source_excludes=['timesketch_label'])

            return event

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
        try:
            result = self.client.count(index=indices)
        except (NotFoundError, RequestError):
            es_logger.error(
                'Unable to count indexes (index not found)',
                exc_info=True)
            return 0
        return result.get('count', 0)

    def set_label(self, searchindex_id, event_id, event_type, sketch_id,
                  user_id, label, toggle=False, remove=False,
                  single_update=True):
        """Set label on event in the datastore.

        Args:
            searchindex_id: String of ElasticSearch index id
            event_id: String of ElasticSearch event id
            event_type: String of ElasticSearch document type
            sketch_id: Integer of sketch primary key
            user_id: Integer of user primary key
            label: String with the name of the label
            remove: Optional boolean value if the label should be removed
            toggle: Optional boolean value if the label should be toggled
            single_update: Boolean if the label should be indexed immediately.

        Returns:
            Dict with updated document body, or None if this is a single update.
        """
        # Elasticsearch painless script.
        update_body = {
            'script': {
                'lang': 'painless',
                'source': UPDATE_LABEL_SCRIPT,
                'params': {
                    'timesketch_label': {
                        'name': str(label),
                        'user_id': user_id,
                        'sketch_id': sketch_id
                    },
                    remove: remove
                }
            }
        }

        if toggle:
            update_body['script']['source'] = TOGGLE_LABEL_SCRIPT

        if not single_update:
            script = update_body['script']
            return dict(
                source=script['source'], lang=script['lang'],
                params=script['params']
            )

        doc = self.client.get(
            index=searchindex_id, id=event_id, doc_type='_all')
        try:
            doc['_source']['timesketch_label']
        except KeyError:
            doc = {'doc': {'timesketch_label': []}}
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

    def create_index(self, index_name=uuid4().hex, doc_type='generic_event'):
        """Create index with Timesketch settings.

        Args:
            index_name: Name of the index. Default is a generated UUID.
            doc_type: Name of the document type. Default id generic_event.

        Returns:
            Index name in string format.
            Document type in string format.
        """
        _document_mapping = {
            'properties': {
                'timesketch_label': {
                    'type': 'nested'
                },
                'datetime': {
                    'type': 'date'
                }
            }
        }

        # TODO: Remove when we deprecate Elasticsearch version 6.x
        if self.version.startswith('6'):
            _document_mapping = {doc_type: _document_mapping}

        if not self.client.indices.exists(index_name):
            try:
                self.client.indices.create(
                    index=index_name, body={'mappings': _document_mapping})
            except ConnectionError as e:
                raise RuntimeError(
                    'Unable to connect to Timesketch backend.') from e
            except RequestError:
                index_exists = self.client.indices.exists(index_name)
                es_logger.warning(
                    'Attempting to create an index that already exists '
                    '({0:s} - {1:s})'.format(index_name, str(index_exists)))

        # We want to return unicode here to keep SQLalchemy happy.
        if six.PY2:
            if not isinstance(index_name, six.text_type):
                index_name = codecs.decode(index_name, 'utf-8')

            if not isinstance(doc_type, six.text_type):
                doc_type = codecs.decode(doc_type, 'utf-8')

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
                    'Unable to connect to Timesketch backend: {}'.format(e)
                ) from e

    def import_event(self, index_name, event_type, event=None, event_id=None,
                     flush_interval=DEFAULT_FLUSH_INTERVAL):
        """Add event to Elasticsearch.

        Args:
            index_name: Name of the index in Elasticsearch
            event_type: Type of event (e.g. plaso_event)
            event: Event dictionary
            event_id: Event Elasticsearch ID
            flush_interval: Number of events to queue up before indexing
        """
        if event:
            for k, v in event.items():
                if not isinstance(k, six.text_type):
                    k = codecs.decode(k, 'utf8')

                # Make sure we have decoded strings in the event dict.
                if isinstance(v, six.binary_type):
                    v = codecs.decode(v, 'utf8')

                event[k] = v

            # Header needed by Elasticsearch when bulk inserting.
            header = {
                'index': {
                    '_index': index_name,
                }
            }
            update_header = {
                'update': {
                    '_index': index_name,
                    '_id': event_id
                }
            }

            # TODO: Remove when we deprecate Elasticsearch version 6.x
            if self.version.startswith('6'):
                header['index']['_type'] = event_type
                update_header['update']['_type'] = event_type

            if event_id:
                # Event has "lang" defined if there is a script used for import.
                if event.get('lang'):
                    event = {'script': event}
                else:
                    event = {'doc': event}
                header = update_header

            self.import_events.append(header)
            self.import_events.append(event)
            self.import_counter['events'] += 1

            if self.import_counter['events'] % int(flush_interval) == 0:
                _ = self.flush_queued_events()
                self.import_events = []
        else:
            # Import the remaining events in the queue.
            if self.import_events:
                _ = self.flush_queued_events()

        return self.import_counter['events']

    def flush_queued_events(self):
        """Flush all queued events.

        Returns:
            dict: A dict object that contains the number of events
                that were sent to Elastic as well as information
                on whether there were any errors, and what the
                details of these errors if any.
        """
        if not self.import_events:
            return {}

        return_dict = {
            'number_of_events': len(self.import_events) / 2,
            'total_events': self.import_counter['events'],
        }

        try:
            results = self.client.bulk(body=self.import_events)
        except (ConnectionTimeout, socket.timeout):
            # TODO: Add a retry here.
            es_logger.error('Unable to add events', exc_info=True)

        errors_in_upload = results.get('errors', False)
        return_dict['errors_in_upload'] = errors_in_upload

        if errors_in_upload:
            items = results.get('items', [])
            return_dict['errors'] = []

            es_logger.error('Errors while attempting to upload events.')
            for item in items:
                index = item.get('index', {})
                index_name = index.get('_index', 'N/A')

                _ = self._error_container.setdefault(
                    index_name, {
                        'errors': [],
                        'types': Counter(),
                        'details': Counter()
                    }
                )

                error_counter = self._error_container[index_name]['types']
                error_detail_counter = self._error_container[index_name][
                    'details']
                error_list = self._error_container[index_name]['errors']

                error = index.get('error', {})
                status_code = index.get('status', 0)
                doc_id = index.get('_id', '(unable to get doc id)')
                caused_by = error.get('caused_by', {})

                caused_reason = caused_by.get(
                    'reason', 'Unkown Detailed Reason')

                error_counter[error.get('type')] += 1
                detail_msg = '{0:s}/{1:s}'.format(
                    caused_by.get('type', 'Unknown Detailed Type'),
                    ' '.join(caused_reason.split()[:5])
                )
                error_detail_counter[detail_msg] += 1

                error_msg = '<{0:s}> {1:s} [{2:s}/{3:s}]'.format(
                    error.get('type', 'Unknown Type'),
                    error.get('reason', 'No reason given'),
                    caused_by.get('type', 'Unknown Type'),
                    caused_reason,
                )
                error_list.append(error_msg)
                try:
                    es_logger.error(
                        'Unable to upload document: {0:s} to index {1:s} - '
                        '[{2:d}] {3:s}'.format(
                            doc_id, index_name, status_code, error_msg))
                # We need to catch all exceptions here, since this is a crucial
                # call that we do not want to break operation.
                except Exception:  # pylint: disable=broad-except
                    es_logger.error(
                        'Unable to upload document, and unable to log the '
                        'error itself.', exc_info=True)

        return_dict['error_container'] = self._error_container

        self.import_events = []
        return return_dict

    @property
    def version(self):
        """Get Elasticsearch version.

        Returns:
          Version number as a string.
        """
        version_info = self.client.info().get('version')
        return version_info.get('number')
