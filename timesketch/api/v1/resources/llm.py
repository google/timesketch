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
"""Timesketch API endpoint for interacting with LLM features."""
import logging
import multiprocessing
import multiprocessing.managers
import time
from typing import Any

import prometheus_client
from flask import request, abort, jsonify, Response
from flask_login import login_required, current_user
from flask_restful import Resource

from timesketch.api.v1 import resources
from timesketch.lib import definitions, utils
from timesketch.lib.definitions import METRICS_NAMESPACE
from timesketch.lib.llms.providers import manager as llm_provider_manager
from timesketch.lib.llms.features import manager as feature_manager
from timesketch.models.sketch import Sketch

logger = logging.getLogger("timesketch.api.llm")


class LLMResource(resources.ResourceMixin, Resource):
    """Resource to interact with Large Language Models (LLMs).

    This resource handles requests for various LLM-powered features.
    It validates requests, selects appropriate features/providers,
    and delegates the actual processing to the feature implementations.
    """

    METRICS = {
        "llm_requests_total": prometheus_client.Counter(
            "llm_requests_total",
            "Total number of LLM requests received",
            ["sketch_id", "feature"],
            namespace=METRICS_NAMESPACE,
        ),
        "llm_errors_total": prometheus_client.Counter(
            "llm_errors_total",
            "Total number of errors during LLM processing",
            ["sketch_id", "feature", "error_type"],
            namespace=METRICS_NAMESPACE,
        ),
        "llm_duration_seconds": prometheus_client.Summary(
            "llm_duration_seconds",
            "Time taken to process an LLM request (in seconds)",
            ["sketch_id", "feature"],
            namespace=METRICS_NAMESPACE,
        ),
    }
    # TODO(itsmvd): Make this configurable
    _LLM_TIMEOUT_WAIT_SECONDS = 30

    @login_required
    def post(self, sketch_id: int) -> Response:
        """Handles POST requests to execute LLM features.

        This method focuses on request validation, feature/provider selection,
        and initiating the process. The actual processing logic is delegated
        to the feature implementation.

        Args:
            sketch_id: The ID of the sketch to operate on.

        Returns:
            A Flask Response object, typically JSON, summarizing the outcome.

        Raises:
            HTTPException: If validation fails or an error occurs.
        """
        start_time = time.time()
        sketch = self._validate_sketch(sketch_id)
        form = self._validate_request_data()
        feature_instance = self._get_feature(form.get("feature"))
        self._increment_request_metric(sketch_id, feature_instance.NAME)
        timeline_ids = self._validate_indices(sketch, form.get("filter", {}))

        try:
            llm_provider = llm_provider_manager.LLMManager.create_provider(
                feature_name=feature_instance.NAME
            )
        except Exception as e:  # pylint: disable=broad-except
            logger.error(
                "Failed to get LLM provider for feature '%s' on sketch %s: %s",
                feature_instance.NAME,
                sketch_id,
                e,
                exc_info=True,
            )
            self.METRICS["llm_errors_total"].labels(
                sketch_id=str(sketch_id),
                feature=feature_instance.NAME,
                error_type="provider_creation_error",
            ).inc()
            abort(
                definitions.HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                f"Error initializing LLM provider: {str(e)}",
            )

        try:
            # Check if feature handles its own execution (new workflow)
            if hasattr(feature_instance, "execute") and callable(
                getattr(feature_instance, "execute")
            ):
                logger.info(
                    "Delegating execution to feature '%s' for sketch %s",
                    feature_instance.NAME,
                    sketch_id,
                )
                result = feature_instance.execute(
                    sketch=sketch,
                    form=form,
                    timeline_ids=timeline_ids,
                    llm_provider=llm_provider,
                    timeout=self._LLM_TIMEOUT_WAIT_SECONDS,
                )
            else:
                # Fallback to legacy non-streaming workflow for backward compatibility
                logger.info(
                    "Using legacy workflow for feature '%s' on sketch %s",
                    feature_instance.NAME,
                    sketch_id,
                )
                result = self._execute_legacy_workflow(
                    feature_instance, sketch, form, timeline_ids, llm_provider
                )

            self._record_duration(sketch_id, feature_instance.NAME, start_time)
            return jsonify(result)

        except ValueError as e:
            logger.error(
                "ValueError during execution of '%s' on sketch %s: %s",
                feature_instance.NAME,
                sketch_id,
                e,
            )
            self.METRICS["llm_errors_total"].labels(
                sketch_id=str(sketch_id),
                feature=feature_instance.NAME,
                error_type="value_error",
            ).inc()
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                f"Unable to execute LLM feature ({feature_instance.NAME}): {str(e)}.",
            )
        except Exception as e:  # pylint: disable=broad-except
            logger.error(
                "Unhandled exception during execution of '%s' on sketch %s: %s",
                feature_instance.NAME,
                sketch_id,
                e,
                exc_info=True,
            )
            self.METRICS["llm_errors_total"].labels(
                sketch_id=str(sketch_id),
                feature=feature_instance.NAME,
                error_type="unhandled_exception",
            ).inc()
            abort(
                definitions.HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                f"An unexpected error occurred: {str(e)}",
            )

    def _execute_legacy_workflow(
        self,
        feature: feature_manager.LLMFeatureInterface,
        sketch: Sketch,
        form: dict,
        timeline_ids: list,
        llm_provider: llm_provider_manager.LLMProvider,
    ) -> dict:
        """Executes the legacy non-streaming workflow for backward compatibility.

        Args:
            feature: The LLM feature instance.
            sketch: The Sketch object.
            form: The request form data.
            timeline_ids: List of timeline DB IDs.
            llm_provider: The instantiated LLM provider.

        Returns:
            The processed result dictionary.
        """
        # Generate prompt
        prompt = self._generate_prompt(feature, sketch, form, timeline_ids)
        # Execute LLM call
        llm_api_response = self._execute_llm_call(
            feature, prompt, sketch.id, llm_provider
        )
        # Process response
        return feature.process_response(
            llm_response=llm_api_response,
            sketch=sketch,
            sketch_id=sketch.id,
            form=form,
            timeline_ids=timeline_ids,
            datastore=self.datastore,
        )

    def _validate_sketch(self, sketch_id: int) -> Sketch:
        """Validates sketch existence and user permissions.

        Args:
            sketch_id: The ID of the sketch to validate.

        Returns:
            The Sketch object if validation is successful.

        Raises:
            HTTPException: With a 404 status if the sketch is not found, or a
                403 status if the user lacks write permissions.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            logger.warning("Sketch not found with ID %s", sketch_id)
            abort(
                definitions.HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID."
            )
        if not sketch.has_permission(current_user, "write"):
            logger.warning(
                "User %s lacks write permission for sketch %s",
                current_user.username,
                sketch_id,
            )
            abort(
                definitions.HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have sufficient access to modify the sketch.",
            )
        return sketch

    def _validate_request_data(self) -> dict:
        """Validates that the request contains JSON data.

        Returns:
            The JSON data from the request as a dictionary.

        Raises:
            HTTPException: With a 400 status if the request body does not
                contain valid JSON.
        """
        form = request.json
        if not form:
            logger.error("POST request is missing JSON data in the body")
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                "The POST request requires JSON data in the body.",
            )
        return form

    def _get_feature(self, feature_name: str) -> feature_manager.LLMFeatureInterface:
        """Retrieves and validates the requested LLM feature.

        Args:
            feature_name: The name of the LLM feature to retrieve.

        Returns:
            An instance of the requested LLM feature.

        Raises:
            HTTP 400: If feature_name is not provided or is invalid.
        """
        if not feature_name:
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                "The 'feature' parameter is required.",
            )
        try:
            feature_instance = feature_manager.FeatureManager.get_feature_instance(
                feature_name.lower()
            )
        except KeyError:
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                f"Invalid LLM feature: {feature_name}",
            )
        return feature_instance

    def _validate_indices(self, sketch: Sketch, query_filter: dict) -> list:
        """Extracts and validates timeline IDs from the query filter for a sketch.

        Args:
            sketch: The Sketch object to validate indices for.
            query_filter: A dictionary containing filter parameters.

        Returns:
            A list of validated timeline IDs.

        Raises:
            HTTP 400: If no valid search indices are found.
        """
        all_indices = list({t.searchindex.index_name for t in sketch.timelines})
        indices = query_filter.get("indices", all_indices)
        if "_all" in indices:
            indices = all_indices
        indices, timeline_ids = utils.get_validated_indices(indices, sketch)
        if not indices:
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                "No valid search indices were found.",
            )
        return timeline_ids

    def _generate_prompt(
        self,
        feature: feature_manager.LLMFeatureInterface,
        sketch: Sketch,
        form: dict,
        timeline_ids: list,
    ) -> str:
        """Generates a prompt string for the LLM based on the feature's logic.

        This method delegates the prompt generation to the specific LLM feature
        implementation. It passes necessary context such as the sketch, form data,
        and relevant timeline IDs.

        Args:
            feature: An instance of LLMFeatureInterface that defines the prompt
                generation logic.
            sketch: The Timesketch sketch object.
            form: A dictionary containing the request form data.
            timeline_ids: A list of database IDs for the timelines relevant to
                the request.

        Returns:
            str: The generated prompt string.

        Raises:
            HTTPException: If a ValueError occurs during prompt generation,
                indicating invalid input or an issue with the feature's logic.
        """
        prompt_str = ""
        try:
            prompt_str = feature.generate_prompt(
                sketch, form=form, datastore=self.datastore, timeline_ids=timeline_ids
            )
        except ValueError as e:
            logger.error(
                "Error generating prompt for feature '%s' on sketch %s: %s",
                feature.NAME,
                sketch.id,
                e,
            )
            abort(definitions.HTTP_STATUS_CODE_BAD_REQUEST, str(e))
        return prompt_str

    def _execute_llm_call(
        self,
        feature: feature_manager.LLMFeatureInterface,
        prompt: str,
        sketch_id: int,
        llm_provider: llm_provider_manager.LLMProvider,
    ) -> Any:
        """Executes a non-streaming LLM call in a separate process with a timeout.

        This method runs the LLM generation in a separate process to enforce a
        timeout. It uses a multiprocessing manager to share the response back
        from the child process. If the call exceeds the configured timeout, the
        process is terminated. It also handles and logs errors that occur within
        the LLM provider call.

        Args:
            feature: The LLM feature instance, used for logging and metrics.
            prompt: The prompt string to send to the LLM provider.
            sketch_id: The ID of the sketch, used for logging and metrics.
            llm_provider: The instantiated LLM provider to use for the call.

        Returns:
            Any: The response from the LLM provider. The exact type depends on
                the provider and feature.

        Raises:
            HTTPException: If the LLM call times out (504 Gateway Timeout) or
                if there is an error during the LLM API call (500 Internal
                Server Error).
        """
        logger.info(
            "Executing LLM call for feature '%s' on sketch %s via provider '%s'",
            feature.NAME,
            sketch_id,
            llm_provider.NAME,
        )
        with multiprocessing.Manager() as manager_mp:
            shared_response = manager_mp.dict()
            process = multiprocessing.Process(
                target=self._get_content_with_timeout,
                args=(feature, prompt, shared_response, llm_provider),
            )
            process.start()
            process.join(timeout=self._LLM_TIMEOUT_WAIT_SECONDS)

            if process.is_alive():
                logger.warning(
                    "LLM call for feature '%s' on sketch %s "
                    "timed out after %s seconds",
                    feature.NAME,
                    sketch_id,
                    self._LLM_TIMEOUT_WAIT_SECONDS,
                )
                process.terminate()
                process.join()
                self.METRICS["llm_errors_total"].labels(
                    sketch_id=str(sketch_id),
                    feature=feature.NAME,
                    error_type="llm_call_timeout",
                ).inc()
                abort(
                    definitions.HTTP_STATUS_CODE_GATEWAY_TIMEOUT,
                    "LLM call timed out. The operation took too long to complete.",
                )

            if "error" in shared_response:
                error_msg = shared_response["error"]
                logger.error(
                    "Error during LLM processing for feature '%s' on sketch %s: %s",
                    feature.NAME,
                    sketch_id,
                    error_msg,
                )
                self.METRICS["llm_errors_total"].labels(
                    sketch_id=str(sketch_id),
                    feature=feature.NAME,
                    error_type="llm_api_error",
                ).inc()
                abort(
                    definitions.HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                    f"Error during LLM processing: {error_msg}",
                )

            return shared_response.get("response")

    def _increment_request_metric(self, sketch_id: int, feature_name: str) -> None:
        """Increments the Prometheus counter for total LLM requests.

        This method is called at the beginning of a request to track the usage
        of different LLM features per sketch.

        Args:
            sketch_id: The ID of the sketch for which the request is made.
            feature_name: The name of the LLM feature being requested.
        """
        self.METRICS["llm_requests_total"].labels(
            sketch_id=str(sketch_id), feature=feature_name
        ).inc()

    def _record_duration(
        self, sketch_id: int, feature_name: str, start_time: float
    ) -> None:
        """Records the duration of the LLM request processing in a Prometheus summary.

        This method calculates the time elapsed since the start_time and records
        it in the `llm_duration_seconds` metric.

        Args:
            sketch_id: The ID of the sketch for which the request was made.
            feature_name: The name of the LLM feature that was executed.
            start_time: The timestamp (from time.time()) when the request
                processing started.
        """
        duration = time.time() - start_time
        self.METRICS["llm_duration_seconds"].labels(
            sketch_id=str(sketch_id), feature=feature_name
        ).observe(duration)

    def _get_content_with_timeout(
        self,
        feature: feature_manager.LLMFeatureInterface,
        prompt: str,
        shared_response: multiprocessing.managers.DictProxy,
        llm_provider: llm_provider_manager.LLMProvider,
    ) -> None:
        """Runs the LLM generation in a separate process and stores the result.

        This function is designed to be the target of a `multiprocessing.Process`
        to allow for a timeout on the LLM call. It calls the provider's
        `generate` method and places the result or an error message into the
        shared dictionary.

        Args:
            feature: The LLM feature instance, used for logging.
            prompt: The prompt string to send to the LLM.
            shared_response: A multiprocessing manager dictionary to store the
                response or error.
            llm_provider: The instantiated LLM provider to use for the call.
        """
        try:
            api_response = llm_provider.generate(
                prompt, response_schema=feature.RESPONSE_SCHEMA
            )
            shared_response.update({"response": api_response})
        except Exception as e:  # pylint: disable=broad-except
            process_logger = logging.getLogger("timesketch.api.llm.subprocess")
            process_logger.error(
                "Error in LLM call for feature '%s': %s", feature.NAME, e, exc_info=True
            )
            shared_response.update({"error": str(e)})
