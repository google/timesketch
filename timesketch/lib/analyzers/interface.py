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
"""Interface for analyzers."""

from __future__ import unicode_literals

from flask import current_app
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.models import db_session
from timesketch.models.sketch import Event as SQLEvent
from timesketch.models.sketch import Sketch as SQLSketch
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import View


def _flush_datastore_decorator(func):
    """Decorator that flushes the bulk insert queue in the datastore."""
    def wrapper(self, *args, **kwargs):
        func_return = func(self, *args, **kwargs)
        self.datastore.flush_queued_events()
        return func_return
    return wrapper


class Event(object):
    """Event object with helper methods.

    Attributes:
        datastore: Instance of ElasticsearchDatastore.
        sketch: Sketch ID or None if not provided.
        event_id: ID of the Event.
        event_type: Document type in Elasticsearch.
        index_name: The name of the Elasticsearch index.
        source: Source document from Elasticsearch.
    """
    def __init__(self, event, datastore, sketch=None):
        """Initialize Event object.

        Args:
            event: Dictionary of event from Elasticsearch.
            datastore: Instance of ElasticsearchDatastore.
            sketch: Optional instance of a Sketch object.

        Raises:
            KeyError if event dictionary is missing mandatory fields.
        """
        self.datastore = datastore
        self.sketch = sketch

        try:
            self.event_id = event['_id']
            self.event_type = event['_type']
            self.index_name = event['_index']
            self.source = event.get('_source', None)
        except KeyError as e:
            raise KeyError('Malformed event: {0:s}'.format(e))

    def _update(self, event):
        """Update Event in Elasticsearch.

        Args:
            event: Dictionary with new or updated values.
        """
        self.datastore.import_event(
            self.index_name, self.event_type, event_id=self.event_id,
            event=event)

    def add_attributes(self, attributes):
        """Add key/values to an Event.

        Args:
            attributes: Dictionary with new or updated values to add.
        """
        self._update(attributes)

    def add_label(self, label, toggle=False):
        """Add label to the Event.

        Args:
            label: Label name.
            toggle: If True the label will be removed if it exists already.

        Raises: RuntimeError of sketch ID is missing.
        """
        if not self.sketch:
            raise RuntimeError('No sketch provided.')

        user_id = 0
        updated_event = self.datastore.set_label(
            self.index_name, self.event_id, self.event_type, self.sketch.id,
            user_id, label, toggle=toggle, single_update=False)
        self._update(updated_event)

    def add_tags(self, tags):
        """Add tags to the Event.

        Args:
            tags: List of tags to add.
        """
        existing_tags = self.source.get('tag', [])
        new_tags = list(set().union(existing_tags, tags))
        updated_event_attribute = {'tag': new_tags}
        self._update(updated_event_attribute)

    def add_star(self):
        """Star event."""
        self.add_label(label='__ts_star')

    def add_comment(self, comment):
        """Add comment to event.

        Args:
            comment: Comment string.

        Raises:
            RuntimeError: if no sketch is present.
        """
        if not self.sketch:
            raise RuntimeError('No sketch provided.')

        searchindex = SearchIndex.query.filter_by(
            index_name=self.index_name).first()
        db_event = SQLEvent.get_or_create(
            sketch=self.sketch.sql_sketch, searchindex=searchindex,
            document_id=self.event_id)
        comment = SQLEvent.Comment(comment=comment, user=None)
        db_event.comments.append(comment)
        db_session.add(db_event)
        db_session.commit()
        self.add_label(label='__ts_comment')


