# Copyright 2024 Google Inc. All rights reserved.
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
"""This file contains a class for managing DFIQ analyzers."""

import importlib
import inspect
import json
import logging
import os

from timesketch.lib.aggregators import manager as aggregator_manager
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager as analyzer_manager
from timesketch.models.sketch import Timeline

logger = logging.getLogger("timesketch.analyzers.dfiq_plugins.manager")


def load_dfiq_analyzers():
    """Loads DFIQ analyzer classes."""

    DFIQ_ANALYZER_PATH = os.path.dirname(os.path.abspath(__file__))

    # Clear existing registrations before reloading
    for name, analyzer_class in analyzer_manager.AnalysisManager.get_analyzers(
        include_dfiq=True
    ):
        if (
            hasattr(analyzer_class, "IS_DFIQ_ANALYZER")
            and analyzer_class.IS_DFIQ_ANALYZER
        ):
            try:
                analyzer_manager.AnalysisManager.deregister_analyzer(name)
                logger.info("Deregistered DFIQ analyzer: %s", name)
            except KeyError as e:
                logger.error(str(e))

    # Dynamically load DFIQ Analyzers
    for filename in os.listdir(DFIQ_ANALYZER_PATH):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = os.path.splitext(filename)[0]  # Remove .py extension
            if module_name == "manager" or module_name.endswith("_test"):
                continue
            module_path = f"timesketch.lib.analyzers.dfiq_plugins.{module_name}"
            try:
                module = importlib.import_module(module_path)
                for name, obj in inspect.getmembers(module):
                    if name not in [
                        "interface",
                        "logger",
                        "logging",
                        "manager",
                    ] and not name.startswith("__"):
                        if (
                            inspect.isclass(obj)
                            and issubclass(obj, interface.BaseAnalyzer)
                            and hasattr(obj, "IS_DFIQ_ANALYZER")
                            and obj.IS_DFIQ_ANALYZER
                        ):
                            analyzer_manager.AnalysisManager.register_analyzer(obj)
                            logger.info("Registered DFIQ analyzer: %s", obj.NAME)
                        else:
                            logger.error(
                                'Skipped loading "%s" as analyzer, since it did'
                                " not meet the requirements.",
                                str(module_path),
                            )
            except ImportError as error:
                logger.error(
                    "Failed to import dfiq analyzer module: %s, %s",
                    str(module_path),
                    str(error),
                )


