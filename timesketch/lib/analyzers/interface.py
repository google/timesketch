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

import datetime
import json
import logging
import os
import time
import traceback
import yaml

from flask import current_app

import pandas

from timesketch.lib import definitions
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.models import db_session
from timesketch.models.sketch import Aggregation
from timesketch.models.sketch import Attribute
from timesketch.models.sketch import AttributeValue
from timesketch.models.sketch import AggregationGroup as SQLAggregationGroup
from timesketch.models.sketch import Event as SQLEvent
from timesketch.models.sketch import Sketch as SQLSketch
from timesketch.models.sketch import Story as SQLStory
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import View
from timesketch.models.sketch import Analysis


logger = logging.getLogger('timesketch.analyzers')


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
            logger.warning((
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
            event=event_to_commit, flush_interval=1)
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
            chart_type=None, label=''):
        """Add aggregation to the sketch.

        Args:
            name: the name of the aggregation run.
            agg_name: the name of the aggregation class to run.
            agg_params: a dictionary of the parameters for the aggregation.
            description: description of the aggregation, visible in the UI,
                this is optional.
            view_id: optional ID of the view to attach the aggregation to.
            chart_type: string representing the chart type.
            label: string with a label to attach to the aggregation.
        """
        if not agg_name:
            raise ValueError('Aggregator name needs to be defined.')
        if not agg_params:
            raise ValueError('Aggregator parameters have to be defined.')

        if view_id:
            view = View.query.get(view_id)
        else:
            view = None

        if chart_type:
            agg_params['supported_charts'] = chart_type

        agg_json = json.dumps(agg_params)
        aggregation = Aggregation.get_or_create(
            name=name, description=description, agg_type=agg_name,
            parameters=agg_json, chart_type=chart_type, user=None,
            sketch=self.sql_sketch, view=view)

        if label:
            aggregation.add_label(label)
        db_session.add(aggregation)
        db_session.commit()
        return aggregation

    def add_aggregation_group(self, name, description='', view_id=None):
        """Add aggregation Group to the sketch.

        Args:
            name: the name of the aggregation run.
            description: optional description of the aggregation, visible in
                the UI.
            view_id: optional ID of the view to attach the aggregation to.
        """
        if not name:
            raise ValueError('Aggregator group name needs to be defined.')

        if view_id:
            view = View.query.get(view_id)
        else:
            view = None

        if not description:
            description = 'Created by an analyzer'

        aggregation_group = SQLAggregationGroup.get_or_create(
            name=name, description=description, user=None,
            sketch=self.sql_sketch, view=view)
        db_session.add(aggregation_group)
        db_session.commit()

        return AggregationGroup(aggregation_group)

    def add_view(self, view_name, analyzer_name, query_string=None,
                 query_dsl=None, query_filter=None, additional_fields=None):
        """Add saved view to the Sketch.

        Args:
            view_name: The name of the view.
            analyzer_name: The name of the analyzer.
            query_string: Elasticsearch query string.
            query_dsl: Dictionary with Elasticsearch DSL query.
            query_filter: Dictionary with Elasticsearch filters.
            additional_fields: A list with field names to include in the
                view output.

        Raises:
            ValueError: If both query_string an query_dsl are missing.

        Returns: An instance of a SQLAlchemy View object.
        """
        if not (query_string or query_dsl):
            raise ValueError('Both query_string and query_dsl are missing.')

        if not query_filter:
            query_filter = {'indices': '_all'}

        if additional_fields:
            query_filter['fields'] = [
                {'field': x.strip()} for x in additional_fields]

        description = 'analyzer: {0:s}'.format(analyzer_name)
        view = View.get_or_create(
            name=view_name, description=description, sketch=self.sql_sketch,
            user=None)
        view.description = description
        view.query_string = query_string
        view.query_filter = view.validate_filter(query_filter)
        view.query_dsl = query_dsl
        view.searchtemplate = None
        view.set_status(status='new')

        db_session.add(view)
        db_session.commit()
        return view

    def add_sketch_attribute(self, name, values, ontology='text'):
        """Add an attribute to the sketch.

        Args:
            name (str): The name of the attribute
            values (list): A list of strings, which contains the values of the
                attribute.
            ontology (str): Ontology of the attribute, matches with
                data/ontology.yaml.
        """
        # Check first whether the attribute already exists.
        attribute = Attribute.query.filter_by(name=name).first()

        if not attribute:
            attribute = Attribute(
                user=None,
                sketch=self.sql_sketch,
                name=name,
                ontology=ontology)
            db_session.add(attribute)
            db_session.commit()

        for value in values:
            attribute_value = AttributeValue(
                user=None,
                attribute=attribute,
                value=value)

            attribute.values.append(attribute_value)
            db_session.add(attribute_value)
            db_session.commit()

        db_session.add(attribute)
        db_session.commit()

    def add_story(self, title):
        """Add a story to the Sketch.

        Args:
            title: The name of the view.

        Raises:
            ValueError: If both query_string an query_dsl are missing.

        Returns:
            An instance of a Story object.
        """
        story = SQLStory.query.filter_by(
            title=title, sketch=self.sql_sketch, user=None).first()

        if story:
            return Story(story)

        story = SQLStory.get_or_create(
            title=title, content='[]', sketch=self.sql_sketch, user=None)
        db_session.add(story)
        db_session.commit()
        return Story(story)

    def get_all_indices(self):
        """List all indices in the Sketch.
        Returns:
            List of index names.
        """
        active_timelines = self.sql_sketch.active_timelines
        indices = [t.searchindex.index_name for t in active_timelines]
        return indices