class Sketch(object):
    """Sketch object with helper methods.

    Attributes:
        id: Sketch ID.
        sql_sketch: Instance of a SQLAlchemy Sketch object.
    """
    def __init__(self, sketch_id):
        """Initializes a Sketch object.

        Args:
            sketch_id: The Sketch ID.
        """
        self.id = sketch_id
        self.sql_sketch = SQLSketch.query.get(sketch_id)

        if not self.sql_sketch:
            raise RuntimeError('No such sketch')

    def add_view(self, name, query_string=None, query_dsl=None,
                 query_filter=None):
        """Add saved view to the Sketch.

        Args:
            name: The name of the view.
            query_string: Elasticsearch query string.
            query_dsl: Dictionary with Elasticsearch DSL query.
            query_filter: Dictionary with Elasticsearch filters.

        Raises:
            ValueError: If both query_string an query_dsl are missing.

        Returns: An instance of a SQLAlchemy View object.
        """
        if not query_string or query_dsl:
            raise ValueError('Both query_string and query_dsl are missing.')

        if not query_filter:
            query_filter = {}

        view = View(name=name, sketch=self.sql_sketch, user=None,
                    query_string=query_string, query_filter=query_filter,
                    query_dsl=query_dsl, searchtemplate=None)

        view.query_filter = view.validate_filter(query_filter)
        db_session.add(view)
        db_session.commit()
        return view

    def get_all_indices(self):
        """List all indices in the Sketch.

        Returns:
            List of index names.
        """
        active_timelines = self.sql_sketch.active_timelines
        indices = [t.searchindex.index_name for t in active_timelines]
        return indices


class BaseIndexAnalyzer(object):
    """Base class for analyzers.

    Attributes:
        name: Analyzer name.
        index_name: Name if Elasticsearch index.
        datastore: Elasticsearch datastore client.
        sketch: Instance of Sketch object.
    """

    NAME = 'name'
    IS_SKETCH_ANALYZER = False

    def __init__(self, index_name):
        """Initialize the analyzer object.

        Args:
            index_name: Elasticsearch index name.
        """
        self.name = self.NAME
        self.index_name = index_name
        self.datastore = ElasticsearchDataStore(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])

        if not hasattr(self, 'sketch'):
            self.sketch = None

    def event_stream(self, query_string, query_filter=None, query_dsl=None,
                     indices=None, return_fields=None):
        """Search ElasticSearch.

        Args:
            query_string: Query string.
            query_filter: Dictionary containing filters to apply.
            query_dsl: Dictionary containing Elasticsearch DSL query.
            indices: List of indices to query.
            return_fields: List of fields to return.

        Returns:
            Generator of Event objects.

        Raises:
            ValueError: if neither query_string or query_dsl is provided.
        """

        if not query_string or query_dsl:
            raise ValueError('Both query_string and query_dsl are missing')

        if not query_filter:
            query_filter = {}

        # If not provided we default to the message field as this will always
        # be present.
        if not return_fields:
            return_fields = 'message'

        if not indices:
            indices = [self.index_name]

        # Refresh the index to make sure it is searchable.
        for index in indices:
            self.datastore.client.indices.refresh(index=index)

        event_generator = self.datastore.search_stream(
            query_string=query_string,
            query_filter=query_filter,
            query_dsl=query_dsl,
            indices=indices,
            return_fields=return_fields
        )
        for event in event_generator:
            yield Event(event, self.datastore, sketch=self.sketch)

    @_flush_datastore_decorator
    def run_wrapper(self):
        """A wrapper method to run the analyzer.

        This method is decorated to flush the bulk insert operation on the
        datastore. This makes sure that all events are indexed at exit.

        Returns:
            Return value of the run method.
        """
        result = self.run()
        return result

    @classmethod
    def get_kwargs(cls):
        """Get keyword arguments needed to instantiate the class.

        Every analyzer gets the index_name as its first argument from Celery.
        By default this is the only argument. If your analyzer need more
        arguments you can override this method and return as a dictionary.

        If you want more than one instance to be created for your analyzer you
        can return a list of dictionaries with kwargs and each one will be
        instantiated and registered in Celery. This is neat if you want to run
        your analyzer with different arguments in parallel.

        Returns:
            List of keyword argument dicts or None if no extra arguments are
            needed.
        """
        return None

    def run(self):
        """Entry point for the analyzer."""
        raise NotImplementedError


class BaseSketchAnalyzer(BaseIndexAnalyzer):
    """Base class for sketch analyzers.

    Attributes:
        sketch: A Sketch instance.
    """

    NAME = 'name'
    IS_SKETCH_ANALYZER = True

    def __init__(self, index_name, sketch_id):
        """Initialize the analyzer object.

        Args:
            index_name: Elasticsearch index name.
            sketch_id: Sketch ID.
        """
        self.sketch = Sketch(sketch_id=sketch_id)
        super(BaseSketchAnalyzer, self).__init__(index_name)

    def run(self):
        """Entry point for the analyzer."""
        raise NotImplementedError
