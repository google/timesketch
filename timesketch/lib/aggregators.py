# Copyright 2015 Google Inc. All rights reserved.
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
"""Elasticsearch aggregations."""

from __future__ import unicode_literals

# Max number of search hits to chart
# TODO: Move to config
MAX_RESULT_LIMIT = 300000


def heatmap(es_client, sketch_id, query_string, query_filter, query_dsl,
            indices):
    """Aggregate query results into number of events per hour/day.

    Args:
        es_client: Elasticsearch client (instance of ElasticSearchDatastore)
        sketch_id: Integer of sketch primary key
        query_string: Query string
        query_filter: Dictionary containing filters to apply
        query_dsl: Dictionary containing Elasticsearch DSL to apply
        indices: List of indices to query

    returns:
        List of events per hour/day
    """

    # scripts don't like our pagination method, so remove them
    query_filter.pop("size", None)
    query_filter.pop("from", None)

    result_count = es_client.search(
        sketch_id, query_string, query_filter, query_dsl, indices, count=True)

    # Exit early if we have too many search hits.
    if result_count > MAX_RESULT_LIMIT or result_count == 0:
        return []

    days_map = {
        'Mon': 1,
        'Tue': 2,
        'Wed': 3,
        'Thu': 4,
        'Fri': 5,
        'Sat': 6,
        'Sun': 7,
    }

    # Elasticsearch 5.x doesn't support toString for dates. Use SimpleDateFormat
    # instead.
    # pylint: disable=line-too-long

    if es_client.version.startswith('5.'):
        source_script = 'new SimpleDateFormat(params.format).format(new Date(doc["datetime"].value))'
    else:
        source_script = 'doc["datetime"].value.toString(params.format);'

    aggregation = {
        'byDay': {
            'terms': {
                'script': {
                    'source': source_script,
                    'lang': 'painless',
                    'params': {
                        'format': 'E'
                    }
                }
            },
            'aggs': {
                'byHour': {
                    'terms': {
                        'order': {
                            '_term': 'asc'
                        },
                        'script': {
                            'source': source_script,
                            'lang': 'painless',
                            'params': {
                                'format': 'H'
                            }
                        },
                        'size': 24
                    }
                }
            }
        }
    }

    search_result = es_client.search(
        sketch_id,
        query_string,
        query_filter,
        query_dsl,
        indices,
        aggregations=aggregation,
        return_fields=None,
        enable_scroll=False)

    try:
        aggregation_result = search_result['aggregations']
        day_buckets = aggregation_result['byDay']['buckets']
    except KeyError:
        day_buckets = []

    per_hour = {}
    for day in range(1, 8):
        for hour in range(0, 24):
            per_hour[(day, hour)] = 0

    for day_bucket in day_buckets:
        day = days_map[day_bucket.get('key')]
        day_hours = day_bucket['byHour']['buckets']

        for day_hour in day_hours:
            hour = int(day_hour['key'])
            count = day_hour['doc_count']
            per_hour[(day, int(hour))] = count

    return [dict(day=k[0], hour=k[1], count=v) for k, v in per_hour.items()]


def histogram(es_client, sketch_id, query_string, query_filter, query_dsl,
              indices):
    """Aggregate query results into number of events per time interval.

    Args:
        es_client: Elasticsearch client (instance of ElasticSearchDatastore)
        sketch_id: Integer of sketch primary key
        query_string: Query string
        query_filter: Dictionary containing filters to apply
        query_dsl: Dictionary containing Elasticsearch DSL to apply
        indices: List of indices to query

    returns:
        List of events per hour/day
    """
    # scripts don't like our pagination method, so remove them
    query_filter.pop("size", None)
    query_filter.pop("from", None)

    result_count = es_client.search(
        sketch_id, query_string, query_filter, query_dsl, indices, count=True)

    # Exit early if we have too many search hits.
    if result_count > MAX_RESULT_LIMIT or result_count == 0:
        return []

    # Default aggregation config
    interval = 'day'
    min_doc_count = 10

    if result_count < 10:
        min_doc_count = 1

    aggregation = {
        'histogram': {
            'date_histogram': {
                'min_doc_count': min_doc_count,
                'field': 'datetime',
                'interval': interval,
                'format': 'yyyy-MM-dd'
            }
        }
    }

    if result_count < MAX_RESULT_LIMIT:
        search_result = es_client.search(
            sketch_id,
            query_string,
            query_filter,
            query_dsl,
            indices,
            aggregations=aggregation,
            return_fields=None,
            enable_scroll=False)
    else:
        search_result = {}

    try:
        aggregation_result = search_result['aggregations']
        if aggregation_result.get('exclude', None):
            buckets = aggregation_result['exclude']['histogram']['buckets']
        else:
            buckets = aggregation_result['histogram']['buckets']
    except KeyError:
        buckets = []

    return buckets
