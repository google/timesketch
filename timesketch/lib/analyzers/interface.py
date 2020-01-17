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

import json
import logging
import os
import traceback
import yaml

import pandas

from flask import current_app
from timesketch.lib import definitions
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.models import db_session
from timesketch.models.sketch import Aggregation
from timesketch.models.sketch import Event as SQLEvent
from timesketch.models.sketch import Sketch as SQLSketch
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import View
from timesketch.models.sketch import Analysis


def _flush_datastore_decorator(func):
    """Decorator that flushes the bulk insert queue in the datastore."""
    def wrapper(self, *args, **kwargs):
        func_return = func(self, *args, **kwargs)
        self.datastore.flush_queued_events()
        return func_return
    return wrapper

def get_config_path(file_name):
    """Returns a path to a configuration file.

    Args:
        file_name: String that defines the config file name.

    Returns:
        The path to the configuration file or None if the file cannot be found.
    """
    path = os.path.join(os.path.sep, 'etc', 'timesketch', file_name)
    if os.path.isfile(path):
        return path

    path = os.path.join(
        os.path.dirname(__file__), '..', '..', '..', 'data', file_name)
    path = os.path.abspath(path)
    if os.path.isfile(path):
        return path

    return None


def get_yaml_config(file_name):
    """Return a dict parsed from a YAML file within the config directory.

    Args:
        file_name: String that defines the config file name.

    Returns:
        A dict with the parsed YAML content from the config file or
        an empty dict if the file is not found or YAML was unable
        to parse it.
    """
    path = get_config_path(file_name)
    if not path:
        return {}

    with open(path, 'r') as fh:
        try:
            return yaml.safe_load(fh)
        except yaml.parser.ParserError as exception:
            # pylint: disable=logging-format-interpolation
            logging.warning((
                'Unable to read in YAML config file, '
                'with error: {0!s}').format(exception))
            return {}


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

        self.updated_event = {}

        try:
            self.event_id = event['_id']
            self.event_type = event['_type']
            self.index_name = event['_index']
            self.source = event.get('_source', None)
        except KeyError as e:
            raise KeyError('Malformed event: {0!s}'.format(e))

    def _update(self, event):
        """Update event attributes to add.

        Args:
            event: Dictionary with new or updated values.
        """
        self.updated_event.update(event)

    def commit(self, event_dict=None):
        """Commit an event to Elasticsearch.

        Args:
            event_dict: (optional) Dictionary with updated event attributes.
            Defaults to self.updated_event.
        """
        if event_dict:
            event_to_commit = event_dict
        else:
            event_to_commit = self.updated_event

        if not event_to_commit:
            return

        self.datastore.import_event(
            self.index_name, self.event_type, event_id=self.event_id,
            event=event_to_commit)
        self.updated_event = {}

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
        self.commit(updated_event)

    def add_tags(self, tags):
        """Add tags to the Event.

        Args:
            tags: List of tags to add.
        """
        if not tags:
            return

        existing_tags = self.source.get('tag', [])
        new_tags = list(set().union(existing_tags, tags))
        updated_event_attribute = {'tag': new_tags}
        self._update(updated_event_attribute)

    def add_emojis(self, emojis):
        """Add emojis to the Event.

        Args:
            emojis: List of emojis to add (as unicode codepoints).
        """
        if not emojis:
            return

        existing_emoji_list = self.source.get('__ts_emojis', [])
        if not isinstance(existing_emoji_list, (list, tuple)):
            existing_emoji_list = []
        new_emoji_list = list(set().union(existing_emoji_list, emojis))
        updated_event_attribute = {'__ts_emojis': new_emoji_list}
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

    def add_human_readable(self, human_readable, analyzer_name, append=True):
        """Add a human readable string to event.

        Args:
            human_readable: human readable string.
            analyzer_name: string with the name of the analyzer that was
                used to generate the human_readable string.
            append: boolean defining whether the data should be appended
                or prepended to the human readable string, if it has already
                been defined. Defaults to True, and does nothing if
                human_readable is not defined.
        """
        existing_human_readable = self.source.get('human_readable', [])

        human_readable = '[{0:s}] {1:s}'.format(analyzer_name, human_readable)

        if human_readable in existing_human_readable:
            return

        if append:
            existing_human_readable.append(human_readable)
        else:
            existing_human_readable.insert(0, human_readable)

        updated_human_readable = {'human_readable': existing_human_readable}
        self._update(updated_human_readable)


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

    def add_aggregation(
            self, name, agg_name, agg_params, description='', view_id=None,
            chart_type=None):
        """Add aggregation to the sketch.

        Args:
            name: the name of the aggregation run.
            agg_name: the name of the aggregation class to run.
            agg_params: a dictionary of the parameters for the aggregation.
            description: description of the aggregation, visible in the UI,
                this is optional.
            view_id: optional ID of the view to attach the aggregation to.
            chart_type: string representing the chart type.
        """
        if not agg_name:
            raise ValueError('Aggregator name needs to be defined.')
        if not agg_params:
            raise ValueError('Aggregator parameters have to be defined.')

        if view_id:
            view = View.query.get(view_id)
        else:
            view = None

        agg_json = json.dumps(agg_params)
        aggregation = Aggregation.get_or_create(
            name=name, description=description, agg_type=agg_name,
            parameters=agg_json, chart_type=chart_type, user=None,
            sketch=self.sql_sketch, view=view)
        db_session.add(aggregation)
        db_session.commit()
        return aggregation

    def add_view(self, view_name, analyzer_name, query_string=None,
                 query_dsl=None, query_filter=None):
        """Add saved view to the Sketch.

        Args:
            view_name: The name of the view.
            analyzer_name: The name of the analyzer.
            query_string: Elasticsearch query string.
            query_dsl: Dictionary with Elasticsearch DSL query.
            query_filter: Dictionary with Elasticsearch filters.

        Raises:
            ValueError: If both query_string an query_dsl are missing.

        Returns: An instance of a SQLAlchemy View object.
        """
        if not (query_string or query_dsl):
            raise ValueError('Both query_string and query_dsl are missing.')

        if not query_filter:
            query_filter = {'indices': '_all'}

        name = '[{0:s}] {1:s}'.format(analyzer_name, view_name)
        view = View.get_or_create(name=name, sketch=self.sql_sketch, user=None)
        view.query_string = query_string
        view.query_filter = view.validate_filter(query_filter)
        view.query_dsl = query_dsl
        view.searchtemplate = None

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

    # If this analyzer depends on another analyzer
    # it needs to be included in this frozenset by using
    # the indexer names.
    DEPENDENCIES = frozenset()

    # Used as hints to the frontend UI in order to render input forms.
    FORM_FIELDS = []

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

    def event_stream(
            self, query_string=None, query_filter=None, query_dsl=None,
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
        if not (query_string or query_dsl):
            raise ValueError('Both query_string and query_dsl are missing')

        if not query_filter:
            query_filter = {'indices': self.index_name}

        # If not provided we default to the message field as this will always
        # be present.
        if not return_fields:
            return_fields = ['message']

        # Make sure we always return tag, human_readable and emoji attributes.
        return_fields.extend(['tag', 'human_readable', '__ts_emojis'])
        return_fields = list(set(return_fields))

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
    def run_wrapper(self, analysis_id):
        """A wrapper method to run the analyzer.

        This method is decorated to flush the bulk insert operation on the
        datastore. This makes sure that all events are indexed at exit.

        Returns:
            Return value of the run method.
        """
        analysis = Analysis.query.get(analysis_id)
        analysis.set_status('STARTED')

        # Run the analyzer. Broad Exception catch to catch any error and store
        # the error in the DB for display in the UI.
        try:
            result = self.run()
            analysis.set_status('DONE')
        except Exception:  # pylint: disable=broad-except
            analysis.set_status('ERROR')
            result = traceback.format_exc()

        # Update database analysis object with result and status
        analysis.result = '{0:s}'.format(result)
        db_session.add(analysis)
        db_session.commit()

        return result

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

    def event_pandas(
            self, query_string=None, query_filter=None, query_dsl=None,
            indices=None, return_fields=None):
        """Search ElasticSearch.

        Args:
            query_string: Query string.
            query_filter: Dictionary containing filters to apply.
            query_dsl: Dictionary containing Elasticsearch DSL query.
            indices: List of indices to query.
            return_fields: List of fields to be included in the search results,
                if not included all fields will be included in the results.

        Returns:
            A python pandas object with all the events.

        Raises:
            ValueError: if neither query_string or query_dsl is provided.
        """
        if not (query_string or query_dsl):
            raise ValueError('Both query_string and query_dsl are missing')

        if not query_filter:
            query_filter = {'indices': self.index_name, 'size': 10000}

        if not indices:
            indices = [self.index_name]

        # Refresh the index to make sure it is searchable.
        for index in indices:
            self.datastore.client.indices.refresh(index=index)

        if return_fields:
            default_fields = definitions.DEFAULT_SOURCE_FIELDS
            return_fields.extend(default_fields)
            return_fields = list(set(return_fields))
            return_fields = ','.join(return_fields)

        results = self.datastore.search_stream(
            sketch_id=self.sketch.id,
            query_string=query_string,
            query_filter=query_filter,
            query_dsl=query_dsl,
            indices=indices,
            return_fields=return_fields,
        )

        events = []
        for event in results:
            source = event.get('_source')
            source['_id'] = event.get('_id')
            source['_type'] = event.get('_type')
            source['_index'] = event.get('_index')
            events.append(source)

        return pandas.DataFrame(events)

    def run(self):
        """Entry point for the analyzer."""
        raise NotImplementedError
