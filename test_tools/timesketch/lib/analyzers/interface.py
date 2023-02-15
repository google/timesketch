# Copyright 2020 Google Inc. All rights reserved.
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
"""Mock interface for analyzers."""

from __future__ import unicode_literals

import codecs
import collections
import csv
import json
import logging
import os
import traceback
import uuid

import pandas

from timesketch.lib import definitions


logger = logging.getLogger("test_tool.analyzer_run")


# Define named tuples to track changes made to events and sketches.
EVENT_CHANGE = collections.namedtuple("event_change", "type, source, what")
SKETCH_CHANGE = collections.namedtuple("sketch_change", "type, source, what")

VIEW_OBJECT = collections.namedtuple("view", "id, name")
AGG_OBJECT = collections.namedtuple("aggregation", "id, name parameters")


def get_config_path(file_name):
    """Returns a path to a configuration file.

    Args:
        file_name: String that defines the config file name.

    Returns:
        The path to the configuration file or an empty string if the file
        cannot be found.
    """
    path = os.path.join("etc", "timesketch", file_name)
    if os.path.isfile(path):
        return os.path.abspath(path)

    path = os.path.join("data", file_name)
    if os.path.isfile(path):
        return os.path.abspath(path)

    path = os.path.join(os.path.dirname(__file__), "..", "data", file_name)
    path = os.path.abspath(path)
    if os.path.isfile(path):
        return path

    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "..", "..", "data", file_name
    )
    path = os.path.abspath(path)
    if os.path.isfile(path):
        return path

    return ""


class AnalyzerContext(object):
    """Report object for analyzer run."""

    def __init__(self, analyzer_name):
        """Initialize the report object."""
        self.analyzer_name = analyzer_name
        self.analyzer_result = ""
        self.error = None
        self.event_cache = {}
        self.failed = False
        self.sketch = None
        self.queries = []

    def get_string_report(self):
        """Returns a string describing the changes made by the analyzer."""
        return_strings = ["-" * 80]
        return_strings.append("{0:^80s}".format(self.analyzer_name))
        return_strings.append("-" * 80)
        return_strings.append(
            "Total number of events: {0:d}".format(len(self.event_cache))
        )
        return_strings.append(
            "Total number of queries: {0:d}".format(len(self.queries))
        )

        return_strings.append("")
        return_strings.append("+" * 80)
        for qid, query in enumerate(self.queries):
            return_strings.append("  -- Query #{0:02d} --".format(qid + 1))
            for key, value in query.items():
                return_strings.append("{0:>20s}: {1!s}".format(key, value))

        if self.failed:
            return "\n".join(return_strings)

        if self.sketch and self.sketch.updates:
            return_strings.append("")
            return_strings.append("+" * 80)
            return_strings.append("Sketch updates:")
            for update in self.sketch.updates:
                return_strings.append(
                    "  {0:s} {1:s}".format(update.type, update.source)
                )
                return_strings.append("\t{0!s}".format(update.what))

        return_strings.append("")
        return_strings.append("+" * 80)
        return_strings.append("Event Updates:")
        event_container = {}
        for event in self.event_cache.values():
            if not event.updates:
                continue
            for update in event.updates:
                type_string = "{0:s} {1:s}".format(update.type, update.source)
                event_container.setdefault(type_string, collections.Counter())
                event_container[type_string]["{0!s}".format(update.what)] += 1

        for key, counter in event_container.items():
            return_strings.append("  {0:s}".format(key))
            for value, count in counter.most_common():
                return_strings.append("\t[{0:d}] {1:s}\n".format(count, value))
        return_strings.append("")
        return_strings.append("+" * 80)
        return_strings.append("Result from analyzer run:")
        return_strings.append("  {0:s}".format(self.analyzer_result))
        return_strings.append("=-" * 40)

        if self.error:
            return_strings.append("Error occurred:\n{0:s}".format(self.error))
        return "\n".join(return_strings)

    def add_event(self, event):
        """Add an event to the cache.

        Args:
              event: instance of Event.
        """
        if event.event_id not in self.event_cache:
            self.event_cache[event.event_id] = event

    def add_query(self, query_string=None, query_dsl=None, indices=None, fields=None):
        """Add a query string or DSL to the context.

        Args:
            query_string: Query string.
            query_dsl: Dictionary containing OpenSearch DSL query.
            indices: List of indices to query.
            fields: List of fields to return.
        """
        query = {
            "string": query_string,
            "dsl": query_dsl,
            "indices": indices,
            "fields": fields,
        }
        self.queries.append(query)

    def remove_event(self, event):
        """Remove an event from the context.

        Args:
              event: instance of Event.
        """
        if event.event_id not in self.event_cache:
            raise ValueError("Event {0:s} not in cache.".format(event.event_id))
        del self.event_cache[event.event_id]

    def update_event(self, event):
        """Update an event that is already stored in the context.

        Args:
              event: instance of Event.
        """
        if event.event_id not in self.event_cache:
            self.add_event(event)
            return
        self.event_cache[event.event_id] = event


