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
from timesketch.models import db_session
from timesketch.models.sketch import Event as SQLEvent
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import SearchIndex


def _flush_datastore_decorator(func):
    """Decorator that flushes the bulk insert queue on the datastore."""
    def wrapper(self, *args, **kwargs):
        func_return = func(self, *args, **kwargs)
        self.datastore.flush_queued_events()
        return func_return
    return wrapper


class Event(object):
    def __init__(self, event, datastore, sketch_id=None):
        self.datastore = datastore
        self.sketch_id = sketch_id

        try:
            self.event_id = event.get('_id')
            self.event_type = event.get('_type')
            self.index_name = event.get('_index')
            self.source = event.get('_source')
        except KeyError:
            raise KeyError('Malformed event')

    def _update(self, event):
        """Update an event."""
        self.datastore.import_event(
            self.index_name, self.event_type, event_id=self.event_id,
            event=event)

    def add_attributes(self, attributes):
        self._update(attributes)

    def add_label(self, label, toggle=False):
        if not self.sketch_id:
            raise RuntimeError('No sketch_id provided.')

        user_id = 0
        updated_event = self.datastore.set_label(
            self.index_name, self.event_id, self.event_type, self.sketch_id,
            user_id, label, toggle=toggle, single_update=False)
        self._update(updated_event)

    def add_tags(self, tags):
        try:
            existing_tags = self.source['tag']
        except KeyError:
            existing_tags = []

        new_tags = list(set().union(existing_tags, tags))
        updated_event_attribute = {'tag': new_tags}
        self._update(updated_event_attribute)

    def add_star(self):
        self.add_label(label='__ts_star')

    def add_comment(self, comment):
        sketch = Sketch.query.get(self.sketch_id)
        searchindex = SearchIndex.query.filter_by(
            index_name=self.index_name).first()
        db_event = SQLEvent.get_or_create(
            sketch=sketch, searchindex=searchindex, document_id=self.event_id)
        comment = SQLEvent.Comment(comment=comment, user=None)
        db_event.comments.append(comment)
        db_session.add(db_event)
        db_session.commit()
        self.add_label(label='__ts_comment')


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

    def event_stream(self, query_string, query_filter=None, return_fields=None):
        if not query_filter:
            query_filter = {}

        if not return_fields:
            return_fields = 'message'

        # Refresh the index to make sure it is searchable.
        self.datastore.client.indices.refresh(index=self.index_name)

        event_generator = self.datastore.search_stream(
            query_string=query_string,
            query_filter=query_filter,
            indices=[self.index_name],
            return_fields=return_fields
        )
        for event in event_generator:
            yield Event(event, self.datastore, sketch_id=4716)

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
