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

import logging
import json

from timesketch.models.sketch import Timeline
from timesketch.lib.aggregators import manager as aggregator_manager
from timesketch.models.sketch import approach_created  # Import the signal

logger = logging.getLogger("timesketch.analyzers.dfiq")

@approach_created.connect
def trigger_dfiq_analyzsis(approach, **extra):
    analyzer_manager = DFIQAnalyzerManager(approach=approach)
    analyzer_manager.check_for_dfiq_analyzer()
# This approach triggrs the following SQLA messages:
# /usr/local/src/timesketch/timesketch/models/annotations.py:403: SAWarning: Object of type <InvestigativeQuestion> not in session, add operation along 'User.investigative_questions' will not proceed db_session.commit()
# /usr/local/src/timesketch/timesketch/models/annotations.py:403: SAWarning: Object of type <InvestigativeQuestion> not in session, add operation along 'Sketch.questions' will not proceed db_session.commit()
# To fix this, the InvestigativeQuestion needs to be added to the Database before we trigger the analyzers!

class DFIQAnalyzerManager:
    """Manager for executing DFIQ analyzers."""

    def __init__(self, approach):
        """Initializes the manager."""
        self.sketch = approach.sketch
        self.user_id = approach.user_id
        self.approach_spec = json.loads(approach.spec_json)

        self.aggregator_manager = aggregator_manager

    def check_for_dfiq_analyzer(self):
      """Checks if the created approach has analyzer steps to execute."""
      dfiq_analyzers = set()
      if self.approach_spec.get("steps"):
          for step in self.approach_spec.get("steps"):
              if step.get("stage") == "analysis" and step.get("type") == "timesketch-analyzer":
                  dfiq_analyzers.add(step.get("value"))

      if dfiq_analyzers:
          print(f"### Next gonna run {dfiq_analyzers}")
          analyzer_sessions = self._run_dfiq_analyzers(dfiq_analyzers)
          return analyzer_sessions

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
        from timesketch.lib.analyzers import manager as analyzer_manager
        analyzer_by_datatypes = {}
        for analyzer_name, analyzer_class in analyzer_manager.AnalysisManager.get_analyzers(
            include_dfiq=True
        ):
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

    def _get_data_types_per_timeline(self):
        """Retrieves data types present in each eligible timeline.

        Returns:
            dict: A dictionary mapping timeline IDs to lists of data types.
        """
        datatype_per_timeline = {}
        for timeline in self.sketch.timelines:
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

    def _run_dfiq_analyzers(self, dfiq_analyzers):
        """Executes DFIQ analyzers on matching timelines.

        Args:
            dfiq_analyzers (set): A set of DFIQ analyzer names.

        Returns:
            list: A list of analyzer sessions (potentially empty).
        """
        analyzer_by_datatypes = self._get_analyzers_by_data_type(dfiq_analyzers)
        if not analyzer_by_datatypes:
            logger.error(
                "None of the requested DFIQ analyzers have required data "
                "types defined. Aborting."
            )
            return []

        datatype_per_timeline = self._get_data_types_per_timeline()

        analyzer_by_timeline = {}
        for timeline_id, timeline_datatypes in datatype_per_timeline.items():
            analyzer_by_timeline[timeline_id] = []
            for data_type, analyzer_names in analyzer_by_datatypes.items():
                # Handle classical analyzers by always including them.
                if data_type == "ALL":
                    analyzer_by_timeline[timeline_id].extend(analyzer_names)
                elif data_type in timeline_datatypes:
                    analyzer_by_timeline[timeline_id].extend(analyzer_names)

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
                    user_id=self.user_id,
                    analyzer_names=analyzer_names,
                    analyzer_kwargs=None,
                    timeline_id=timeline_id,
                    analyzer_force_run=True,
                    include_dfiq=True,
                )
            except KeyError as e:
                logger.warning(
                    f"Unable to build analyzer pipeline, analyzer does not exist: {e}"
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
