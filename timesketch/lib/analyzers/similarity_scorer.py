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
"""Calculate similarity scores based on the Jaccard distance between events."""

from __future__ import unicode_literals

import re

from flask import current_app

from datasketch.minhash import MinHash
from datasketch.lsh import MinHashLSH
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class SimilarityScorerConfig(object):
    """Configuration for a similarity scorer."""

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
    # TODO: Move this to its own file.
    # TODO: Add stopwords boolean config parameter.
    # TODO: Add remove_words boolean config parameter.
    CONFIG_REGISTRY = {
        'windows:evtx:record': {
            'query': 'data_type:"windows:evtx:record"',
            'field': 'message',
            'delimiters': [' ', '-', '/'],
            'threshold': DEFAULT_THRESHOLD,
            'num_perm': DEFAULT_PERMUTATIONS
        }
    }

    def __init__(self, index_name, data_type):
        """Initializes a similarity scorer config.

        Args:
            index_name: Elasticsearch index name.
            data_type: Name of the data_type.
        """
        self._index_name = index_name
        self._data_type = data_type
        for k, v in self._get_config().items():
            setattr(self, k, v)

    def _get_config(self):
        """Get config for supplied data_type.

        Returns:
            Dictionary with configuration parameters.
        """
        config_dict = self.CONFIG_REGISTRY.get(self._data_type)

        # If there is no config for this data_type, use default config and set
        # the query based on the data_type.
        if not config_dict:
            config_dict = self.DEFAULT_CONFIG
            config_dict['query'] = 'data_type:"{0}"'.format(self._data_type)

        config_dict['index_name'] = self._index_name
        config_dict['data_type'] = self._data_type
        return config_dict


class SimilarityScorer(interface.BaseIndexAnalyzer):
    """Score events based on Jaccard distance."""

    NAME = 'SimilarityScorer'

    def __init__(self, index_name, data_type=None):
        """Initializes a similarity scorer.

        Args:
            index_name: Elasticsearch index name.
            data_type: Name of the data_type.
        """
        if data_type:
            self._config = SimilarityScorerConfig(index_name, data_type)
        else:
            self._config = None
        super(SimilarityScorer, self).__init__(index_name)

    def _shingles_from_text(self, text):
        """Splits string into words.

        Args:
            text: String to extract words from.

        Returns:
            List of words.
        """
        # TODO: Remove stopwords using the NLTK python package.
        # TODO: Remove configured patterns from string.
        delimiters = self._config.delimiters
        return filter(None, re.split('|'.join(delimiters), text))

    def _minhash_from_text(self, text):
        """Calculate minhash of text.

        Args:
            text: String to calculate minhash of.

        Returns:
            A minhash (instance of datasketch.minhash.MinHash)
        """
        minhash = MinHash(self._config.num_perm)
        for word in self._shingles_from_text(text):
            minhash.update(word.encode('utf8'))
        return minhash

    def _new_lsh_index(self, events):
        """Create a new LSH from a set of Timesketch events.

        Returns:
            A tuple with an LSH (instance of datasketch.lsh.LSH) and a
            dictionary with event ID as key and minhash as value.
        """
        minhashes = {}
        lsh = MinHashLSH(self._config.threshold, self._config.num_perm)

        with lsh.insertion_session() as lsh_session:
            for event in events:
                # Insert minhash in LSH index
                key = (event.event_id, event.event_type, event.index_name)
                minhash = self._minhash_from_text(
                    event.source[self._config.field])
                minhashes[key] = minhash
                lsh_session.insert(key, minhash)

        return lsh, minhashes

    @staticmethod
    def _calculate_score(lsh, minhash, total_num_events):
        """Calculate a score based on Jaccard distance.

        The score is calculated based on how many similar events that there are
        for the event being scored. This is called neighbours and we simply
        calculate how many neighbours the event has divided by the total events
        in the LSH.

        Args:
            lsh: Instance of datasketch.lsh.MinHashLSH
            minhash: Instance of datasketch.minhash.MinHash
            total_num_events: Integer of how many events in the LSH

        Returns:
            A float between 0 and 1.
        """
        neighbours = lsh.query(minhash)
        return float(len(neighbours)) / float(total_num_events)

    @classmethod
    def get_kwargs(cls):
        """Keyword arguments needed to instantiate the class.

        In addition to the index_name passed to the constructor by default we
        need the data_type name as well. Furthermore we want to instantiate
        one task per data_type in order to run the analyzer in parallel. To
        achieve this we override this method and return a list of keyword
        argument dictionaries.

        Returns:
            List of keyword arguments (dict), one per data_type.
        """
        kwargs_list = []
        try:
            data_types = current_app.config['SIMILARITY_DATA_TYPES']
            if data_types:
                for data_type in data_types:
                    kwargs_list.append({'data_type': data_type})
        except KeyError:
            return None
        return kwargs_list

    def run(self):
        """Entry point for the SimilarityScorer.

        Returns:
            A dict with metadata about the processed data set or None if no
            data_types has been configured.
        """
        # Exit early if there is no data_type to process.
        if not self._config:
            return

        # Event generator for streaming results.
        events = self.event_stream(
            query_string=self._config.query,
            return_fields=[self._config.field]
        )

        lsh, minhashes = self._new_lsh_index(events)
        total_num_events = len(minhashes)
        for key, minhash in minhashes.items():
            event_id, event_type, index_name = key
            event_dict = dict(_id=event_id, _type=event_type, _index=index_name)
            event = interface.Event(event_dict, self.datastore)
            score = self._calculate_score(lsh, minhash, total_num_events)
            attributes_to_add = {'similarity_score': score}
            event.add_attributes(attributes_to_add)

        return dict(
            index=self._config.index_name,
            data_type=self._config.data_type,
            num_events_processed=total_num_events
        )


manager.AnalysisManager.register_analyzer(SimilarityScorer)
