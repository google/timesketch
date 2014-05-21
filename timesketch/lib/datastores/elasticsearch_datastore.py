# Copyright 2014 Google Inc. All rights reserved.
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
"""This implements timesketch ElasticSearch API."""

from pyelasticsearch import ElasticSearch
from timesketch.settings import ELASTICSEARCH_SERVER_IP
from timesketch.settings import ELASTICSEARCH_PORT

from timesketch.lib import datastore


class ElasticSearchDataStore(datastore.DataStore):
    """Implements the API.""" 
    def __init__(self, index_list):
        # Connect to the Elasticsearch server.
        self.client = ElasticSearch('http://%s:%s/' % (ELASTICSEARCH_SERVER_IP,
                                                       ELASTICSEARCH_PORT))
        # TODO Refactor this to not need the index list at this stage.
        self.index_list = index_list

    def search(self, sketch, query, filters):
        """Search ElasticSearch. This will take a query string from the UI
        together with a filter definition. Based on this it will send the
        search request to elasticsearch and get result back.

        Args:
            sketch -- string, sketch ID
            query -- string, query string
            filters -- dict, Dictionary containing filters to apply 

        Returns:
            Set of event documents in JSON format
        """

        if filters.get("time_start", None):
            query = {
                "query": {
                    "query_string": {
                        "query": query
                    }
                },
                "filter": {
                    "range": {
                        "datetime": {
                            "gte": filters['time_start'],
                            "lte": filters['time_end']
                        }
                    }
                },
                "sort": {
                    "datetime": "asc"
                }
            }
        elif filters.get("star", None):
            query = {
                "query": {
                    "match_all": {}
                },
                "filter": {
                    "nested": {
                        "path": "timesketch_label", "filter": {
                        "bool": {
                            "must": [
                                {
                                    "term": {
                                        "timesketch_label.name": "__ts_star"
                                    }
                                },
                                {
                                    "term": {
                                        "timesketch_label.sketch": str(sketch)
                                    }
                                }
                            ]
                        }
                        }
                    }
                },
                "sort": {
                    "datetime": "asc"
                }
            }
        else:
            query = {
                "query": {
                    "query_string": {
                        "query": query
                    }
                },
                "sort": {
                    "datetime": "asc"
                }
            }

        return self.client.search(query, index=self.index_list,
                                  doc_type="plaso_event", size=500)


    def get_single_event(self, event_id):
        """Get singel event document form elasticsearch

        Args:
            event_id -- string, event ID

        Returns:
            Event document as JSON
        """
        return self.client.get(index=self.index_list[0],
            doc_type="plaso_event",id=event_id)

    def add_label_to_event(self, event, sketch, user, label, toggle=False):
        """Add label to a event document in ElasticSearch.

        Args:
            event -- string, event ID
            sketch -- string, sketch ID
            user -- string, user ID
            label -- string, the label to apply
            toggle -- Bool, Toggle label or create a new one

        Returns:
            HTTP status code

        In order for this to work, we need to add a mapping for this nested
        document. This needs to be done when the index is forst created.
        mapping = {
            "plaso_event": {
                "properties": {
                    "timesketch_label": {
                        "type": "nested"
                    }
                }
            }
        }
        """

        doc = self.client.get(self.index_list, "plaso_event", event)
        try:
            doc['_source']['timesketch_label']
        except KeyError:
            doc = {"timesketch_label": []}
            self.client.update(self.index_list, "plaso_event", event, doc=doc)

        if toggle:
            script_string = "if(ctx._source.timesketch_label.contains"\
                            "(timesketch_label)) {ctx._source.timesketch_label"\
                            ".remove(timesketch_label)} else {ctx._source."\
                            "timesketch_label += timesketch_label}"
        else:
            script_string = "if( ! ctx._source.timesketch_label.contains"\
                            "(timesketch_label)) {ctx._source.timesketch_label"\
                            "+= timesketch_label}"
        script = {
            "script": script_string,
            "params": {
                "timesketch_label": {
                    "name": label, "user": user, "sketch": sketch
                }
            }
        }
        self.client.update(self.index_list, "plaso_event", event, script)
