# Copyright 2018 Google Inc. All rights reserved.
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
"""Interface for Analyzers."""

from __future__ import unicode_literals

from flask import current_app
from timesketch.lib.datastores.elastic import ElasticsearchDataStore


def _flush_datastore_decorator(func):
    """Decorator that flushes the bulk insert queue on the datastore."""
    def wrapper(self, *args, **kwargs):
        func_return = func(self, *args, **kwargs)
        self.datastore.flush_queued_events()
        return func_return
    return wrapper


class BaseAnalyzer(object):
    """Base class for analyzers.

    Attributes:
        name: of analyzer
        datastore: Elasticsearch datastore client
    """

    NAME = 'name'
    IS_SKETCH_ANALYZER = False

    def __init__(self):
        self.name = self.NAME
        self.datastore = ElasticsearchDataStore(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])

    def update_event(self, index_name, event_type, event_id, attributes):
        """Update an event in Elasticsearch.

        Args:
            event_id: ID of the Elasticsearch document.
            event_type: The Elasticsearch type of the event.
            index_name: The name of the index in Elasticsearch.
            attributes: A dictionary with attributes to add to the event.
        """
        self.datastore.import_event(
            index_name, event_type, event_id=event_id, event=attributes)

    def set_label(self,
                  searchindex_id,
                  event_id,
                  event_type,
                  sketch_id,
                  user_id,
                  label,
                  toggle=False):

    def label_event(self, event, sketch_id, label):
        
        self.datastore.set_label(
            index_name, event_type, event_id=event_id, event=attributes)


    @_flush_datastore_decorator
    def run_wrapper(self):
        """A wrapper method to run the analyzer.

        This method is decorated with a decorator for flushing the bulk insert
        operation on the datastore. This makes sure all events are flushed at
        exit.

        Returns:
            Return value of the run method.
        """
        result = self.run()
        return result

    @classmethod
    def get_kwargs(cls):
        """Get keyword arguments needed to instantiate the class.

        Every analyzer gets the index_name aas its first argument from Celery.
        By default, this is the only argument. If your analyzer needs more
        arguments you can override this method and return as a dictionary.

        If you want more than one instance to be created for your analyzer you
        can return a list of dictionaries with kwargs and each one will be
        instantiated and registered in Celery. This is neat if you want to run
        your analyzer with different arguments in parallel.

        Returns:
            Keyword arguments (dict) or a list of keyword argument dicts or None
            if no extra arguments are needed.
        """
        return None

    def run(self):
        raise NotImplementedError
