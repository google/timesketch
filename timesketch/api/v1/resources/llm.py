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
import prometheus_client
from flask import request, abort, jsonify, Response
from flask_login import login_required, current_user
from flask_restful import Resource
from timesketch.api.v1 import resources
from timesketch.lib import definitions, utils
from timesketch.lib.definitions import METRICS_NAMESPACE
from timesketch.lib.llms.providers import manager as llm_manager
from timesketch.lib.llms.features import manager as feature_manager
from timesketch.models.sketch import Sketch

logger = logging.getLogger("timesketch.api.llm")


class LLMResource(resources.ResourceMixin, Resource):
    """Resource to interact with LLMs.

    This class provides an API endpoint for accessing and utilizing Large Language
    Model features within Timesketch. It handles request validation, processing,
    and response handling, while also monitoring performance metrics.
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
        """Handles POST requests to the resource.

        Processes LLM requests, validates inputs, generates prompts,
        executes LLM calls, and returns the processed results.

        Args:
            sketch_id: The ID of the sketch to process.

        Returns:
            A Flask JSON response containing the processed LLM result.

        Raises:
            HTTP exceptions for various error conditions.
        """
        start_time = time.time()
        sketch = self._validate_sketch(sketch_id)
        form = self._validate_request_data()
        feature = self._get_feature(form.get("feature"))
        self._increment_request_metric(sketch_id, feature.NAME)
        timeline_ids = self._validate_indices(sketch, form.get("filter", {}))
        prompt = self._generate_prompt(feature, sketch, form, timeline_ids)
        response = self._execute_llm_call(feature, prompt, sketch_id)
        result = self._process_llm_response(
            feature, response, sketch, form, timeline_ids
        )
        self._record_duration(sketch_id, feature.NAME, start_time)
        return jsonify(result)

    def _validate_sketch(self, sketch_id: int) -> Sketch:
        """Validates sketch existence and user permissions.

        Args:
            sketch_id: The ID of the sketch to validate.

        Returns:
            The validated Sketch object.

        Raises:
            HTTP 404: If the sketch doesn't exist.
            HTTP 403: If the user doesn't have read access to the sketch.
        """
        sketch = Sketch.get_with_acl(sketch_id)
        if not sketch:
            abort(
                definitions.HTTP_STATUS_CODE_NOT_FOUND, "No sketch found with this ID."
            )
        if not sketch.has_permission(current_user, "read"):
            abort(
                definitions.HTTP_STATUS_CODE_FORBIDDEN,
                "User does not have read access to the sketch.",
            )
        return sketch

    def _validate_request_data(self) -> dict:
        """Validates the presence of request JSON data.

        Returns:
            The validated request data as a dictionary.

        Raises:
            HTTP 400: If no JSON data is provided in the request.
        """
        form = request.json
        if not form:
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                "The POST request requires data",
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
            return feature_manager.FeatureManager.get_feature_instance(feature_name)
        except KeyError:
            abort(
                definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                f"Invalid LLM feature: {feature_name}",
            )

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
        """Generates the LLM prompt based on the feature and request data.

        Args:
            feature: The LLM feature instance to use.
            sketch: The Sketch object.
            form: The request form data.
            timeline_ids: A list of validated timeline IDs.

        Returns:
            The generated prompt string for the LLM.

        Raises:
            HTTP 400: If prompt generation fails.
        """
        try:
            return feature.generate_prompt(
                sketch, form=form, datastore=self.datastore, timeline_ids=timeline_ids
            )
        except ValueError as e:
            abort(definitions.HTTP_STATUS_CODE_BAD_REQUEST, str(e))

    def _execute_llm_call(
        self, feature: feature_manager.LLMFeatureInterface, prompt: str, sketch_id: int
    ) -> dict:
        """Executes the LLM call with a timeout using multiprocessing.

        Args:
            feature: The LLM feature instance to use.
            prompt: The generated prompt to send to the LLM.
            sketch_id: The ID of the sketch being processed.

        Returns:
            The LLM response as a dictionary.

        Raises:
            HTTP 400: If the LLM call times out.
            HTTP 500: If an error occurs during LLM processing.
        """
        with multiprocessing.Manager() as manager:
            shared_response = manager.dict()
            process = multiprocessing.Process(
                target=self._get_content_with_timeout,
                args=(feature, prompt, shared_response),
            )
            process.start()
            process.join(timeout=self._LLM_TIMEOUT_WAIT_SECONDS)
            if process.is_alive():
                logger.warning(
                    "LLM call timed out after %d seconds.",
                    self._LLM_TIMEOUT_WAIT_SECONDS,
                )
                process.terminate()
                process.join()
                self.METRICS["llm_errors_total"].labels(
                    sketch_id=str(sketch_id), feature=feature.NAME, error_type="timeout"
                ).inc()
                abort(
                    definitions.HTTP_STATUS_CODE_BAD_REQUEST,
                    "LLM call timed out, please try again. "
                    "If this issue persists, contact your administrator.",
                )
            response = dict(shared_response)
            if "error" in response:
                self.METRICS["llm_errors_total"].labels(
                    sketch_id=str(sketch_id),
                    feature=feature.NAME,
                    error_type="llm_api_error",
                ).inc()
                abort(
                    definitions.HTTP_STATUS_CODE_INTERNAL_SERVER_ERROR,
                    f"Error during LLM processing: {response['error']}",
                )
            return response["response"]

    def _process_llm_response(
        self,
        feature: feature_manager.LLMFeatureInterface,
        response: dict,
        sketch: Sketch,
        form: dict,
        timeline_ids: list,
    ) -> dict:
        """Processes the LLM response into the final result.

        Args:
            feature: The LLM feature instance used.
            response: The raw LLM response.
            sketch: The Sketch object.
            form: The request form data.
            timeline_ids: A list of validated timeline IDs.

        Returns:
            The processed LLM response as a dictionary.

        Raises:
            HTTP 400: If response processing fails.
        """
        try:
            return feature.process_response(
                llm_response=response,
                form=form,
                sketch_id=sketch.id,
                datastore=self.datastore,
                sketch=sketch,
                timeline_ids=timeline_ids,
            )
        except ValueError as e:
            self.METRICS["llm_errors_total"].labels(
                sketch_id=str(sketch.id),
                feature=feature.NAME,
                error_type="response_processing",
            ).inc()
            abort(definitions.HTTP_STATUS_CODE_BAD_REQUEST, str(e))

    def _increment_request_metric(self, sketch_id: int, feature_name: str) -> None:
        """Increments the request counter metric.

        Args:
            sketch_id: The ID of the sketch being processed.
            feature_name: The name of the LLM feature being used.
        """
        self.METRICS["llm_requests_total"].labels(
            sketch_id=str(sketch_id), feature=feature_name
        ).inc()

    def _record_duration(
        self, sketch_id: int, feature_name: str, start_time: float
    ) -> None:
        """Records the duration of the request.

        Args:
            sketch_id: The ID of the sketch being processed.
            feature_name: The name of the LLM feature being used.
            start_time: The timestamp when the request started.
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
    ) -> None:
        """Send a prompt to the LLM and get a response within a process.

        This method is executed in a separate process to allow for timeout control.

        Args:
            feature: The LLM feature instance to use.
            prompt: The generated prompt to send to the LLM.
            shared_response: A managed dictionary to store the response or error.
        """
        try:
            llm = llm_manager.LLMManager.create_provider(feature_name=feature.NAME)
            response_schema = (
                feature.RESPONSE_SCHEMA if hasattr(feature, "RESPONSE_SCHEMA") else None
            )
            response = llm.generate(prompt, response_schema=response_schema)
            shared_response.update({"response": response})
        except Exception as e:  # pylint: disable=broad-except
            logger.error("Error in LLM call within process: %s", e, exc_info=True)
            shared_response.update({"error": str(e)})
