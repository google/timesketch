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

from timesketch.lib import similarity
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class SimilarityScorerConfig(object):
    """Configuration for a similarity scorer."""

    # Parameters for Jaccard and Minhash calculations.
    DEFAULT_THRESHOLD = 0.5
    DEFAULT_PERMUTATIONS = 128

    DEFAULT_CONFIG = {
        "field": "message",
        "delimiters": [" ", "-", "/"],
        "threshold": DEFAULT_THRESHOLD,
        "num_perm": DEFAULT_PERMUTATIONS,
    }

    # For any data_type that need custom config parameters.
    # TODO: Move this to its own file.
    # TODO: Add stopwords boolean config parameter.
    # TODO: Add remove_words boolean config parameter.
    CONFIG_REGISTRY = {
        "windows:evtx:record": {
            "query": 'data_type:"windows:evtx:record"',
            "field": "message",
            "delimiters": [" ", "-", "/"],
            "threshold": DEFAULT_THRESHOLD,
            "num_perm": DEFAULT_PERMUTATIONS,
        }
    }

    def __init__(self, index_name, data_type):
        """Initializes a similarity scorer config.

        Args:
            index_name: OpenSearch index name.
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
            config_dict["query"] = 'data_type:"{0}"'.format(self._data_type)

        config_dict["index_name"] = self._index_name
        config_dict["data_type"] = self._data_type
        return config_dict


class SimilarityScorer(interface.BaseAnalyzer):
    """Score events based on Jaccard distance."""

    NAME = "similarity_scorer"
    DISPLAY_NAME = "Similarity Scorer"
    DESCRIPTION = (
        "Experimental: Calculate similarity scores based on the "
        "Jaccard distance between events"
    )

    DEPENDENCIES = frozenset()

    def __init__(self, index_name, sketch_id, timeline_id=None, data_type=None):
        """Initializes a similarity scorer.

        Args:
            index_name: OpenSearch index name.
            sketch_id: The ID of the sketch.
            timeline_id: The ID of the timeline.
            data_type: Name of the data_type.
        """
        self._config = None
        if data_type:
            self._config = SimilarityScorerConfig(index_name, data_type)
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)

    def run(self):
        """Entry point for the SimilarityScorer.

        Returns:
            A dict with metadata about the processed data set or None if no
            data_types has been configured.
        """
        if not self._config:
            return "No data_type specified."

        # Event generator for streaming results.
        events = self.event_stream(
            query_string=self._config.query, return_fields=[self._config.field]
        )

        lsh, minhashes = similarity.new_lsh_index(
            events,
            field=self._config.field,
            delimiters=self._config.delimiters,
            num_perm=self._config.num_perm,
            threshold=self._config.threshold,
        )
        total_num_events = len(minhashes)
        for key, minhash in minhashes.items():
            event_id, index_name = key
            event_dict = dict(_id=event_id, _index=index_name)
            event = interface.Event(event_dict, self.datastore)
            score = similarity.calculate_score(lsh, minhash, total_num_events)
            attributes_to_add = {"similarity_score": score}
            event.add_attributes(attributes_to_add)
            # Commit the event to the datastore.
            event.commit()

        msg = "Similarity scorer processed {0:d} events for data_type {1:s}"
        return msg.format(total_num_events, self._config.data_type)


manager.AnalysisManager.register_analyzer(SimilarityScorer)
