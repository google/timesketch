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


def heatmap(es_client, sketch_id, query, query_filter, indices):
    """Aggregate query results into number of events per hour/day.

    Args:
        es_client: Elasticsearch client (instance of ElasticSearchDatastore)
        sketch_id: Integer of sketch primary key
        query: Query string
        query_filter: Dictionary containing filters to apply
        indices: List of indices to query

    returns:
        List of events per hour/day
    """
    aggregation = {
        u'heatmap': {
            u'date_histogram': {
                u'field': u'datetime',
                u'interval': u'hour',
                u'format': u'e,H'
            }
        }
    }

    search_result = es_client.search(
        sketch_id, query, query_filter, indices, aggregations=aggregation,
        return_results=False)

    try:
        aggregation_result = search_result[u'aggregations']
        if aggregation_result.get(u'exclude', None):
            buckets = aggregation_result[u'exclude'][u'heatmap'][u'buckets']
        else:
            buckets = aggregation_result[u'heatmap'][u'buckets']
    except KeyError:
        buckets = []

    per_hour = {}
    for day in range(1, 8):
        for hour in range(0, 24):
            per_hour[(day, hour)] = 0

    for bucket in buckets:
        day_hour = tuple(int(dh) for dh in bucket[u'key_as_string'].split(u','))
        count = bucket[u'doc_count']
        per_hour[day_hour] += count

    return [dict(day=k[0], hour=k[1], count=v) for k, v in per_hour.items()]


def histogram(es_client, sketch_id, query, query_filter, indices):
    """Aggregate query results into number of events per time interval.

    Args:
        es_client: Elasticsearch client (instance of ElasticSearchDatastore)
        sketch_id: Integer of sketch primary key
        query: Query string
        query_filter: Dictionary containing filters to apply
        indices: List of indices to query

    returns:
        List of events per hour/day
    """
    aggregation = {
        u'histogram': {
            u'date_histogram': {
                u'field': u'datetime',
                u'interval': u'day',
                u'format': u'yyyy-MM-dd'
            }
        }
    }

    search_result = es_client.search(
        sketch_id, query, query_filter, indices, aggregations=aggregation,
        return_results=False)

    try:
        aggregation_result = search_result[u'aggregations']
        if aggregation_result.get(u'exclude', None):
            buckets = aggregation_result[u'exclude'][u'histogram'][u'buckets']
        else:
            buckets = aggregation_result[u'histogram'][u'buckets']
    except KeyError:
        buckets = []

    return buckets
