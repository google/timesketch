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
import re
from flask import current_app
from datasketch.minhash import MinHash
from datasketch.lsh import MinHashLSH
from timesketch.lib.datastores.elastic import ElasticsearchDataStore


class DataTypeConfig(object):

    REGISTRY = {
        'windows:evtx:record': {
            'query': 'data_type:"windows:evtx:record"',
            'field': 'message',
            'delimiters': [' ', '-', '/']
        },
        'chrome:history:page_visited': {
            'query': 'data_type:"chrome:history:page_visited"',
            'field': 'message',
            'delimiters': [' ', '-', '/']
        }
    }

    def __init__(self, data_type):
        self._data_type = self._get_config(data_type)

    def _get_config(self, data_type):
        default_config = {
            'query': 'data_type:"{0}"'.format(data_type),
            'field': 'message',
            'delimiters': [' ', '-', '/']
        }
        return self.REGISTRY.get(data_type, default_config)

    @property
    def query(self):
        return self._data_type.get('query')

    @property
    def field(self):
        return self._data_type.get('field')

    @property
    def delimiters(self):
        return self._data_type.get('delimiters')


class SimilarityScorer(object):

    def __init__(self, index, data_type, threshold=0.5, num_perm=128):
        self._datastore = ElasticsearchDataStore(
            host=current_app.config[u'ELASTIC_HOST'],
            port=current_app.config[u'ELASTIC_PORT'])
        self._threshold = threshold
        self._num_perm = num_perm
        self._LSH = MinHashLSH(threshold, num_perm)
        self._index = index
        self._data_type_name = data_type
        self._config = DataTypeConfig(data_type)

    def _shingles_from_text(self, text):
        delimiters = self._config.delimiters
        return re.split('|'.join(delimiters), text)

    def _minhash_from_text(self, text):
        minhash = MinHash(self._num_perm)
        for word in self._shingles_from_text(text):
            minhash.update(word.encode('utf8'))
        return minhash

    def _new_lsh_index(self, event_generator):
        minhashes = {}

        with self._LSH.insertion_session() as lsh_session:
            for event in event_generator:
                event_id = event['_id']
                index_name = event['_index']
                event_type = event['_type']
                event_text = event['_source'][self._config.field]

                # Insert minhash in LSH index
                key = (event_id, event_type, index_name)
                minhash = self._minhash_from_text(event_text)
                minhashes[key] = minhash
                lsh_session.insert(key, minhash)

        return minhashes

    def _score(self, minhash, total_num_events):
        neighbours = self._LSH.query(minhash)
        return float(len(neighbours)) / float(total_num_events)

    def _event_generator(self):
        query = self._config.query
        field = self._config.field

        return self._datastore.search_stream(
            query_string=query, query_filter={}, indices=[self._index],
            return_fields=[field])

    def _update_event(self, event_id, event_type, index_name, score):
        update_doc = {u'similarity_score': score}
        self._datastore.import_event(
            flush_interval=1000, index_name=index_name, event_type=event_type,
            event_id=event_id, event=update_doc)

    def process(self):
        event_generator = self._event_generator()
        minhashes = self._new_lsh_index(event_generator)
        total_num_events = len(minhashes)
        for key, minhash in minhashes.items():
            event_id, event_type, index_name = key
            score = self._score(minhash, total_num_events)
            self._update_event(event_id, event_type, index_name, score)

        return dict(
            index=self._index,
            data_type=self._data_type_name,
            num_events_processed=total_num_events
        )
