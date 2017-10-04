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

# Max number of search hits to chart
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
    RESULT_COUNT = search_result = es_client.search(
        sketch_id, query_string, query_filter, query_dsl, indices, count=True)

    # Exit early if we have too many search hits.
    if RESULT_COUNT > MAX_RESULT_LIMIT or RESULT_COUNT == 0:
        return []

    DAYS = {
        u'Mon': 1,
        u'Tue': 2,
        u'Wed': 3,
        u'Thu': 4,
        u'Fri': 5,
        u'Sat': 6,
        u'Sun': 7,
    }

    aggregation = {
        u'byDay': {
            u'terms': {
                u'script': {
                    u'file': 'dateaggregation',
                    u'lang': 'groovy',
                    u'params': {
                        u'date_field': 'datetime',
                        u'format': 'EE'
                    }
                }
            },
            u'aggs': {
                u'byHour': {
                    u'terms': {
                        u'order': {
                            u'_term': 'asc'
                        },
                        u'script': {
                            u'file': 'dateaggregation',
                            u'lang': 'groovy',
                            u'params': {
                                u'date_field': 'datetime',
                                u'format': 'HH'
                            }
                        },
                        u'size': 24
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
        return_results=False,
        return_fields=None,
        enable_scroll=False)

    try:
        aggregation_result = search_result[u'aggregations']
        day_buckets = aggregation_result[u'byDay'][u'buckets']
    except KeyError:
        day_buckets = []

    per_hour = {}
    for day in range(1, 8):
        for hour in range(0, 24):
            per_hour[(day, hour)] = 0

    for day_bucket in day_buckets:
        day = DAYS[day_bucket.get(u'key')]
        day_hours = day_bucket[u'byHour'][u'buckets']

        for day_hour in day_hours:
            hour = int(day_hour[u'key'])
            count = day_hour[u'doc_count']
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
    RESULT_COUNT = search_result = es_client.search(
        sketch_id, query_string, query_filter, query_dsl, indices, count=True)

    # Exit early if we have too many search hits.
    if RESULT_COUNT > MAX_RESULT_LIMIT or RESULT_COUNT == 0:
        return []

    # Default aggregation config
    interval = u'day'
    min_doc_count = 10

    if not query_filter.get(u'time_start') and RESULT_COUNT > 1000:
        interval = u'year'
        min_doc_count = 100

    if RESULT_COUNT < 10:
        min_doc_count = 1

    aggregation = {
        u'histogram': {
            u'date_histogram': {
                u'min_doc_count': min_doc_count,
                u'field': u'datetime',
                u'interval': interval,
                u'format': u'yyyy-MM-dd'
            }
        }
    }

    if RESULT_COUNT < MAX_RESULT_LIMIT:
        search_result = es_client.search(
            sketch_id,
            query_string,
            query_filter,
            query_dsl,
            indices,
            aggregations=aggregation,
            return_results=False)
    else:
        search_result = {}

    try:
        aggregation_result = search_result[u'aggregations']
        if aggregation_result.get(u'exclude', None):
            buckets = aggregation_result[u'exclude'][u'histogram'][u'buckets']
        else:
            buckets = aggregation_result[u'histogram'][u'buckets']
    except KeyError:
        buckets = []

    return buckets
