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

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from flask import abort

from timesketch.lib import datastore


# Setup logging
es_logger = logging.getLogger('elasticsearch')
es_logger.addHandler(logging.NullHandler())


class ElasticSearchDataStore(datastore.DataStore):
    """Implements the datastore."""
    def __init__(self, host='127.0.0.1', port=9200):
        """Create a Elasticsearch client."""
        self.client = Elasticsearch([
            {'host': host, 'port': port}
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
            query = ""

        query_dict = {
            "query": {
                "filtered": {
                    "query": {
                        "query_string": {
                            "query": query
                        }
                    }
                }
            },
            "sort": {
                "datetime": "asc"
            }
        }

        if query_filter.get('star', None):
            del query_dict['query']['filtered']['query']
            query_dict['query']['filtered']['filter'] = {
                "nested": {
                    "path": "timesketch_label",
                    "filter": {
                        "bool": {
                            "must": [
                                {
                                    "term": {
                                        "timesketch_label.name": "__ts_star"
                                    }
                                },
                                {
                                    "term": {
                                        "timesketch_label.sketch_id": sketch_id
                                    }
                                }
                            ]
                        }
                    }
                }
            }

        if query_filter.get("time_start", None):
            query_dict['query']['filtered']['filter'] = {
                "range": {
                    "datetime": {
                        "gte": query_filter['time_start'],
                        "lte": query_filter['time_end']
                    }
                }
            }

        if not indices:
            return {u'hits':  {u'hits': [], u'total': 0}, u'took': 0}

        # Suppress the lint error because elasticsearch-py adds parameters
        # to the function with a decorator and this makes pylint sad.
        # pylint: disable=unexpected-keyword-arg
        return self.client.search(
            body=query_dict, index=indices, size=500,
            _source_include=[
                'datetime', 'timestamp', 'message', 'timestamp_desc',
                'timesketch_label'
            ])

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
                _source_exclude=['timesketch_label'])
        except NotFoundError:
            abort(404)

    def set_label(
            self, searchindex_id, event_id, sketch_id, user_id, label,
            toggle=False):
        """Set label on event in the datastore.

        Args:
            searchindex_id: String of ElasticSearch index id
            event_id: String of ElasticSearch event id
            sketch_id: Integer of sketch primary key
            user_id: Integer of user primary key
            label: String with the name of the label
            toggle: Optional boolean value if the label should be toggled
            (add/remove). The default is False.
        """
        doc = self.client.get(index=searchindex_id, id=event_id)
        try:
            doc['_source']['timesketch_label']
        except KeyError:
            doc = {'doc': {'timesketch_label': []}}
            self.client.update(
                index=searchindex_id, doc_type='plaso_event', id=event_id,
                body=doc)

        if toggle:
            script_string = (
                'if(ctx._source.timesketch_label.contains'
                '(timesketch_label)) {ctx._source.timesketch_label'
                '.remove(timesketch_label)} else {ctx._source.'
                'timesketch_label += timesketch_label}')
        else:
            script_string = (
                'if( ! ctx._source.timesketch_label.contains'
                '(timesketch_label)) {ctx._source.timesketch_label'
                '+= timesketch_label}')
        script = {
            'script': script_string,
            'params': {
                'timesketch_label': {
                    'name': str(label),
                    'user_id': user_id,
                    'sketch_id': sketch_id
                }
            }
        }
        self.client.update(
            index=searchindex_id, id=event_id, doc_type='plaso_event',
            body=script)
