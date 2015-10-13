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
    aggregations = {
        u'time_histogram': {
            u'date_histogram': {
                u'field': u'datetime',
                u'interval': u'hour',
                u'format': u'e,H'
            }
        }
    }
    search_result = es_client.search(
        sketch_id, query, query_filter, indices, aggregations=aggregations,
        return_results=False)

    per_hour = {}
    for day in range(1, 8):
        for hour in range(0, 24):
            per_hour[(day, hour)] = 0

    for n in search_result[u'aggregations'][u'time_histogram'][u'buckets']:
        day_hour = tuple(int(dh) for dh in n[u'key_as_string'].split(u','))
        count = n[u'doc_count']
        per_hour[day_hour] = count

    return [dict(day=k[0], hour=k[1], count=v) for k, v in per_hour.items()]


