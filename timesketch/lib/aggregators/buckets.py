from __future__ import unicode_literals

from timesketch.lib.aggregators import manager
from timesketch.lib.aggregators import interface


class BucketTermsAggregation(interface.BaseAggregator):

    NAME = 'bucket_terms'
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

    def __init__(self, sketch_id=None, index=None):
        super(BucketTermsAggregation, self).__init__(sketch_id, index)

    def run(self, field, limit=10):

        # Encoding information for Vega-Lite.
        encoding = {
            'x': {'field': field, 'type': u'nominal'},
            'y': {'field': u'count', 'type': u'quantitative'}
        }

        aggregation_spec = {
            'aggs': {
                'aggregation': {
                    'terms': {
                        'field': '{0:s}.keyword'.format(field),
                        'size': limit,
                        'exclude': ''
                    }
                }
            }
        }

        response = self.elastic_aggregation(aggregation_spec)
        buckets = response['aggregations']['aggregation']['buckets']
        values = []
        for bucket in buckets:
            d = {field: bucket['key'], 'count': bucket['doc_count']}
            values.append(d)

        return interface.AggregationResult(encoding, values)


manager.AggregatorManager.register(BucketTermsAggregation)
