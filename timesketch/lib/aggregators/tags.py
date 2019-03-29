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
"""Tagging aggregations."""

from __future__ import unicode_literals

from timesketch.lib.aggregators import manager
from timesketch.lib.aggregators import interface


class TaggingAggregation(interface.BaseAggregator):
    """Tagging Bucket Aggregation."""

    NAME = 'tag_bucket'

    SUPPORTED_CHARTS = frozenset(['barchart', 'horizontal_barchart'])

    FORM_FIELDS = {
        'tag': {
            'type': 'text',
            'description': 'What tag do you want to aggregate.'
        },
        'attribute': {
            'type': 'text',
            'description': 'The attribute to bucketize.'
        },
    }

    def _get_spec(self):
        """Returns aggregation spec that aggregates frequency of tags."""
        return {
            'aggregations': {
                'tag_count': {
                    'terms': {
                        'field': 'tag.keyword',
                    }
                }
            }
        }

    def _get_spec_with_tag(self, tag, attribute):
        """Returns aggregation specs for events with specific tag.

        The aggregation spec will summarize values of an attribute
        whose events have a specific tag.

        Args:
          tag (str): the tag that needs to be set for an event to be counted.
          attribute (str): the attribute used to aggregate.

        Returns:
          a dict value that can be used as an aggregation spec.
        """
        return {
            'aggregations': {
                'tag_count': {
                    'filter': {
                        'bool': {
                            'must': [
                                {
                                    'query_string': {
                                        'query': 'tag:"{0:s}"'.format(tag)
                                    }
                                }
                            ]
                        }
                    },
                    'aggregations': {
                        'tag_count': {
                            'terms': {
                                'field': '{0:s}.keyword'.format(attribute)
                            }
                        }
                    }
                }
            }
        }


    # pylint: disable=arguments-differ
    def run(self, tag='', attribute=''):
        """Run the aggregation.

        Args:
            tag (str): what tag to aggregate. If a tag is supplied events
                that have that tag applied to it are counted, using the value
                of the supplied attribute. If the tag is not supplied (default)
                then all tagged events are included and the tags themselves
                are bucketized.
            attribute (str): if a tag is supplied this denotes the event
                attribute that is used for aggregation.

        Returns:
            Instance of interface.AggregationResult with aggregation result.
        """
        if tag:
            aggregation_spec = self._get_spec_with_tag(tag, attribute)
        else:
            aggregation_spec = self._get_spec()
            attribute = 'tag'

        # Encoding information for Vega-Lite.
        encoding = {
            'x': {'field': attribute, 'type': 'nominal'},
            'y': {'field': 'count', 'type': 'quantitative'}
        }

        response = self.elastic_aggregation(aggregation_spec)
        aggregations = response.get('aggregations', {})
        tag_count = aggregations.get('tag_count', {})

        # If we are doing the aggregation of a specific tag we have an extra
        # layer.
        if 'tag_count' in tag_count:
            tag_count = tag_count.get('tag_count', {})

        buckets = tag_count.get('buckets', [])
        values = []
        for bucket in buckets:
            d = {
                attribute: bucket.get('key', 'N/A'),
                'count': bucket.get('doc_count', 0)
            }
            values.append(d)

        return interface.AggregationResult(encoding, values)


manager.AggregatorManager.register_aggregator(TaggingAggregation)