class DFIQAnalyzerManager:
    """Manager for executing DFIQ analyzers."""

    def __init__(self, sketch):
        """Initializes the manager.

        Args:
            sketch: The sketch object.
        """
        self.sketch = sketch
        self.aggregator_manager = aggregator_manager
        self.aggregation_max_tries = 3

    def trigger_analyzers_for_approach(self, approach):
        """Triggers DFIQ analyzers for a newly added approach.

        Args:
           approach (InvestigativeQuestionApproach): An approach object to link
                    with the analyssis

        Returns:
            analyzer_sessions or None
        """
        dfiq_analyzers = self._get_dfiq_analyzer(approach)

        analyzer_sessions = []
        if dfiq_analyzers:
            analyzer_sessions = self._run_dfiq_analyzers(dfiq_analyzers, approach)

        return analyzer_sessions if analyzer_sessions else False

    def trigger_analyzers_for_timelines(self, timelines):
        """Triggers DFIQ analyzers for a newly added timeline.

        Args:
            timelines [<timesketch.models.sketch.Timeline>]: List of timeline
                     objects.

        Returns:
            analyzer_sessions or None
        """
        if isinstance(timelines, Timeline):
            timelines = [timelines]
        analyzer_sessions = []
        for approach in self._find_analyzer_approaches():
            dfiq_analyzers = self._get_dfiq_analyzer(approach)
            if dfiq_analyzers:
                session = self._run_dfiq_analyzers(
                    dfiq_analyzers=dfiq_analyzers,
                    approach=approach,
                    timelines=timelines,
                )
                if session:
                    analyzer_sessions.extend(session)

        return analyzer_sessions if analyzer_sessions else False

    def _find_analyzer_approaches(self):
        """Finds approaches with a defined analyzer step.

        Returns:
            A list of InvestigativeQuestionApproach objects that have a defined
            analyzer step in their specification.
        """
        approaches = []
        for question in self.sketch.questions:
            for approach in question.approaches:
                approach_spec = json.loads(approach.spec_json)
                if any(
                    step.get("stage") == "analysis"
                    and step.get("type") == "timesketch-analyzer"
                    for step in approach_spec.get("steps", [])
                ):
                    approaches.append(approach)
        return approaches

    def _get_dfiq_analyzer(self, approach):
        """Checks if the approach has analyzer steps to execute."""
        dfiq_analyzers = set()
        approach_spec = json.loads(approach.spec_json)
        if approach_spec.get("steps"):
            for step in approach_spec.get("steps"):
                if (
                    step.get("stage") == "analysis"
                    and step.get("type") == "timesketch-analyzer"
                ):
                    dfiq_analyzers.add(step.get("value"))

        return dfiq_analyzers

    def _get_analyzers_by_data_type(self, dfiq_analyzers):
        """Groups DFIQ analyzers by their required data types.

        Args:
            dfiq_analyzers (set): A set of DFIQ analyzer names.

        Returns:
            dict: A dictionary mapping data types to lists of analyzer names.
                  The special key "ALL" will be used for classical analyzers
                  and DFIQ analyzers that don't have a REQUIRED_DATA_TYPES
                  attribute (i.e., an empty list). It will trigger the analyzer
                  to run on all timelines in the sketch.
        """
        analyzer_by_datatypes = {}
        for (
            analyzer_name,
            analyzer_class,
        ) in analyzer_manager.AnalysisManager.get_analyzers(include_dfiq=True):
            if analyzer_name not in dfiq_analyzers:
                continue

            required_data_types = getattr(analyzer_class, "REQUIRED_DATA_TYPES", [])
            if not required_data_types:
                # Classical or DFIQ analyzer without REQUIRED_DATA_TYPES
                analyzer_by_datatypes.setdefault("ALL", []).append(analyzer_class.NAME)
            else:
                for data_type in required_data_types:
                    analyzer_by_datatypes.setdefault(data_type, []).append(
                        analyzer_class.NAME
                    )
        return analyzer_by_datatypes

    def _get_data_types_per_timeline(self, timelines=None):
        """Retrieves data types present in each eligible timeline.

        Args:
            timelines: (optional) A list of timeline objects.

        Returns:
            dict: A dictionary mapping timeline IDs to lists of data types.
        """
        if not timelines:
            timelines = self.sketch.timelines

        datatype_per_timeline = {}
        for timeline in timelines:
            if timeline.get_status.status.lower() != "ready":
                continue

            aggregation = self.aggregator_manager.AggregatorManager.get_aggregator(
                "field_bucket"
            )(sketch_id=self.sketch.id, timeline_ids=[timeline.id])
            agg_result = aggregation.run(field="data_type", limit="1000")
            datatype_per_timeline[timeline.id] = [
                entry["data_type"] for entry in agg_result.values
            ]
        return datatype_per_timeline

    def _run_dfiq_analyzers(self, dfiq_analyzers, approach, timelines=None):
        """Executes DFIQ analyzers on matching timelines.

        Args:
            dfiq_analyzers (set): A set of DFIQ analyzer names.
            approach (InvestigativeQuestionApproach): An approach object to link
                     with the analyssis
            timelines ([<Timeline>]): Optional list of timelines to limit the
                      analysis on.

        Returns:
            list: A list of analyzer sessions (potentially empty).
        """
        analyzer_by_datatypes = self._get_analyzers_by_data_type(dfiq_analyzers)
        if not analyzer_by_datatypes:
            logger.error(
                "None of the requested DFIQ analyzers exist on this Timesketch "
                "instance Requested: %s",
                str(dfiq_analyzers),
            )
            return []

        datatype_per_timeline = self._get_data_types_per_timeline(timelines)
        analyzer_by_timeline = {}
        for timeline_id, timeline_datatypes in datatype_per_timeline.items():
            analyzer_by_timeline[timeline_id] = []
            for data_type, analyzer_names in analyzer_by_datatypes.items():
                # Handle classical analyzers by always including them.
                if data_type == "ALL":
                    analyzer_by_timeline[timeline_id].extend(analyzer_names)
                elif data_type in timeline_datatypes:
                    analyzer_by_timeline[timeline_id].extend(analyzer_names)

        # Import here to avoid circular imports.

        from timesketch.lib import tasks

        sessions = []
        for timeline_id, analyzer_names in analyzer_by_timeline.items():
            if not analyzer_names:
                continue
            timeline = Timeline.get_by_id(timeline_id)
            if not timeline or timeline.status[0].status != "ready":
                continue
            try:
                analyzer_group, session = tasks.build_sketch_analysis_pipeline(
                    sketch_id=self.sketch.id,
                    searchindex_id=timeline.searchindex.id,
                    user_id=approach.user.id,
                    analyzer_names=analyzer_names,
                    analyzer_kwargs=None,
                    timeline_id=timeline_id,
                    analyzer_force_run=False,
                    include_dfiq=True,
                    approach_id=approach.id,
                )
            except KeyError as e:
                logger.warning(
                    "Unable to build analyzer pipeline, analyzer does not exist: %s",
                    str(e),
                )
                continue
            if analyzer_group:
                pipeline = (
                    tasks.run_sketch_init.s([timeline.searchindex.index_name])
                    | analyzer_group
                )
                pipeline.apply_async()

            if session:
                sessions.append(session)

        return sessions
