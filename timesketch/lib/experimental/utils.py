# Copyright 2017 Google Inc. All rights reserved.
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
"""Utilities for generating graphs from elasticsearch data."""

from __future__ import unicode_literals

# pylint: skip-file
import sys

from flask import current_app

from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.models.sketch import Sketch
from xml.etree import ElementTree

# TODO: Just for testing, remove as soon as graph analyzers are implemented.
GRAPH_VIEWS = [
    {
        'name': 'Entire graph',
        'description': 'Show the entire graph.',
        'labels': ['Browser'],
        'supported_os': ['Darwin', 'Linux', 'Windows'],
        'form_data': {},
        'query': 'MATCH (:Sketch{sketch_id:{sketch_id}})<-[:HAS]-(a)-[b]->(c) RETURN *'
    },
    {
        'name': 'Windows interactive logins',
        'description': 'Windows interactive logins.',
        'labels': [],
        'supported_os': ['Windows'],
        'form_data': {
            'username': {
                'label': 'Username',
                'value': '',
                'type': 'text',
                'validation': {'required': True},
            },
            'machine': {
                'label': 'Machine',
                'value': '',
                'type': 'text',
                'validation': {'required': False},
            }
        },
        'query': 'MATCH (:Sketch{sketch_id:{sketch_id}})<-[:HAS]-(user:WindowsADUser)-[r1:ACCESS]->(m1:WindowsMachine) WHERE r1.method = "Interactive" AND user.username = {username} RETURN *'
    },
    {
        'name': 'All Windows logins',
        'description': 'Windows interactive logins.',
        'labels': [],
        'supported_os': ['Windows'],
        'form_data': {},
        'query': 'MATCH (:Sketch{sketch_id:{sketch_id}})<-[:HAS]-(user:WindowsADUser)-[r1:ACCESS]->(m1:WindowsMachine) RETURN *'
    },
]


def event_stream(sketch_id, query):
    es = ElasticsearchDataStore(
        host=current_app.config['ELASTIC_HOST'],
        port=current_app.config['ELASTIC_PORT'])
    sketch = Sketch.query.get(sketch_id)
    if not sketch:
        sys.exit('No such sketch')
    indices = {t.searchindex.index_name for t in sketch.timelines}

    result = es.search(
        sketch_id=sketch_id,
        query_string=query,
        query_filter={'size': 10000, 'terminate_after': 1000},
        query_dsl={},
        indices=['_all'],
        return_fields=['xml_string', 'timestamp'],
        enable_scroll=True)

    scroll_id = result['_scroll_id']
    scroll_size = result['hits']['total']

    for event in result['hits']['hits']:
        yield event

    while scroll_size > 0:
        result = es.client.scroll(scroll_id=scroll_id, scroll='1m')
        scroll_id = result['_scroll_id']
        scroll_size = len(result['hits']['hits'])
        for event in result['hits']['hits']:
            yield event


def parse_xml_event(event_xml):
    xml_root = ElementTree.fromstring(event_xml)
    base = './/{http://schemas.microsoft.com/win/2004/08/events/event}'
    event_container = {'System': {}, 'EventData': {}}

    def _sanitize_event_value(value):
        none_values = ['-', ' ']
        if value in none_values:
            return None
        return value

    for child in xml_root.find('{0:s}System'.format(base)):
        element_name = child.tag.split('}')[1]
        element_value = _sanitize_event_value(child.text)
        event_container['System'][element_name] = {'value': element_value}
        event_container['System'][element_name]['attributes'] = child.attrib

    for child in xml_root.find('{0:s}EventData'.format(base)):
        element_name = child.get('Name')
        element_value = _sanitize_event_value(child.text)
        event_container['EventData'][element_name] = element_value

    return event_container


def get_graph_views():
    views = []

    for index, view in enumerate(GRAPH_VIEWS):
        view['id'] = index
        views.append(view)

    return views


def get_graph_view(view_id):
    return GRAPH_VIEWS[view_id]

