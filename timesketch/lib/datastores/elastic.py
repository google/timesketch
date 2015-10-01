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

    def search(self, sketch_id, query, query_filter, indices):
        """Search ElasticSearch. This will take a query string from the UI
        together with a filter definition. Based on this it will execute the
        search request on ElasticSearch and get result back.

        Args:
            sketch_id: Integer of sketch primary key
            query: Query string
            query_filter: Dictionary containing filters to apply
            indices = List of indices to query

        Returns:
            Set of event documents in JSON format
        """
        if not query:
            query = u''

        query_dict = {
            u'query': {
                u'filtered': {
                    u'query': {
                        u'query_string': {
                            u'query': query
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

        if query_filter.get(u'time_start', None):
            query_dict[u'query'][u'filtered'][u'filter'] = {
                u'range': {
                    u'datetime': {
                        u'gte': query_filter[u'time_start'],
                        u'lte': query_filter[u'time_end']
                    }
                }
            }

        if not indices:
            return {u'hits': {u'hits': [], u'total': 0}, u'took': 0}

        # Suppress the lint error because elasticsearch-py adds parameters
        # to the function with a decorator and this makes pylint sad.
        # pylint: disable=unexpected-keyword-arg
        return self.client.search(
            body=query_dict, index=indices, size=500, _source_include=[
                u'datetime', u'timestamp', u'message', u'timestamp_desc',
                u'timesketch_label'])

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
                u'_timestamp': {
                    u'enabled': True,
                    u'path': u'datetime',
                    u'format': u'date_time_no_millis'
                },
                u'properties': {u'timesketch_label': {u'type': u'nested'}}
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
