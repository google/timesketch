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
import random
import time
import traceback


import yaml

import opensearchpy
from flask import current_app
from jsonschema import validate, ValidationError, SchemaError

import pandas

from timesketch.api.v1 import utils as api_utils

from timesketch.lib import definitions
from timesketch.lib.datastores.opensearch import OpenSearchDataStore
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


logger = logging.getLogger("timesketch.analyzers")


def _flush_datastore_decorator(func):
    """Decorator that flushes the bulk insert queue in the datastore."""

    def wrapper(self, *args, **kwargs):
        func_return = func(self, *args, **kwargs)

        # Add in tagged events and emojis.
        for event_dict in self.tagged_events.values():
            event = event_dict.get("event")
            tags = event_dict.get("tags")

            event.commit({"tag": tags})

        for event_dict in self.emoji_events.values():
            event = event_dict.get("event")
            emojis = event_dict.get("emojis")

            event.commit({"__ts_emojis": emojis})

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
    path = os.path.join(os.path.sep, "etc", "timesketch", file_name)
    if os.path.isfile(path):
        return path

    path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", file_name)
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

    with open(path, "r") as fh:
        try:
            return yaml.safe_load(fh)
        except yaml.parser.ParserError as exception:
            # pylint: disable=logging-format-interpolation
            logger.warning(
                ("Unable to read in YAML config file, " "with error: {0!s}").format(
                    exception
                )
            )
            return {}


