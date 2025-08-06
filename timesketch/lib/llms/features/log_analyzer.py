# Copyright 2025 Google Inc. All rights reserved.
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
"""LogAnalyzer feature for automated log analysis using LLMs via an external service."""
import re
import logging
from typing import Any, Dict, Optional, Generator

from flask import current_app
from timesketch.models import db_session
from timesketch.models.sketch import (
    Sketch,
    InvestigativeQuestion,
    InvestigativeQuestionConclusion,
    Event,
)
from timesketch.lib.llms.features.interface import LLMFeatureInterface
from timesketch.lib.llms.providers.interface import LLMProvider
from timesketch.lib.datastores.opensearch import OpenSearchDataStore

logger = logging.getLogger("timesketch.llm.log_analyzer_feature")


class LogAnalysisError(Exception):
    """Custom exception for log analysis errors."""


class LogAnalyzer(LLMFeatureInterface):
    """
    LogAnalyzer feature for automated log analysis using LLMs via an
    external service. It prepares a stream of logs, processes a stream
    of findings, and creates/commits DFIQ objects in Timesketch.
    This feature always processes ALL events within the active timelines of a sketch.
    """

    NAME = "log_analyzer"
    SUPPORTS_STREAMING_INPUT = True
    SUPPORTS_STREAMING_OUTPUT = True
    RESPONSE_SCHEMA: Optional[Dict[str, Any]] = None

    def __init__(self):
        """Initialize the LogAnalyzer feature."""
        super().__init__()
        self._errors_encountered = []
        self._events_exported = 0
        self._findings_received = 0

    @property
    def datastore(self) -> OpenSearchDataStore:
        """Property to get an instance of the datastore backend.

        Returns:
            Instance of lib.datastores.opensearch.OpenSearchDatastore
        """
        return OpenSearchDataStore(
            host=current_app.config["OPENSEARCH_HOST"],
            port=current_app.config["OPENSEARCH_PORT"],
            pool_maxsize=60,
        )

    def execute(  # pylint: disable=unused-argument
        self, sketch: Sketch, form: Dict, llm_provider: LLMProvider, **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Executes the log analysis streaming workflow.

        This method encapsulates all the streaming logic for log analysis,
        including preparing the log stream, sending it to the LLM provider,
        and processing the results.

        Args:
            sketch: The Timesketch Sketch object.
            form: Form data from the request.
            llm_provider: The LLM provider instance.
            **kwargs: Additional keyword arguments (for future extensibility).

        Returns:
            Dict[str, Any]: Summary of the analysis results.
        """
        logger.info("LogAnalyzer: Starting streaming analysis for sketch %s", sketch.id)

        if not llm_provider.SUPPORTS_STREAMING:
            raise ValueError(
                f'LLM provider "{llm_provider.NAME}" does not support '
                "streaming operations"
            )

        try:
            # Prepare log stream
            log_events_generator = self.prepare_log_stream_for_analysis(
                sketch=sketch, form=form
            )

            # Stream logs to LLM provider and get findings back
            findings_generator = llm_provider.generate_stream_from_logs(
                log_events_generator=log_events_generator
            )

            # Process findings
            processed_findings_summary = []

            for finding_dict in findings_generator:
                if finding_dict.get("error"):
                    logger.error(
                        "LogAnalyzer: Error from provider stream: %s",
                        finding_dict["error"],
                    )
                    processed_findings_summary.append(
                        {
                            "status": "error_from_provider",
                            "message": finding_dict["error"],
                            "raw_line": finding_dict.get("raw_line"),
                        }
                    )
                    self._errors_encountered.append(finding_dict["error"])
                    if (
                        len(self._errors_encountered) > 100
                    ):  # Fail fast on too many errors
                        raise LogAnalysisError("Too many errors from provider stream")
                    continue

                self._findings_received += 1

                # Process individual finding
                processing_result = self.process_response(
                    llm_response=finding_dict, sketch=sketch
                )

                processed_findings_summary.append(processing_result)

                if processing_result.get("status") == "error":
                    self._errors_encountered.append("Processing error for finding")

            return {
                "status": "success",
                "feature": self.NAME,
                "total_findings_processed": self._findings_received,
                "errors_encountered": len(self._errors_encountered),
                "events_exported": self._events_exported,
                "findings_received": self._findings_received,
                "error_details": (
                    self._errors_encountered[:10] if self._errors_encountered else []
                ),
                "processed_findings_summary": processed_findings_summary,
            }

        except Exception as exception:
            logger.error(
                "LogAnalyzer: Failed to execute analysis for sketch %s: %s",
                sketch.id,
                exception,
                exc_info=True,
            )
            raise

    def prepare_log_stream_for_analysis(
        self, sketch: Sketch, form: Dict
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Returns a generator of log events from the sketch's active timelines.
        """
        active_timelines = list(sketch.active_timelines)
        if not active_timelines:
            logger.warning(
                "LogAnalyzer: No active timelines found for sketch %s",
                sketch.id,
            )
            raise LogAnalysisError(f"No active timelines found for sketch {sketch.id}")

        indices_for_pit = [
            timeline.searchindex.index_name for timeline in active_timelines
        ]
        timeline_ids = [str(timeline.id) for timeline in active_timelines]

        query_string = form.get("query", "*")
        if not query_string or query_string.strip() == "":
            query_string = "*"

        must_clauses = [
            {"query_string": {"query": query_string, "default_operator": "AND"}}
        ]
        must_clauses.append({"terms": {"__ts_timeline_id": timeline_ids}})
        base_query_body = {"query": {"bool": {"must": must_clauses}}}

        try:
            log_events_generator = self.datastore.export_events_with_slicing(
                indices_for_pit=indices_for_pit,
                base_query_body=base_query_body,
                num_slices=20,
            )

            for event in log_events_generator:
                self._events_exported += 1
                # Add index name to event for better tracking
                if "_index" in event:
                    event["__ts_index_name"] = event["_index"]
                yield event

        except Exception as exception:
            logger.error(
                "LogAnalyzer: Error during datastore.export_events_with_slicing "
                "for sketch %s: %s",
                sketch.id,
                exception,
                exc_info=True,
            )
            raise LogAnalysisError(
                f"Failed to export events: {str(exception)}"
            ) from exception

    def generate_prompt(self, sketch: Sketch, **kwargs: Any) -> str:
        """
        Abstract method from LLMFeatureInterface.

        The log_analyzer uses an agent instead of generating any prompts, so this
        method is not used here.
        """
        logger.debug("LogAnalyzer.generate_prompt called for sketch %s", sketch.id)
        return (
            "Log analysis initiated for events in sketch "
            f'"{sketch.name}" (ID: {sketch.id})'
        )

    def process_response(
        self, llm_response: Dict[str, Any], **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Processes a single finding dictionary from the LLM provider,
        creates associated Timesketch objects (Event,
        InvestigativeQuestion, InvestigativeQuestionConclusion), and commits
        them to the database.

        Args:
            llm_response (Dict[str, Any]): A single finding object from the LLM.
            **kwargs: Additional data needed for processing, which must include:
                - sketch (Sketch): The active Timesketch Sketch object.

        Returns:
            Dict[str, Any]: A dictionary summarizing the processing result for
                            this finding. Example: {"status": "success",
                            "message": "...", "linked_event_id": "..."}
        """
        sketch = kwargs.get("sketch")
        PRIORITY_MAP = {"low": 1, "medium": 2, "high": 3}

        if not isinstance(llm_response, dict):
            logger.error(
                "LogAnalyzer.process_response: Expected dict, got %s",
                type(llm_response),
            )
            return {
                "status": "error",
                "message": "Invalid finding format received from LLM provider.",
            }

        original_ts_event_id = llm_response.get("record_id")
        if not original_ts_event_id:
            logger.warning(
                "LogAnalyzer: Finding missing 'record_id': %s",
                str(llm_response)[:200],
            )
            return {
                "status": "error",
                "message": "Finding is missing its associated Timesketch event ID.",
            }

        events_to_commit = []

        event_to_link = Event.get_or_create(
            sketch_id=sketch.id, document_id=original_ts_event_id
        )

        # If newly created, find the event's searchindex
        if not event_to_link.searchindex_id:
            try:
                # Extract index name from the finding if available
                index_name = llm_response.get("__ts_index_name") or llm_response.get(
                    "_index"
                )
                if index_name:
                    searchindex_db_id = self._get_search_index_by_name(
                        sketch, index_name
                    )
                else:
                    searchindex_db_id = self._get_search_index(
                        sketch, original_ts_event_id
                    )
                event_to_link.searchindex_id = searchindex_db_id
                events_to_commit.append(event_to_link)
            except ValueError as exception:
                logger.error(
                    "LogAnalyzer: Could not find Event for ID %s: %s",
                    original_ts_event_id,
                    exception,
                )
                self._errors_encountered.append(
                    f"Failed to find searchindex for event {original_ts_event_id}"
                )
                return {
                    "status": "error",
                    "message": "Failed to associate finding with event "
                    f"{original_ts_event_id}: {exception}",
                }

        # Process annotations
        annotations = llm_response.get("annotations", [])
        if not annotations:
            logger.info(
                "LogAnalyzer: No annotations for event %s", original_ts_event_id
            )
            if events_to_commit:
                try:
                    db_session.add_all(events_to_commit)
                    db_session.commit()
                except Exception as exception:  # pylint: disable=broad-exception-caught
                    db_session.rollback()
                    logger.error(
                        "LogAnalyzer: DB error for event %s: %s",
                        original_ts_event_id,
                        exception,
                        exc_info=True,
                    )
                    return {
                        "status": "error",
                        "message": f"DB error saving event for {original_ts_event_id}.",
                    }
            return {
                "status": "success",
                "message": "Finding processed; no DFIQ objects from annotations.",
                "linked_event_id": original_ts_event_id,
            }

        questions_created_this_finding = 0
        conclusions_created_this_finding = 0

        for ann_data in annotations:
            question_text = ann_data.get("investigative_question")
            conclusion_texts = ann_data.get("conclusions", [])

            if not (
                question_text
                and isinstance(question_text, str)
                and conclusion_texts
                and isinstance(conclusion_texts, list)
            ):
                logger.warning(
                    "LogAnalyzer: Malformed annotation for event %s",
                    original_ts_event_id,
                )
                self._errors_encountered.append(
                    f"Malformed annotation for event {original_ts_event_id}: "
                    f"question={question_text}, "
                    f"conclusions={conclusion_texts}"
                )
                continue

            # TODO: Remove the regex again once the agent adjsuted their response.
            cleaned_question_text = re.sub(
                r"^\s*q\d+:\s*", "", question_text, flags=re.IGNORECASE
            ).strip()

            question = InvestigativeQuestion.get_or_create(
                sketch=sketch, name=cleaned_question_text
            )
            if not question.display_name:
                question.display_name = cleaned_question_text

            priority_value = ann_data.get("priority")
            if priority_value and isinstance(priority_value, str):
                priority_value = priority_value.lower()
                if priority_value not in PRIORITY_MAP:
                    self._errors_encountered.append(
                        f"Unknown priority value for event {original_ts_event_id}:"
                        f" question={question_text},"
                        f" priority={priority_value}"
                    )
                else:
                    current_priority_level = None
                    for label_str in question.get_labels:
                        if label_str.startswith("__ts_priority_"):
                            current_priority_level = label_str.split("_")[-1]
                            break
                    new_priority_score = PRIORITY_MAP.get(priority_value, 0)
                    current_priority_score = PRIORITY_MAP.get(current_priority_level, 0)
                    if new_priority_score > current_priority_score:
                        if current_priority_level:
                            old_priority_label = (
                                f"__ts_priority_{current_priority_level}"
                            )
                            question.remove_label(old_priority_label)
                        new_priority_label = f"__ts_priority_{priority_value}"
                        question.add_label(new_priority_label)

            questions_created_this_finding += 1
            question.add_attribute("source", "AI_GENERATED")
            question.add_attribute(
                "attack_stage_suggestion", ann_data.get("attack_stage", "n/a")
            )

            # Create individual conclusions for each conclusion text
            for conclusion_text in conclusion_texts:
                if not isinstance(conclusion_text, str) or not conclusion_text.strip():
                    continue

                # Check if this exact conclusion already exists for this question
                existing_conclusion = InvestigativeQuestionConclusion.query.filter_by(
                    investigativequestion=question,
                    conclusion=conclusion_text,
                    automated=True,
                ).first()

                if existing_conclusion:
                    if event_to_link not in existing_conclusion.events:
                        existing_conclusion.events.append(event_to_link)
                        db_session.add(existing_conclusion)
                else:
                    new_conclusion = InvestigativeQuestionConclusion(
                        conclusion=conclusion_text,
                        investigativequestion=question,
                        user=None,
                        automated=True,
                    )

                    if event_to_link not in new_conclusion.events:
                        new_conclusion.events.append(event_to_link)

                    db_session.add(new_conclusion)
                    conclusions_created_this_finding += 1
                    question.set_status("pending-review")

        try:
            db_session.commit()
            logger.info(
                "LogAnalyzer: Committed %d questions and %d conclusions for event %s",
                questions_created_this_finding,
                conclusions_created_this_finding,
                original_ts_event_id,
            )
        except Exception as exception:  # pylint: disable=broad-exception-caught
            db_session.rollback()
            logger.error(
                "LogAnalyzer: DB commit error for event %s: %s",
                original_ts_event_id,
                exception,
                exc_info=True,
            )
            self._errors_encountered.append(
                f"DB error for event {original_ts_event_id}: {str(exception)}"
            )
            return {
                "status": "error",
                "message": f"DB error saving analysis for event "
                f"{original_ts_event_id}.",
            }

        return {
            "status": "success",
            "message": (
                f"Successfully processed {questions_created_this_finding} question(s) "
                f"and {conclusions_created_this_finding} conclusion(s) for event "
                f"{original_ts_event_id}."
            ),
            "linked_event_id": original_ts_event_id,
        }

    def _get_search_index_by_name(self, sketch: Sketch, index_name: str) -> int:
        """Gets the database ID of a SearchIndex by its OpenSearch index name.

        Args:
            sketch: The Timesketch Sketch ORM object.
            index_name: The OpenSearch index name.

        Returns:
            int: The database primary key of the SearchIndex.

        Raises:
            ValueError: If the index is not found in the sketch's timelines.
        """
        for timeline in sketch.active_timelines:
            if timeline.searchindex.index_name == index_name:
                return timeline.searchindex.id

        raise ValueError(
            f'Index "{index_name}" not found in active timelines of '
            f"sketch {sketch.id}"
        )

    def _get_search_index(self, sketch: Sketch, document_id: str) -> int:
        """
        Gets the database primary key (ID) of the Timesketch SearchIndex
        ORM object to which the given OpenSearch document_id belongs,
        within the context of the provided sketch's active timelines.

        Args:
            sketch: The Timesketch Sketch ORM object.
            document_id: The OpenSearch document ID (_id) of the event.

        Returns:
            int: The database primary key (e.g., searchindex.id) of the
                 Timesketch SearchIndex ORM object.

        Raises:
            ValueError: If the event cannot be found in any of the sketch's
                        active timelines' associated OpenSearch indices.
        """
        for timeline in sketch.active_timelines:
            searchindex_orm_object = timeline.searchindex
            opensearch_index_name = searchindex_orm_object.index_name

            try:
                count_response = self.datastore.client.count(
                    index=opensearch_index_name,
                    body={"query": {"term": {"_id": document_id}}},
                )

                if count_response.get("count", 0) > 0:
                    return searchindex_orm_object.id

            except Exception as exception:  # pylint: disable=broad-exception-caught
                logger.warning(
                    'LogAnalyzer: Error checking event %s in index "%s": %s. '
                    "Will try other indices.",
                    document_id,
                    opensearch_index_name,
                    exception,
                    exc_info=False,
                )
                continue

        logger.error(
            "LogAnalyzer: Event %s was not found in any OpenSearch indices "
            "associated with active timelines for sketch %s.",
            document_id,
            sketch.id,
        )
        raise ValueError(
            f"Event (doc_id: {document_id}) could not be located in any of the "
            "OpenSearch indices linked to the active timelines of "
            f"sketch {sketch.id}."
        )
