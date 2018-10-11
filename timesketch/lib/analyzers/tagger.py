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

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class Tagger(interface.BaseAnalyzer):
    """Score events based on Jaccard distance."""

    NAME = 'Tagger'

    def __init__(self, index_name):
        """Initializes a similarity scorer.

        Args:
            index_name: Elasticsearch index name.
        """
        self.index_name = index_name
        super(Tagger, self).__init__()

    def run(self):

        events = self.event_stream(
            query_string='data_type:"windows:evtx:record"',
            return_fields=['tag']
        )

        counter = 0
        tags = ['foo', 'bar']

        for event in events:
            #event.add_tags(tags)
            #event.add_comment("foobar")
            #event.add_star()
            counter += 1

        return 'Tagged {0:d} events'.format(counter)


manager.AnalysisManager.register_analyzer(Tagger)
