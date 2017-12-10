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
from __future__ import unicode_literals

import re
from flask import current_app
from datasketch.minhash import MinHash
from datasketch.lsh import MinHashLSH
from timesketch.lib.datastores.elastic import ElasticsearchDataStore


class SimilarityScorerConfig(object):

    # Parameters for Jaccard and Minhash calculations.
    DEFAULT_THRESHOLD = 0.5
    DEFAULT_PERMUTATIONS = 128

    DEFAULT_CONFIG = {
        'field': 'message',
        'delimiters': [' ', '-', '/'],
        'threshold': DEFAULT_THRESHOLD,
        'num_perm': DEFAULT_PERMUTATIONS
    }

    # For any data_type that need custom config parameters.
    CONFIG_REGISTRY = {
        'windows:evtx:record': {
            'query': 'data_type:"windows:evtx:record"',
            'field': 'message',
            'delimiters': [' ', '-', '/'],
            'threshold': DEFAULT_THRESHOLD,
            'num_perm': DEFAULT_PERMUTATIONS
        }
    }

    def __init__(self, data_type, index):
        config = self._get_config(data_type, index)
        for key in config:
            setattr(self, key, config[key])

    def _get_config(self, data_type, index):
        config = self.CONFIG_REGISTRY.get(data_type)

        # If there are no config for this data_type, use generic config and set
        # the query based on the data_type.
        if not config:
            config = self.DEFAULT_CONFIG
            config['query'] = 'data_type:"{0}"'.format(data_type)

        config['index'] = index
        config['data_type'] = data_type

        return config


class SimilarityScorer(object):

    def __init__(self, index, data_type):
        self._datastore = ElasticsearchDataStore(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])
        self.config = SimilarityScorerConfig(data_type, index)

    def _shingles_from_text(self, text):
        delimiters = self.config.delimiters
        return re.split('|'.join(delimiters), text)

    def _minhash_from_text(self, text):
        minhash = MinHash(self.config.num_perm)
        for word in self._shingles_from_text(text):
            minhash.update(word.encode('utf8'))
        return minhash

    def _new_lsh_index(self, event_generator):
        minhashes = {}
        lsh = MinHashLSH(self.config.threshold, self.config.num_perm)

        with lsh.insertion_session() as lsh_session:
            for event in event_generator:
                event_id = event['_id']
                index_name = event['_index']
                event_type = event['_type']
                event_text = event['_source'][self.config.field]

                # Insert minhash in LSH index
                key = (event_id, event_type, index_name)
                minhash = self._minhash_from_text(event_text)
                minhashes[key] = minhash
                lsh_session.insert(key, minhash)

        return lsh, minhashes

    @staticmethod
    def _score(lsh, minhash, total_num_events):
        neighbours = lsh.query(minhash)
        return float(len(neighbours)) / float(total_num_events)

    def _event_generator(self):
        return self._datastore.search_stream(
            query_string=self.config.query,
            query_filter={},
            indices=[self.config.index],
            return_fields=[self.config.field]
        )

    def _update_event(self, event_id, event_type, index_name, score):
        update_doc = {'similarity_score': score}
        flush_interval = 1000  # Number of events that will be sent in batch
        self._datastore.import_event(
            flush_interval=flush_interval, index_name=index_name,
            event_type=event_type, event_id=event_id, event=update_doc)

    def run(self):
        event_generator = self._event_generator()
        lsh, minhashes = self._new_lsh_index(event_generator)
        total_num_events = len(minhashes)
        for key, minhash in minhashes.items():
            event_id, event_type, index_name = key
            score = self._score(lsh, minhash, total_num_events)
            self._update_event(event_id, event_type, index_name, score)

        return dict(
            index=self.config.index,
            data_type=self.config.data_type,
            num_events_processed=total_num_events
        )