def get_yaml_config(unusued_file_name):  # pylint: disable-msg=unused-argument
    """Return an empty dict.

    This is only implemented to make sure that analyzers attempting
    to call this function still work.

    Args:
        unused_file_name: String that defines the config file name.

    Returns:
        An empty dict.
    """
    return {}


class Event(object):
    """Event object with helper methods.

    Attributes:
        datastore: Instance of OpenSearchDatastore (mocked as None).
        sketch: Sketch ID or None if not provided.
        event_id: ID of the Event.
        index_name: The name of the OpenSearch index.
        source: Source document from OpenSearch.
        updates: A list of all changes made to an event, with each change
            stored as a EVENT_CHANGE named tuple.
    """

    def __init__(self, event, datastore=None, sketch=None, context=None):
        """Initialize Event object.

        Args:
            event: Dictionary of event from OpenSearch.
            datastore: Defaults to none, should be None as this is mocked.
            sketch: Optional instance of a Sketch object.
            context: Optional context object (instance of Context).

        """
        self.datastore = datastore
        self.sketch = sketch
        self._context = context

        self.updated_event = {}
        self.updates = []

        self.event_id = uuid.uuid4().hex
        self.index_name = "mocked_index"
        self.source = event

    def _update_change(self, change=None):
        """Update the status of an event.

        Args:
            change: optional change object (instance of a namedtuple).
                    If supplied the context will be updated with the
                    change information.
        """
        if change:
            self.updates.append(change)

        if self._context:
            self._context.update_event(self)

    def commit(self, event_dict=None):
        """Mock the commit of an event to OpenSearch.

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

        self.updated_event = event_to_commit
        self._update_change()

    def add_attributes(self, attributes):
        """Add key/values to an Event.

        Args:
            attributes: Dictionary with new or updated values to add.
        """
        change = EVENT_CHANGE("ADD", "attribute", attributes)
        self._update_change(change)

    def add_label(self, label, toggle=False):
        """Add label to the Event.

        Args:
            label: Label name.
            toggle: If True the label will be removed if it exists already.

        Raises:
            RuntimeError of sketch ID is missing.
        """
        if not self.sketch:
            raise RuntimeError("No sketch provided.")

        if toggle:
            event_type = "UPDATE"
        else:
            event_type = "ADD"
        change = EVENT_CHANGE(event_type, "label", label)
        self._update_change(change)

    def add_tags(self, tags):
        """Add tags to the Event.

        Args:
            tags: List of tags to add.
        """
        if not tags:
            return

        change = EVENT_CHANGE("ADD", "tag", tags)
        self._update_change(change)

    def add_emojis(self, emojis):
        """Add emojis to the Event.

        Args:
            emojis: List of emojis to add (as unicode codepoints).
        """
        if not emojis:
            return

        change = EVENT_CHANGE("ADD", "emoji", emojis)
        self._update_change(change)

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

        change = EVENT_CHANGE("ADD", "comment", comment)
        self._update_change(change)
        self.add_label(label="__ts_comment")

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
        human_readable = "[{0:s}] {1:s}".format(analyzer_name, human_readable)

        if append:
            event_type = "ADD"
        else:
            event_type = "PREPEND"

        change = EVENT_CHANGE(event_type, "human_readable", human_readable)
        self._update_change(change)


class Sketch(object):
    """Sketch object with helper methods.

    Attributes:
        id: Sketch ID.
        updates: A list of all changes made to an event, with each change
            stored as a SKETCH_CHANGE namedtuple.
    """

    def __init__(self, sketch_id):
        """Initializes a Sketch object.

        Args:
            sketch_id: The Sketch ID.
        """
        self.id = sketch_id
        self.updates = []
        self._context = None

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

        params = {
            "name": name,
            "agg_name": agg_name,
            "agg_params": agg_params,
            "description": description,
            "view_id": view_id,
            "chart_type": chart_type,
            "label": label,
        }
        change = SKETCH_CHANGE("ADD", "aggregation", params)
        self.updates.append(change)

        agg_obj = AGG_OBJECT(1, name, agg_params)
        return agg_obj

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

        if not description:
            description = "Created by an analyzer"

        params = {"name": name, "description": description, "view_id": view_id}
        change = SKETCH_CHANGE("ADD", "aggregation_group", params)
        self.updates.append(change)

        return AggregationGroup(
            analyzer=self,
            name=name,
            description=description,
            user=None,
            sketch=self.id,
            view=view_id,
        )

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

        name = "[{0:s}] {1:s}".format(analyzer_name, view_name)
        params = {
            "name": name,
            "query_string": query_string,
            "query_dsl": query_dsl,
            "query_filter": query_filter,
            "additional_fields": additional_fields,
        }
        change = SKETCH_CHANGE("ADD", "view", params)
        self.updates.append(change)

        view = VIEW_OBJECT(1, name)
        return view

    def add_sketch_attribute(self, name, values, ontology="text"):
        """Add an attribute to the sketch.

        Args:
            name (str): The name of the attribute
            values (list): A list of strings, which contains the values of the
                attribute.
            ontology (str): Ontology of the attribute, matches with
                data/ontology.yaml.
        """
        params = {
            "name": name,
            "values": values,
            "ontology": ontology,
        }
        change = SKETCH_CHANGE("ADD", "sketch_attribute", params)
        self.updates.append(change)

    def add_story(self, title):
        """Add a story to the Sketch.

        Args:
            title: The name of the view.

        Raises:
            ValueError: If both query_string an query_dsl are missing.

        Returns:
            An instance of a Story object.
        """
        params = {
            "title": title,
        }
        change = SKETCH_CHANGE("ADD", "story", params)
        self.updates.append(change)

        story = Story(self, title=title)
        return story

    def get_all_indices(self):
        """List all indices in the Sketch.
        Returns:
            An empty list.
        """
        return []

    def set_context(self, context):
        """Sets the context of the analyzer.

        Args:
            context: Context object (instance of AnalyzerContext).
        """
        self._context = context


class BaseAnalyzer(object):
    """Base class for analyzers.

    Attributes:
        name: Analyzer name.
        index_name: Mocked index name.
        sketch: Instance of Sketch object.
    """

    NAME = "name"
    IS_SKETCH_ANALYZER = False

    # If this analyzer depends on another analyzer
    # it needs to be included in this frozenset by using
    # the indexer names.
    DEPENDENCIES = frozenset()

    # Used as hints to the frontend UI in order to render input forms.
    FORM_FIELDS = []

    def __init__(self, file_name):
        """Initialize the analyzer object.

        Args:
            file_name: the file path to the test event file.
        """
        self.datastore = None
        self.index_name = "mocked_index"
        self.name = self.NAME
        if not os.path.isfile(file_name):
            raise IOError(
                "Unable to read in data, file not found: {0:s}".format(file_name)
            )
        self._file_name = file_name
        self._context = None

        if not hasattr(self, "sketch"):
            self.sketch = None

    def event_stream(
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
            return_fields: List of fields to return.

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
            indices = ["MOCKED_INDEX"]

        if self._context:
            self._context.add_query(
                query_string=query_string,
                query_dsl=query_dsl,
                indices=indices,
                fields=return_fields,
            )

        _, _, file_extension = self._file_name.rpartition(".")
        file_extension = file_extension.lower()
        if file_extension not in ["csv", "jsonl"]:
            raise ValueError(
                "Unable to parse the test file [{0:s}] unless it has the "
                "extension of either .csv or .jsonl".format(self._file_name)
            )

        with codecs.open(self._file_name, encoding="utf-8", errors="replace") as fh:
            if file_extension == "csv":
                reader = csv.DictReader(fh)
                for row in reader:
                    event = Event(row, sketch=self.sketch, context=self._context)
                    if self._context:
                        self._context.add_event(event)
                    yield event
            elif file_extension == "jsonl":
                for row in fh:
                    event = Event(
                        json.loads(row), sketch=self.sketch, context=self._context
                    )
                    if self._context:
                        self._context.add_event(event)
                    yield event

    def run_wrapper(self):
        """A wrapper method to run the analyzer.

        This method is decorated to flush the bulk insert operation on the
        datastore. This makes sure that all events are indexed at exit.
        """
        # Run the analyzer. Broad Exception catch to catch any error and store
        # the error in the DB for display in the UI.
        try:
            result = self.run()
        except Exception:  # pylint: disable=broad-except
            if self._context:
                self._context.error = traceback.format_exc()
            logger.error(
                "Unable to run the analyzer.\nMake sure the test data "
                "contains all the necessary information to run."
                "\n\nThe traceback for the execution is:\n\n",
                exc_info=True,
            )
            self._context.failed = True
            return

        # Update database analysis object with result and status
        if self._context:
            self._context.result = "{0:s}".format(result)
            self._context.analyzer_result = result

    def run(self):
        """Entry point for the analyzer."""
        raise NotImplementedError

    def set_context(self, context):
        """Sets the context of the analyzer.

        Args:
            context: Context object (instance of AnalyzerContext).
        """
        self._context = context
        # In some cases we need the context to be provided yet the analyzers
        # will not have a chance to provide it, and thus we mock it by
        # replacing the datastore with a context, since the datstore is not
        # used in the mocked scenario.
        self.datastore = context


class BaseSketchAnalyzer(BaseAnalyzer):
    """Base class for sketch analyzers.

    Attributes:
        sketch: A Sketch instance.
    """

    NAME = "name"
    IS_SKETCH_ANALYZER = True

    def __init__(self, file_name, sketch_id):
        """Initialize the analyzer object.

        Args:
            file_name: the file path to the test event file.
            sketch_id: Sketch ID.
        """
        self.sketch = Sketch(sketch_id=sketch_id)
        super().__init__(file_name)

    def set_context(self, context):
        """Sets the context of the analyzer.

        Args:
            context: Context object (instance of AnalyzerContext).
        """
        super().set_context(context)
        self._context.sketch = self.sketch
        self.sketch.set_context(self._context)

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
            indices = ["MOCKED_INDEX"]

        if return_fields:
            default_fields = definitions.DEFAULT_SOURCE_FIELDS
            return_fields.extend(default_fields)
            return_fields = list(set(return_fields))
            return_fields = ",".join(return_fields)

        self._context.add_query(
            query_string=query_string,
            query_dsl=query_dsl,
            indices=indices,
            fields=return_fields,
        )

        data_frame = pandas.read_csv(self._file_name)
        data_frame = data_frame.assign(_id=lambda x: uuid.uuid4().hex)
        data_frame["_type"] = "mocked_event"
        data_frame["_index"] = "mocked_index"

        return data_frame

    def run(self):
        """Entry point for the analyzer."""
        raise NotImplementedError


class Story(object):
    """Mocked story object."""

    def __init__(self, analyzer, title):
        """Initialize the story."""
        self.id = 1
        self.title = title
        self._analyzer = analyzer

    def add_aggregation(self, aggregation, agg_type=""):
        """Add a saved aggregation to the Story.

        Args:
            aggregation (Aggregation): Saved aggregation to add to the story.
            agg_type (str): string indicating the type of aggregation, can be:
                "table" or the name of the chart to be used, eg "barcharct",
                "hbarchart".
        """
        parameter_dict = aggregation.parameters
        if agg_type:
            parameter_dict["supported_charts"] = agg_type
        else:
            agg_type = parameter_dict.get("supported_charts")
            # Neither agg_type nor supported_charts is set.
            if not agg_type:
                agg_type = "table"
                parameter_dict["supported_charts"] = "table"

        params = {
            "agg_id": aggregation.id,
            "agg_name": aggregation.name,
            "agg_type": agg_type,
            "agg_params": parameter_dict,
        }
        change = SKETCH_CHANGE("STORY_ADD", "aggregation", params)
        self._analyzer.updates.append(change)

    def add_aggregation_group(self, aggregation_group):
        """Add an aggregation group to the Story.

        Args:
            aggregation_group (SQLAggregationGroup): Save aggregation group
                to add to the story.
        """
        if not isinstance(aggregation_group, AggregationGroup):
            return

        params = {
            "group_id": aggregation_group.id,
            "group_name": aggregation_group.name,
        }
        change = SKETCH_CHANGE("STORY_ADD", "aggregation_group", params)
        self._analyzer.updates.append(change)

    def add_text(self, text, skip_if_exists=False):
        """Add a text block to the Story.

        Args:
            text (str): text (markdown is supported) to add to the story.
            skip_if_already_there (boolean): if set to True then the text
                will not be added if a block with this text already exists.
        """
        params = {
            "text": text,
            "skip_if_exists": skip_if_exists,
        }
        change = SKETCH_CHANGE("STORY_ADD", "text", params)
        self._analyzer.updates.append(change)

    def add_view(self, view):
        """Add a saved view to the story.

        Args:
            view (View): Saved view to add to the story.
        """
        params = {"view_id": view.id, "view_name": view.name}
        change = SKETCH_CHANGE("STORY_ADD", "view", params)
        self._analyzer.updates.append(change)


class AggregationGroup(object):
    """Aggregation Group object with helper methods.

    Attributes:
        group (SQLAlchemy): Instance of a SQLAlchemy AggregationGroup object.
    """

    def __init__(self, analyzer, name, description, user, sketch, view):
        """Initializes the AggregationGroup object."""
        self._analyzer = analyzer
        self._name = name
        self._description = description
        self._user = user
        self._sketch = sketch
        self._view = view

        self._orientation = "layer"
        self._parameters = ""

    @property
    def id(self):
        """Returns the group ID."""
        return 1

    @property
    def name(self):
        """Returns the group name."""
        return self._name

    def add_aggregation(self, aggregation_obj):
        """Add an aggregation object to the group.

        Args:
            aggregation_obj (Aggregation): the Aggregation objec.
        """
        params = {
            "agg_id": aggregation_obj.id,
            "agg_name": aggregation_obj.name,
        }
        change = SKETCH_CHANGE("AGGREGATION_GROUP_ADD", "aggregation", params)
        self._analyzer.updates.append(change)

    def commit(self):
        """Commit changes to DB."""
        change = SKETCH_CHANGE("AGGREGATION_GROUP_CHANGE", "commit_issued", {})
        self._analyzer.updates.append(change)

    def set_orientation(self, orientation="layer"):
        """Sets how charts should be joined.

        Args:
            orienation: string that contains how they should be connected
                together, That is the chart orientation,  the options are:
                "layer", "horizontal" and "vertical". The default behavior
                is "layer".
        """
        orientation = orientation.lower()
        params = {
            "orientation": orientation,
        }
        change = SKETCH_CHANGE("AGGREGATION_GROUP_CHANGE", "orientation", params)
        self._analyzer.updates.append(change)

    def set_vertical(self):
        """Sets the "orienation" to vertical."""
        self.set_orientation("vertical")

    def set_horizontal(self):
        """Sets the "orientation" to horizontal."""
        self.set_orientation("horizontal")

    def set_layered(self):
        """Sets the "orientation" to layer."""
        self.set_orientation("layer")

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

        params = {
            "parameters": parameter_string,
        }
        change = SKETCH_CHANGE("AGGREGATION_GROUP_CHANGE", "parameters", params)
        self._analyzer.updates.append(change)
        self._parameters = parameter_string
