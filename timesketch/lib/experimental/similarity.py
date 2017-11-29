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
from flask import current_app

from datetime import datetime
import re

from datasketch.minhash import MinHash
from datasketch.lsh import MinHashLSH

from timesketch.lib.datastores.elastic import ElasticsearchDataStore


data_type_registry = {
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


class TimesketchSimilarityScorer(object):

    def __init__(self, index, data_type):
        self._index = index
        self._data_type = data_type_registry.get(data_type)
        self.es = ElasticsearchDataStore(
            host=current_app.config[u'ELASTIC_HOST'],
            port=current_app.config[u'ELASTIC_PORT'])

    def _generate_shingles(self, text):
        delimiters = self._data_type.get('delimiters')
        return re.split('|'.join(delimiters), text)

    def _generate_minhash(self, text):
        minhash = MinHash(num_perm=128)
        for word in self._generate_shingles(text):
            minhash.update(word.encode('utf8'))
        return minhash

    def _generate_lsh(self):
        lsh = MinHashLSH(threshold=0.5, num_perm=128)
        query = self._data_type.get('query')
        field = self._data_type.get('field')
        docs = {}

        t1 = datetime.now()
        for event in self.es.search_stream(
                query_string=query, query_filter={}, indices=[self._index],
                return_fields=[field]):
            doc_id = event['_id']
            doc_type = event['_type']
            index_id = event['_index']
            text = event['_source'][field]
            doc_key = doc_id + '+' + index_id + '+' + doc_type

            # Create LSH index
            minhash = self._generate_minhash(text)
            docs[doc_key] = minhash
            lsh.insert(doc_key, minhash)

        t2 = datetime.now()
        delta = t2 - t1

        return lsh, docs, delta.seconds

    @staticmethod
    def _score(lsh, docs):
        total_num_docs = len(docs)
        for doc_key, minhash in docs.items():
            neighbours = lsh.query(minhash)
            score = float(len(neighbours)) / float(total_num_docs)
            doc = doc_key.split('+')
            doc_id = doc[0]
            doc_index = doc[1]
            doc_type = doc[2]
            yield (doc_id, doc_index, doc_type, score)

    def run(self):
        lsh, docs, lsh_seconds = self._generate_lsh()
        t1 = datetime.now()
        for event in self._score(lsh, docs):
            doc_id, doc_index, doc_type, score = event
            new_doc = {u'similarity_score': score}
            self.es.import_event(
                flush_interval=1000, index_name=doc_index, event_type=doc_type,
                event=new_doc, event_id=doc_id)
        t2 = datetime.now()
        delta = t2 - t1

        return dict(
            num_docs=len(docs),
            index=self._index,
            query=self._data_type.get('query'),
            hash_seconds=lsh_seconds,
            score_seconds=delta.seconds
        )