class AggregationGroup(object):
    """Aggregation Group object with helper methods.

    Attributes:
        group (SQLAlchemy): Instance of a SQLAlchemy AggregationGroup object.
    """
    def __init__(self, aggregation_group):
        """Initializes the AggregationGroup object.

        Args:
            aggregation_group: SQLAlchemy AggregationGroup object.
        """
        self.group = aggregation_group
        self._orientation = 'layer'
        self._parameters = ''

    @property
    def id(self):
        """Returns the group ID."""
        return self.group.id

    @property
    def name(self):
        """Returns the group name."""
        return self.group.name

    def add_aggregation(self, aggregation_obj):
        """Add an aggregation object to the group.

        Args:
            aggregation_obj (Aggregation): the Aggregation objec.
        """
        self.group.aggregations.append(aggregation_obj)
        self.group.orientation = self._orientation
        db_session.add(aggregation_obj)
        db_session.add(self.group)
        db_session.commit()

    def commit(self):
        """Commit changes to DB."""
        self.group.orientation = self._orientation
        self.group.parameters = self._parameters
        db_session.add(self.group)
        db_session.commit()

    def set_orientation(self, orientation='layer'):
        """Sets how charts should be joined.

        Args:
            orienation: string that contains how they should be connected
                together, That is the chart orientation,  the options are:
                "layer", "horizontal" and "vertical". The default behavior
                is "layer".
        """
        orientation = orientation.lower()
        if orientation == 'layer' or orientation.starstwith('layer'):
            self._orientation = 'layer'
        elif orientation == 'horizontal' or orientation.startswith('hor'):
            self._orientation = 'horizontal'
        elif orientation == 'vertical' or orientation.startswith('ver'):
            self._orientation = 'vertical'
        self.commit()

    def set_vertical(self):
        """Sets the "orienation" to vertical."""
        self._orientation = 'vertical'
        self.commit()

    def set_horizontal(self):
        """Sets the "orientation" to horizontal."""
        self._orientation = 'horizontal'
        self.commit()

    def set_layered(self):
        """Sets the "orientation" to layer."""
        self._orientation = 'layer'
        self.commit()

    def set_parameters(self, parameters=None):
        """Sets the parameters for the aggregation group.

        Args:
            parameters: a JSON string or a dict with the parameters
                for the aggregation group.
        """
        if isinstance(parameters, dict):
            parameter_string = json.dumps(parameters)
        elif isinstance(parameters, str):
            parameter_string = parameters
        elif parameters is None:
            parameter_string = ''
        else:
            parameter_string = str(parameters)
        self._parameters = parameter_string
        self.commit()


