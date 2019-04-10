# Copyright 2019 Google Inc. All rights reserved.
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
"""Bucket aggregations."""

from __future__ import unicode_literals

from timesketch.lib.aggregators import manager
from timesketch.lib.aggregators import interface


class TermsAggregation(interface.BaseAggregator):
    """Terms Bucket Aggregation."""

    NAME = 'term_bucket_term'
    SUPPORTED_CHARTS = frozenset(['barchart', 'horizontal_barchart'])
    FORM_FIELDS = {
        'field': {
            'type': 'text',
            'description': 'What field to aggregate.'
        },
        'limit': {
            'type': 'number',
            'description': 'Number of results to return.'
        }
    }

    # pylint: disable=arguments-differ
    def run(self, field, limit=10):
        """Run the aggregation.

        Args:
            field: What field to aggregate.
            limit: How many buckets to return.

        Returns:
            Instance of interface.AggregationResult with aggregation result.
        """

        # Encoding information for Vega-Lite.
        encoding = {
            'x': {'field': field, 'type': 'nominal'},
            'y': {'field': 'count', 'type': 'quantitative'}
        }

        aggregation_spec = {
            'aggs': {
                'aggregation': {
                    'terms': {
                        'field': '{0:s}.keyword'.format(field),
                        'size': limit
                    }
                }
            }
        }

        response = self.elastic_aggregation(aggregation_spec)
        aggregations = response.get('aggregations', {})
        aggregation = aggregations.get('aggregation', {})
        buckets = aggregation.get('buckets', [])
        values = []
        for bucket in buckets:
            d = {field: bucket['key'], 'count': bucket['doc_count']}
            values.append(d)

        return interface.AggregationResult(encoding, values)


manager.AggregatorManager.register_aggregator(TermsAggregation)
