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

    NAME = 'field_bucket'
    DESCRIPTION = 'Aggregating values of a particular field'

    SUPPORTED_CHARTS = frozenset(['barchart', 'hbarchart'])

    FORM_FIELDS = [
        {
            'type': 'ts-dynamic-form-select-input',
            'name': 'supported_charts',
            'label': 'Chart type to render',
            'options': list(SUPPORTED_CHARTS)
        },
        {
            'type': 'ts-dynamic-form-text-input',
            'name': 'field',
            'label': 'What field to aggregate on',
            'placeholder': 'Enter a field to aggregate',
            'default_value': ''
        },
        {
            'type': 'ts-dynamic-form-text-input',
            'name': 'limit',
            'label': 'Number of results to return',
            'placeholder': 'Enter number of results to return',
            'default_value': '10'
        }
    ]

    def __init__(self, sketch_id=None, index=None):
        """Initialize the aggregator object.

        Args:
            sketch_id: Sketch ID.
            index: List of elasticsearch index names.
        """
        super(TermsAggregation, self).__init__(
            sketch_id=sketch_id, index=index)
        self.field = ''

    @property
    def chart_title(self):
        """Returns a title for the chart."""
        if self.field:
            return 'Top results for "{0:s}"'.format(self.field)
        return 'Top results for an unknown field'

    # pylint: disable=arguments-differ
    def run(self, field, limit=10):
        """Run the aggregation.

        Args:
            field: What field to aggregate.
            limit: How many buckets to return.

        Returns:
            Instance of interface.AggregationResult with aggregation result.
        """
        self.field = field
        # Encoding information for Vega-Lite.
        encoding = {
            'x': {
                'field': field,
                'type': 'nominal',
                'sort': {
                    'op': 'sum',
                    'field': 'count',
                    'order': 'descending'
                }
            },
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