class Story(object):
    """Story object with helper methods.

    Attributes:
        story (SQLAlchemy): Instance of a SQLAlchemy Story object.
    """
    def __init__(self, story):
        """Initializes a Story object.

        Args:
            story: SQLAlchemy Story object.
        """
        self.story = story

    @property
    def data(self):
        """Return back the content of the story object."""
        return json.loads(self.story.content)

    @staticmethod
    def _create_new_block():
        """Create a new block to be added to a Story.

        Returns:
            Dictionary with default block content.
        """
        block = {
            'componentName': '',
            'componentProps': {},
            'content': '',
            'edit': False,
            'showPanel': False,
            'isActive': False
        }
        return block

    def _commit(self, block):
        """Commit the Story to database.

        Args:
            block (dict): Block to add.
        """
        story_blocks = json.loads(self.story.content)
        story_blocks.append(block)
        self.story.content = json.dumps(story_blocks)
        db_session.add(self.story)
        db_session.commit()

    def add_text(self, text, skip_if_exists=False):
        """Add a text block to the Story.

        Args:
            text (str): text (markdown is supported) to add to the story.
            skip_if_exists (boolean): if set to True then the text
                will not be added if a block with this text already exists.
        """
        if skip_if_exists and self.data:
            for block in self.data:
                if not block:
                    continue
                if not isinstance(block, dict):
                    continue
                old_text = block.get('content')
                if not old_text:
                    continue
                if text == old_text:
                    return

        block = self._create_new_block()
        block['content'] = text
        self._commit(block)

    def add_aggregation(self, aggregation, agg_type=''):
        """Add a saved aggregation to the Story.

        Args:
            aggregation (Aggregation): Saved aggregation to add to the story.
            agg_type (str): string indicating the type of aggregation, can be:
                "table" or the name of the chart to be used, eg "barcharct",
                "hbarchart". Defaults to the value of supported_charts.
        """
        today = datetime.datetime.utcnow()
        block = self._create_new_block()
        parameter_dict = json.loads(aggregation.parameters)
        if agg_type:
            parameter_dict['supported_charts'] = agg_type
        else:
            agg_type = parameter_dict.get('supported_charts')
            # Neither agg_type nor supported_charts is set.
            if not agg_type:
                agg_type = 'table'
                parameter_dict['supported_charts'] = 'table'

        block['componentName'] = 'TsAggregationCompact'
        block['componentProps']['aggregation'] = {
            'agg_type': aggregation.agg_type,
            'id': aggregation.id,
            'name': aggregation.name,
            'chart_type': agg_type,
            'description': aggregation.description,
            'created_at': today.isoformat(),
            'updated_at': today.isoformat(),
            'parameters': json.dumps(parameter_dict),
            'user': {'username': None},
            }
        self._commit(block)

    def add_aggregation_group(self, aggregation_group):
        """Add an aggregation group to the Story.

        Args:
            aggregation_group (SQLAggregationGroup): Save aggregation group
                to add to the story.
        """
        if not isinstance(aggregation_group, AggregationGroup):
            return

        block = self._create_new_block()
        block['componentName'] = 'TsAggregationGroupCompact'
        block['componentProps']['aggregation_group'] = {
            'id': aggregation_group.id,
            'name': aggregation_group.name}
        self._commit(block)

    def add_view(self, view):
        """Add a saved view to the Story.

        Args:
            view (View): Saved view to add to the story.
        """
        block = self._create_new_block()
        block['componentName'] = 'TsViewEventList'
        block['componentProps']['view'] = {'id': view.id, 'name': view.name}
        self._commit(block)


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

    # Configure how long an analyzer should run before the timeline
    # gets fully indexed.
    SECONDS_PER_WAIT = 10
    MAXIMUM_WAITS = 360

    def __init__(self, index_name):
        """Initialize the analyzer object.

        Args:
            index_name: Elasticsearch index name.
        """
        self.name = self.NAME
        self.index_name = index_name
        self.timeline_name = ''
        self.datastore = ElasticsearchDataStore(
            host=current_app.config['ELASTIC_HOST'],
            port=current_app.config['ELASTIC_PORT'])

        if not hasattr(self, 'sketch'):
            self.sketch = None

    def event_stream(
            self, query_string=None, query_filter=None, query_dsl=None,
            indices=None, return_fields=None, scroll=True):
        """Search ElasticSearch.

        Args:
            query_string: Query string.
            query_filter: Dictionary containing filters to apply.
            query_dsl: Dictionary containing Elasticsearch DSL query.
            indices: List of indices to query.
            return_fields: List of fields to return.
            scroll: Boolean determining whether we support scrolling searches
                or not. Defaults to True.

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
            return_fields=return_fields,
            enable_scroll=scroll,
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

        timeline = analysis.timeline
        self.timeline_name = timeline.name
        searchindex = timeline.searchindex

        counter = 0
        while True:
            status = searchindex.get_status.status
            status = status.lower()
            if status == 'ready':
                break

            if status == 'fail':
                logger.error(
                    'Unable to run analyzer on a failed index ({0:s})'.format(
                        searchindex.index_name))
                return 'Failed'

            time.sleep(self.SECONDS_PER_WAIT)
            counter += 1
            if counter >= self.MAXIMUM_WAITS:
                logger.error(
                    'Indexing has taken too long time, aborting run of '
                    'analyzer')
                return 'Failed'
            # Refresh the searchindex object.
            db_session.refresh(searchindex)

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