class Event(object):
    """Event object with helper methods.

    Attributes:
        datastore: Instance of OpenSearchDataStore.
        sketch: Sketch ID or None if not provided.
        event_id: ID of the Event.
        index_name: The name of the OpenSearch index.
        source: Source document from OpenSearch.
    """

    def __init__(self, event, datastore, sketch=None, analyzer=None):
        """Initialize Event object.

        Args:
            event: Dictionary of event from OpenSearch.
            datastore: Instance of OpenSearchDataStore.
            sketch: Optional instance of a Sketch object.
            analyzer: Optional instance of a BaseAnalyzer object.

        Raises:
            KeyError if event dictionary is missing mandatory fields.
        """
        self._analyzer = analyzer
        self.datastore = datastore
        self.sketch = sketch

        self.updated_event = {}

        try:
            self.event_id = event["_id"]
            self.index_name = event["_index"]
            self.timeline_id = event.get("_source", {}).get("__ts_timeline_id")
            self.source = event.get("_source", None)
        except KeyError as e:
            raise KeyError("Malformed event: {0!s}".format(e)) from e

    def _update(self, event):
        """Update event attributes to add.

        Args:
            event: Dictionary with new or updated values.
        """
        self.updated_event.update(event)

    def commit(self, event_dict=None):
        """Commit an event to OpenSearch.

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
            self.index_name,
            event_id=self.event_id,
            event=event_to_commit,
        )
        self.updated_event = {}

    def add_attributes(self, attributes):
        """Add key/values to an Event.

        Args:
            attributes: Dictionary with new or updated values to add.
        """
        # TODO: add attributes to the analyzer output object!
        if self._analyzer:
            self._analyzer.output.add_created_attributes(list(attributes.keys()))

        self._update(attributes)

    def add_label(self, label, toggle=False):
        """Add label to the Event.

        Args:
            label: Label name.
            toggle: If True the label will be removed if it exists already.

        Raises: RuntimeError of sketch ID is missing.
        """
        if not self.sketch:
            raise RuntimeError("No sketch provided.")

        user_id = 0
        updated_event = self.datastore.set_label(
            self.index_name,
            self.event_id,
            self.sketch.id,
            user_id,
            label,
            toggle=toggle,
            single_update=False,
        )
        self.commit(updated_event)

    def add_tags(self, tags):
        """Add tags to the Event.

        Args:
            tags: List of tags to add.
        """
        if not tags:
            return

        existing_tags = self.source.get("tag", [])
        if self._analyzer:
            if self.event_id in self._analyzer.tagged_events:
                existing_tags = self._analyzer.tagged_events[self.event_id].get("tags")
            else:
                self._analyzer.tagged_events[self.event_id] = {
                    "event": self,
                    "tags": existing_tags,
                }

        new_tags = list(set(existing_tags) | set(tags))
        if self._analyzer:
            self._analyzer.tagged_events[self.event_id]["tags"] = new_tags
        else:
            updated_event_attribute = {"tag": new_tags}
            self._update(updated_event_attribute)

        # Add new tags to the analyzer output object
        if self._analyzer:
            self._analyzer.output.add_created_tags(tags)

    def add_emojis(self, emojis):
        """Add emojis to the Event.

        Args:
            emojis: List of emojis to add (as unicode codepoints).
        """
        if not emojis:
            return

        existing_emoji_list = self.source.get("__ts_emojis", [])
        if not isinstance(existing_emoji_list, (list, tuple)):
            existing_emoji_list = []

        if self._analyzer:
            if self.event_id in self._analyzer.emoji_events:
                existing_emoji_list = self._analyzer.emoji_events[self.event_id].get(
                    "emojis"
                )
            else:
                self._analyzer.emoji_events[self.event_id] = {
                    "event": self,
                    "emojis": existing_emoji_list,
                }

        new_emoji_list = list(set().union(existing_emoji_list, emojis))

        if self._analyzer:
            self._analyzer.emoji_events[self.event_id]["emojis"] = new_emoji_list
        else:
            updated_event_attribute = {"__ts_emojis": new_emoji_list}
            self._update(updated_event_attribute)

    def add_star(self):
        """Star event."""
        self.add_label(label="__ts_star")

    def add_comment(self, comment):
        """Add comment to event.

        Args:
            comment: Comment string.

        Raises:
            RuntimeError: if no sketch is present.
        """
        if not self.sketch:
            raise RuntimeError("No sketch provided.")

        searchindex = SearchIndex.query.filter_by(index_name=self.index_name).first()
        db_event = SQLEvent.get_or_create(
            sketch=self.sketch.sql_sketch,
            searchindex=searchindex,
            document_id=self.event_id,
        )
        comment = SQLEvent.Comment(comment=comment, user=None)
        db_event.comments.append(comment)
        db_session.add(db_event)
        db_session.commit()
        self.add_label(label="__ts_comment")

    def get_comments(self):
        """Get comments for event.

        Returns:
            List of comments.

        Raises:
            RuntimeError: if no sketch is present.
        """
        if not self.sketch:
            raise RuntimeError("No sketch provided.")

        searchindex = SearchIndex.query.filter_by(index_name=self.index_name).first()
        db_event = SQLEvent.get_or_create(
            sketch=self.sketch.sql_sketch,
            searchindex=searchindex,
            document_id=self.event_id,
        )
        return db_event.comments

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
        existing_human_readable = self.source.get("human_readable", [])

        human_readable = "[{0:s}] {1:s}".format(analyzer_name, human_readable)

        if human_readable in existing_human_readable:
            return

        if append:
            existing_human_readable.append(human_readable)
        else:
            existing_human_readable.insert(0, human_readable)

        updated_human_readable = {"human_readable": existing_human_readable}
        self._update(updated_human_readable)


class Sketch(object):
    """Sketch object with helper methods.

    Attributes:
        id: Sketch ID.
        sql_sketch: Instance of a SQLAlchemy Sketch object.
    """

    def __init__(self, sketch_id, analyzer=None):
        """Initializes a Sketch object.

        Args:
            sketch_id: The Sketch ID.
        """
        self.id = sketch_id
        self.sql_sketch = SQLSketch.get_by_id(sketch_id)
        self._analyzer = analyzer

        if not self.sql_sketch:
            raise RuntimeError("No such sketch")

    def add_apex_aggregation(
        self, name, params, chart_type, description="", label=None, view_id=None
    ):
        """Add aggregation to the sketch using apex charts and tables.

        Note: since this is updating the database directly, the caller needs
        to ensure the chart type and parameters are valid since no checks are
        performed in this function.

        Args:
            name: the name.
            params: a dictionary of the parameters for the aggregation.
            chart_type: the chart type.
            description: the description, visible in the UI.
            label: string with a label to attach to the aggregation.
            view_id: optional ID of the view to attach the aggregation to.
        """
        if not name:
            raise ValueError("Aggregator name needs to be defined.")
        if not params:
            raise ValueError("Aggregator parameters have to be defined.")

        if view_id:
            view = View.get_by_id(view_id)
        else:
            view = None

        if "aggregator_name" not in params:
            raise ValueError("Aggregator name not specified")
        aggregator = params["aggregator_name"]

        aggregation = Aggregation.get_or_create(
            agg_type=aggregator,
            chart_type=chart_type,
            description=description,
            name=name,
            parameters=json.dumps(params, ensure_ascii=False),
            sketch=self.sql_sketch,
            user=None,
            view=view,
        )

        if label:
            aggregation.add_label(label)
        db_session.add(aggregation)
        db_session.commit()

        return aggregation

    def add_aggregation(
        self,
        name,
        agg_name,
        agg_params,
        description="",
        view_id=None,
        chart_type=None,
        label="",
    ):
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
            raise ValueError("Aggregator name needs to be defined.")
        if not agg_params:
            raise ValueError("Aggregator parameters have to be defined.")

        if view_id:
            view = View.get_by_id(view_id)
        else:
            view = None

        if chart_type:
            agg_params["supported_charts"] = chart_type

        agg_json = json.dumps(agg_params)
        aggregation = Aggregation.get_or_create(
            name=name,
            description=description,
            agg_type=agg_name,
            parameters=agg_json,
            chart_type=chart_type,
            user=None,
            sketch=self.sql_sketch,
            view=view,
        )

        if label:
            aggregation.add_label(label)
        db_session.add(aggregation)
        db_session.commit()
        return aggregation

    def add_aggregation_group(self, name, description="", view_id=None):
        """Add aggregation Group to the sketch.

        Args:
            name: the name of the aggregation run.
            description: optional description of the aggregation, visible in
                the UI.
            view_id: optional ID of the view to attach the aggregation to.
        """
        if not name:
            raise ValueError("Aggregator group name needs to be defined.")

        if view_id:
            view = View.get_by_id(view_id)
        else:
            view = None

        if not description:
            description = "Created by an analyzer"

        aggregation_group = SQLAggregationGroup.get_or_create(
            name=name,
            description=description,
            user=None,
            sketch=self.sql_sketch,
            view=view,
        )
        db_session.add(aggregation_group)
        db_session.commit()

        return AggregationGroup(aggregation_group)

    def add_view(
        self,
        view_name,
        analyzer_name,
        query_string=None,
        query_dsl=None,
        query_filter=None,
        additional_fields=None,
    ):
        """Add saved view to the Sketch.

        Args:
            view_name: The name of the view.
            analyzer_name: The name of the analyzer.
            query_string: OpenSearch query string.
            query_dsl: Dictionary with OpenSearch DSL query.
            query_filter: Dictionary with OpenSearch filters.
            additional_fields: A list with field names to include in the
                view output.

        Raises:
            ValueError: If both query_string an query_dsl are missing.

        Returns: An instance of a SQLAlchemy View object.
        """
        if not (query_string or query_dsl):
            raise ValueError("Both query_string and query_dsl are missing.")

        if not query_filter:
            query_filter = {"indices": "_all"}

        if additional_fields:
            query_filter["fields"] = [{"field": x.strip()} for x in additional_fields]

        description = "analyzer: {0:s}".format(analyzer_name)
        view = View.get_or_create(
            name=view_name, description=description, sketch=self.sql_sketch, user=None
        )
        view.description = description
        view.query_string = query_string
        view.query_filter = view.validate_filter(query_filter)
        view.query_dsl = query_dsl
        view.searchtemplate = None
        view.set_status(status="new")

        db_session.add(view)
        db_session.commit()

        # Add new view to the list of saved_views in the analyzer output object
        if self._analyzer:
            self._analyzer.output.add_saved_view(view.id)

        return view

    def add_sketch_attribute(self, name, values, ontology="text", overwrite=False):
        """Add an attribute to the sketch.

        Args:
            name (str): The name of the attribute
            values (list): A list of strings, which contains the values of the
                attribute.
            ontology (str): Ontology of the attribute, matches with
                data/ontology.yaml.
            overwrite (bool): If True and the attribute already exists,
                overwrite it.
        """
        # Check first whether the attribute already exists.
        attribute = Attribute.query.filter_by(name=name, sketch=self.sql_sketch).first()

        if not attribute:
            attribute = Attribute(
                user=None, sketch=self.sql_sketch, name=name, ontology=ontology
            )
            db_session.add(attribute)
            db_session.commit()

        if overwrite:
            attribute.values = []

        for value in values:
            attribute_value = AttributeValue(
                user=None, attribute=attribute, value=value
            )
            attribute.values.append(attribute_value)
            db_session.add(attribute_value)
            db_session.commit()

        db_session.add(attribute)
        db_session.commit()

    def get_sketch_attributes(self, name):
        """Get attributes from a sketch.

        Args:
            name (str): The name of the attribute.

        Returns:
            The value of the sketch attribute.
        """
        attributes = api_utils.get_sketch_attributes(self.sql_sketch)
        if name not in attributes:
            raise ValueError(f"Attribute {name} does not exist in sketch.")
        return attributes[name]["value"]

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
            title=title, sketch=self.sql_sketch, user=None
        ).first()

        if story:
            return Story(story)

        story = SQLStory.get_or_create(
            title=title, content="[]", sketch=self.sql_sketch, user=None
        )
        db_session.add(story)
        db_session.commit()

        # Add new story to the analyzer output object.
        if self._analyzer:
            self._analyzer.output.add_saved_story(story.id)

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
        self._orientation = "layer"
        self._parameters = ""

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
            aggregation_obj (Aggregation): the Aggregation object.
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

    def set_orientation(self, orientation="layer"):
        """Sets how charts should be joined.

        Args:
            orientation: string that contains how they should be connected
                together, That is the chart orientation,  the options are:
                "layer", "horizontal" and "vertical". The default behavior
                is "layer".
        """
        orientation = orientation.lower()
        if orientation == "layer" or orientation.starstwith("layer"):
            self._orientation = "layer"
        elif orientation == "horizontal" or orientation.startswith("hor"):
            self._orientation = "horizontal"
        elif orientation == "vertical" or orientation.startswith("ver"):
            self._orientation = "vertical"
        self.commit()

    def set_vertical(self):
        """Sets the "orientation" to vertical."""
        self._orientation = "vertical"
        self.commit()

    def set_horizontal(self):
        """Sets the "orientation" to horizontal."""
        self._orientation = "horizontal"
        self.commit()

    def set_layered(self):
        """Sets the "orientation" to layer."""
        self._orientation = "layer"
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
            parameter_string = ""
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
            "componentName": "",
            "componentProps": {},
            "content": "",
            "edit": False,
            "showPanel": False,
            "isActive": False,
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
                old_text = block.get("content")
                if not old_text:
                    continue
                if text == old_text:
                    return

        block = self._create_new_block()
        block["content"] = text
        self._commit(block)

    def add_aggregation(self, aggregation):
        """Add a saved aggregation to the Story.

        Args:
            aggregation (Aggregation): Saved aggregation to add to the story.
        """
        today = datetime.datetime.utcnow()
        block = self._create_new_block()

        block["componentName"] = "TsSavedVisualization"
        block["componentProps"] = {
            "name": aggregation.name,
            "savedVisualizationId": aggregation.id,
            "description": aggregation.description,
            "created_at": today.isoformat(),
            "updated_at": today.isoformat(),
            "user": {"username": None},
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
        block["componentName"] = "TsAggregationGroupCompact"
        block["componentProps"]["aggregation_group"] = {
            "id": aggregation_group.id,
            "name": aggregation_group.name,
        }
        self._commit(block)

    def add_view(self, view):
        """Add a saved view to the Story.

        Args:
            view (View): Saved view to add to the story.
        """
        block = self._create_new_block()
        block["componentName"] = "TsViewEventList"
        block["componentProps"]["view"] = {"id": view.id, "name": view.name}
        self._commit(block)


class BaseAnalyzer:
    """Base class for analyzers.

    Attributes:
        name: Analyzer name.
        index_name: Name of OpenSearch index.
        datastore: OpenSearch datastore client.
        sketch: Instance of Sketch object.
        timeline_id: The ID of the timeline the analyzer runs on.
        tagged_events: Dict with all events to add tags and those tags.
        emoji_events: Dict with all events to add emojis and those emojis.
    """

    NAME = "name"
    DISPLAY_NAME = None
    DESCRIPTION = None

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

    def __init__(self, index_name, sketch_id, timeline_id=None):
        """Initialize the analyzer object.

        Args:
            index_name: OpenSearch index name.
            sketch_id: Sketch ID.
            timeline_id: The timeline ID.
        """
        self.name = self.NAME
        self.index_name = index_name
        self.sketch = Sketch(sketch_id=sketch_id, analyzer=self)
        self.timeline_id = timeline_id
        self.timeline_name = ""

        self.tagged_events = {}
        self.emoji_events = {}

        self.datastore = OpenSearchDataStore(
            host=current_app.config["OPENSEARCH_HOST"],
            port=current_app.config["OPENSEARCH_PORT"],
        )

        # Add AnalyzerOutput instance and set all attributes that can be set
        # automatically
        self.output = AnalyzerOutput(
            analyzer_identifier=self.NAME,
            analyzer_name=self.DISPLAY_NAME,
            timesketch_instance=current_app.config.get(
                "EXTERNAL_HOST_URL", "https://localhost"
            ),
            sketch_id=sketch_id,
            timeline_id=timeline_id,
        )

        if not hasattr(self, "sketch"):
            self.sketch = None

    def event_pandas(
        self,
        query_string=None,
        query_filter=None,
        query_dsl=None,
        indices=None,
        return_fields=None,
    ):
        """Search OpenSearch.

        Args:
            query_string: Query string.
            query_filter: Dictionary containing filters to apply.
            query_dsl: Dictionary containing OpenSearch DSL query.
            indices: List of indices to query.
            return_fields: List of fields to be included in the search results,
                if not included all fields will be included in the results.

        Returns:
            A python pandas object with all the events.

        Raises:
            ValueError: if neither query_string or query_dsl is provided.
        """
        if not (query_string or query_dsl):
            raise ValueError("Both query_string and query_dsl are missing")

        if not query_filter:
            query_filter = {"indices": self.index_name, "size": 10000}

        if not indices:
            indices = [self.index_name]

        if self.timeline_id:
            timeline_ids = [self.timeline_id]
        else:
            timeline_ids = None

        # Refresh the index to make sure it is searchable.
        for index in indices:
            try:
                self.datastore.client.indices.refresh(index=index)
            except opensearchpy.NotFoundError:
                logger.error(
                    "Unable to refresh index: {0:s}, not found, "
                    "removing from list.".format(index)
                )
                broken_index = indices.index(index)
                _ = indices.pop(broken_index)

        if not indices:
            raise ValueError("Unable to get events, no indices to query.")

        if return_fields:
            default_fields = definitions.DEFAULT_SOURCE_FIELDS
            return_fields.extend(default_fields)
            return_fields = list(set(return_fields))
            return_fields = ",".join(return_fields)

        results = self.datastore.search_stream(
            sketch_id=self.sketch.id,
            query_string=query_string,
            query_filter=query_filter,
            query_dsl=query_dsl,
            indices=indices,
            timeline_ids=timeline_ids,
            return_fields=return_fields,
        )

        events = []
        for event in results:
            source = event.get("_source")
            source["_id"] = event.get("_id")
            source["_type"] = event.get("_type")
            source["_index"] = event.get("_index")
            events.append(source)

        return pandas.DataFrame(events)

    def event_stream(
        self,
        query_string=None,
        query_filter=None,
        query_dsl=None,
        indices=None,
        return_fields=None,
        scroll=True,
    ):
        """Search OpenSearch.

        Args:
            query_string: Query string.
            query_filter: Dictionary containing filters to apply.
            query_dsl: Dictionary containing OpenSearch DSL query.
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
            raise ValueError("Both query_string and query_dsl are missing")

        if not query_filter:
            query_filter = {"indices": self.index_name}

        # If not provided we default to the message field as this will always
        # be present.
        if not return_fields:
            return_fields = ["message"]

        # Make sure we always return tag, human_readable and emoji attributes.
        return_fields.extend(["tag", "human_readable", "__ts_emojis"])
        return_fields = list(set(return_fields))

        if not indices:
            indices = [self.index_name]

        # Refresh the index to make sure it is searchable.
        for index in indices:
            try:
                self.datastore.client.indices.refresh(index=index)
            except opensearchpy.NotFoundError:
                logger.error(
                    "Unable to find index: {0:s}, removing from "
                    "result set.".format(index)
                )
                broken_index = indices.index(index)
                _ = indices.pop(broken_index)
        if not indices:
            raise ValueError(
                "Unable to query for analyzers, discovered no index to query."
            )

        if self.timeline_id:
            timeline_ids = [self.timeline_id]
        else:
            timeline_ids = None

        # Exponential backoff for the call to OpenSearch. Sometimes the
        # cluster can be a bit overloaded and timeout on requests. We want to
        # retry a few times in order to give the cluster a chance to return
        # results.
        backoff_in_seconds = 3
        retries = 5
        for x in range(0, retries):
            try:
                event_generator = self.datastore.search_stream(
                    query_string=query_string,
                    query_filter=query_filter,
                    query_dsl=query_dsl,
                    indices=indices,
                    return_fields=return_fields,
                    enable_scroll=scroll,
                    timeline_ids=timeline_ids,
                )
                for event in event_generator:
                    yield Event(
                        event, self.datastore, sketch=self.sketch, analyzer=self
                    )
                break  # Query was successful
            except opensearchpy.TransportError as e:
                sleep_seconds = backoff_in_seconds * 2**x + random.uniform(3, 7)
                logger.info(
                    "Attempt: {0:d}/{1:d} sleeping {2:f} for query {3:s}".format(
                        x + 1, retries, sleep_seconds, query_string
                    )
                )
                time.sleep(sleep_seconds)

                if x == retries - 1:
                    logger.error(
                        "Timeout executing search for {0:s}: {1!s}".format(
                            query_string, e
                        ),
                        exc_info=True,
                    )
                    raise

    @_flush_datastore_decorator
    def run_wrapper(self, analysis_id):
        """A wrapper method to run the analyzer.

        This method is decorated to flush the bulk insert operation on the
        datastore. This makes sure that all events are indexed at exit.

        Returns:
            Return value of the run method.
        """
        analysis = Analysis.get_by_id(analysis_id)
        analysis.set_status("STARTED")

        timeline = analysis.timeline
        self.timeline_name = timeline.name
        searchindex = timeline.searchindex

        counter = 0
        while True:
            status = searchindex.get_status.status
            status = status.lower()
            if status == "ready":
                break

            if status == "fail":
                logger.error(
                    "Unable to run analyzer on a failed index ({0:s})".format(
                        searchindex.index_name
                    )
                )
                return "Failed"

            time.sleep(self.SECONDS_PER_WAIT)
            counter += 1
            if counter >= self.MAXIMUM_WAITS:
                logger.error(
                    "Indexing has taken too long time, aborting run of " "analyzer"
                )
                return "Failed"
            # Refresh the searchindex object.
            db_session.refresh(searchindex)

        # Run the analyzer. Broad Exception catch to catch any error and store
        # the error in the DB for display in the UI.
        try:
            result = self.run()
            analysis.set_status("DONE")
        except Exception:  # pylint: disable=broad-except
            analysis.set_status("ERROR")
            result = traceback.format_exc()

        # Update database analysis object with result and status
        analysis.result = "{0:s}".format(result)
        db_session.add(analysis)
        db_session.commit()

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
            List of keyword argument dicts or empty list if no extra arguments
            are needed.
        """
        return []

    def run(self):
        """Entry point for the analyzer."""
        raise NotImplementedError


class AnalyzerOutputException(Exception):
    """Analyzer output exception."""


class AnalyzerOutput:
    """A class to record timesketch analyzer output.

    Attributes:
        platform (str): [Required] Analyzer platform.
        analyzer_identifier (str): [Required] Unique analyzer identifier.
        analyzer_name (str): [Required] Analyzer display name.
        result_status (str): [Required] Analyzer result status.
            Valid values are success or error.
        result_priority (str): [Required] Priority of the result based on the
            analysis findings. Valid values are NOTE (default), LOW, MEDIUM, HIGH.
        result_summary (str): [Required] A summary statement of the analyzer
            finding. A result summary must exist even if there is no finding.
        result_markdown (str): [Optional] A detailed information about the
            analyzer finding in a markdown format.
        references (List[str]): [Optional] A list of references about the
            analyzer or the issue the analyzer attempts to address.
        result_attributes (dict): [Optional] A dict of key : value pairs that
            holds additional finding details.
        platform_meta_data: (dict): [Required] A dict of key : value pairs that
            holds the following information:
            timesketch_instance (str): [Required] The Timesketch instance URL.
            sketch_id (int): [Required] Timesketch sketch ID for this analyzer.
            timeline_id (int): [Required] Timesketch timeline ID for this analyzer.
            saved_views (List[int]): [Optional] Views generatred by the analyzer.
            saved_stories (List[int]): [Optional] Stories generated by the analyzer.
            saved_graphs (List[int|str]): [Optional] Graphs generated by the analyzer.
            saved_aggregations (List[int]): [Optional] Aggregations generated
                by the analyzer.
            created_tags (List[str]): [Optional] Tags created by the analyzer.
            created_attributes (List[str]): [Optional] Attributes created by
                the analyzer.
    """

    def __init__(
        self,
        analyzer_identifier,
        analyzer_name,
        timesketch_instance,
        sketch_id,
        timeline_id,
    ):
        """Initialize analyzer output."""
        self.platform = "timesketch"
        self.analyzer_identifier = analyzer_identifier
        self.analyzer_name = analyzer_name
        self.result_status = ""  # TODO: link to analyzer status/error?
        self.result_priority = "NOTE"
        self.result_summary = ""
        self.result_markdown = ""
        self.references = []
        self.result_attributes = {}
        self.platform_meta_data = {
            "timesketch_instance": timesketch_instance,
            "sketch_id": sketch_id,
            "timeline_id": timeline_id,
            "saved_views": [],
            "saved_stories": [],
            "saved_graphs": [],
            "saved_aggregations": [],
            "created_tags": [],
            "created_attributes": [],
        }

    def validate(self):
        """Validates the analyzer output and raises exception."""
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "platform": {"type": "string", "enum": ["timesketch"]},
                "analyzer_identifier": {"type": "string", "minLength": 1},
                "analyzer_name": {"type": "string", "minLength": 1},
                "result_status": {
                    "type": "string",
                    "enum": ["SUCCESS", "NO-FINDINGS", "ERROR"],
                },
                "result_priority": {
                    "type": "string",
                    "default": "NOTE",
                    "enum": ["HIGH", "MEDIUM", "LOW", "NOTE"],
                },
                "result_summary": {"type": "string", "minLength": 1},
                "result_markdown": {"type": "string", "minLength": 1},
                "references": {
                    "type": "array",
                    "items": [{"type": "string", "minLength": 1}],
                },
                "result_attributes": {"type": "object"},
                "platform_meta_data": {
                    "type": "object",
                    "properties": {
                        "timesketch_instance": {"type": "string", "minLength": 1},
                        "sketch_id": {"type": "integer"},
                        "timeline_id": {"type": "integer"},
                        "saved_views": {
                            "type": "array",
                            "items": [
                                {"type": "integer"},
                            ],
                        },
                        "saved_stories": {
                            "type": "array",
                            "items": [{"type": "integer"}],
                        },
                        "saved_graphs": {
                            "type": "array",
                            "items": [
                                {"type": ["integer", "string"]},
                            ],
                        },
                        "saved_aggregations": {
                            "type": "array",
                            "items": [
                                {"type": "integer"},
                            ],
                        },
                        "created_tags": {
                            "type": "array",
                            "items": [
                                {"type": "string"},
                            ],
                        },
                        "created_attributes": {
                            "type": "array",
                            "items": [
                                {"type": "string"},
                            ],
                        },
                    },
                    "required": [
                        "timesketch_instance",
                        "sketch_id",
                        "timeline_id",
                    ],
                },
            },
            "required": [
                "platform",
                "analyzer_identifier",
                "analyzer_name",
                "result_status",
                "result_priority",
                "result_summary",
                "platform_meta_data",
            ],
        }

        try:
            validate(instance=self.to_json(), schema=schema)
            return True
        except (ValidationError, SchemaError) as e:
            raise AnalyzerOutputException(f"json schema error: {e}") from e

    def add_reference(self, reference):
        """Adds a reference to the list of references.

        Args:
            reference: A reference e.g. URL to add to the list of references.
        """
        if not isinstance(reference, list):
            reference = [reference]
        self.references = list(set().union(self.references, reference))

    def set_meta_timesketch_instance(self, timesketch_instance):
        """Sets the timesketch instance URL.

        Args:
            timesketch_instance: The timesketch instance URL.
        """
        self.platform_meta_data["timesketch_instance"] = timesketch_instance

    def set_meta_sketch_id(self, sketch_id):
        """Sets the sketch ID.

        Args:
            sketch_id: The sketch ID.
        """
        self.platform_meta_data["sketch_id"] = sketch_id

    def set_meta_timeline_id(self, timeline_id):
        """Sets the timeline ID.

        Args:
            timeline_id: The timeline ID.
        """
        self.platform_meta_data["timeline_id"] = timeline_id

    def add_meta_item(self, key, item):
        """Handles the addition of platform_meta_data items.

        Args:
            key: The key to add to the platform_meta_data dict.
            item: The value to add to the platform_meta_data dict.
        """
        if not isinstance(item, list):
            item = [item]
        if key in self.platform_meta_data:
            self.platform_meta_data[key] = list(
                set(self.platform_meta_data[key]) | set(item)
            )
        else:
            self.platform_meta_data[key] = item

    def add_saved_view(self, view_id):
        """Adds a view ID to the list of saved_views.

        Args:
            view_id: The view ID to add to the list of saved_views.
        """
        self.add_meta_item("saved_views", view_id)

    def add_saved_story(self, story_id):
        """Adds a story ID to the list of saved_stories.

        Args:
            story_id: The story ID to add to the list of saved_stories.
        """
        self.add_meta_item("saved_stories", story_id)

    def add_saved_graph(self, graph_id):
        """Adds a graph ID to the list of saved_graphs.

        Args:
            graph_id: The graph ID to add to the list of saved_graphs.
        """
        self.add_meta_item("saved_graphs", graph_id)

    def add_saved_aggregation(self, aggregation_id):
        """Adds an aggregation ID to the list of saved_aggregations.

        Args:
            aggregation_id: The aggregation ID to add to the list of saved_aggregations.
        """
        self.add_meta_item("saved_aggregations", aggregation_id)

    def add_created_tags(self, tags):
        """Adds a tags to the list of created_tags.

        Args:
            tags: The tags to add to the list of created_tags.
        """
        existing_tags = self.platform_meta_data["created_tags"]
        analyzer_tags = list(set(existing_tags) | set(tags))
        self.add_meta_item("created_tags", analyzer_tags)

    def add_created_attributes(self, attributes):
        """Adds a attributes to the list of created_attributes.

        Args:
            attributes: The attributes to add to the list of created_attributes.
        """
        self.add_meta_item("created_attributes", attributes)

    def to_json(self) -> dict:
        """Returns JSON output of AnalyzerOutput. Filters out empty values."""
        # add required fields
        output = {
            "platform": self.platform,
            "analyzer_identifier": self.analyzer_identifier,
            "analyzer_name": self.analyzer_name,
            "result_status": self.result_status.upper(),
            "result_priority": self.result_priority.upper(),
            "result_summary": self.result_summary,
            "platform_meta_data": {
                "timesketch_instance": self.platform_meta_data["timesketch_instance"],
                "sketch_id": self.platform_meta_data["sketch_id"],
                "timeline_id": self.platform_meta_data["timeline_id"],
            },
        }

        # add optional fields if they are not empty
        if self.result_markdown and self.result_markdown != "":
            output["result_markdown"] = self.result_markdown

        if self.references:
            output["references"] = self.references

        if self.result_attributes:
            output["result_attributes"] = self.result_attributes

        if self.platform_meta_data["saved_views"]:
            output["platform_meta_data"]["saved_views"] = self.platform_meta_data[
                "saved_views"
            ]

        if self.platform_meta_data["saved_stories"]:
            output["platform_meta_data"]["saved_stories"] = self.platform_meta_data[
                "saved_stories"
            ]

        if self.platform_meta_data["saved_graphs"]:
            output["platform_meta_data"]["saved_graphs"] = self.platform_meta_data[
                "saved_graphs"
            ]

        if self.platform_meta_data["saved_aggregations"]:
            output["platform_meta_data"]["saved_aggregations"] = (
                self.platform_meta_data["saved_aggregations"]
            )

        if self.platform_meta_data["created_tags"]:
            output["platform_meta_data"]["created_tags"] = self.platform_meta_data[
                "created_tags"
            ]

        if self.platform_meta_data["created_attributes"]:
            output["platform_meta_data"]["created_attributes"] = (
                self.platform_meta_data["created_attributes"]
            )

        return output

    def __str__(self) -> str:
        """Returns string output of AnalyzerOutput."""
        if self.validate():
            return json.dumps(self.to_json())
        return ""
