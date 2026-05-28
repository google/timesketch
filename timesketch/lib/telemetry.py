# Copyright 2026 Google Inc. All rights reserved.
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
"""Module providing OpenTelemetry capability to Timesketch."""

import json
import logging
import os
from typing import Optional, List

from timesketch.version import get_version

# Initialize optional Google/GCP variables to None to resolve E0606 warning
compute_engine = None
auth_exceptions = None
transport = None
TraceServiceClient = None

try:
    from opentelemetry import trace
    from opentelemetry.trace.span import INVALID_SPAN
    from opentelemetry.exporter.otlp.proto.grpc import trace_exporter as grpc_exporter
    from opentelemetry.exporter.otlp.proto.http import trace_exporter as http_exporter
    from opentelemetry.instrumentation.celery import CeleryInstrumentor
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    HAS_OTEL = True
except ImportError:
    HAS_OTEL = False

HAS_GCP_TRACE = False
if HAS_OTEL:
    try:
        from google.auth import compute_engine
        from google.auth import exceptions as auth_exceptions
        from google.auth import transport
        from google.cloud.trace_v2 import TraceServiceClient

        HAS_GCP_TRACE = True
    except ImportError:
        HAS_GCP_TRACE = False


logger = logging.getLogger("timesketch.telemetry")


def _get_gcp_project_id():
    """Returns the GCP Project ID as a string."""
    auth_request = transport.requests.Request()
    try:
        # pylint: disable=protected-access
        project_id = compute_engine._metadata.get_project_id(auth_request)
        return project_id
    except auth_exceptions.TransportError as e:
        logger.error("Could not get project_id from GCE metadata server: %s", str(e))
    return None


def is_enabled() -> bool:
    """Returns whether OpenTelemetry instrumentation is enabled.

    Returns:
        bool: True if telemetry is enabled, False otherwise.
    """
    if not HAS_OTEL:
        return False
    otel_mode = os.environ.get("TIMESKETCH_OTEL_MODE", "").lower()
    return otel_mode.startswith("otlp-")


def setup_telemetry(service_name: str):
    """Configures the OpenTelemetry trace exporter.

    Supported modes:
        - 'otlp-default-gce': Exports to Google Cloud Trace API from a GCE instance.
        - 'otlp-grpc': Exports to an OTLP collector via gRPC.
          Uses `TIMESKETCH_OTLP_GRPC_ENDPOINT` (default: localhost:4317).
        - 'otlp-http': Exports to an OTLP collector via HTTP.
          Uses `TIMESKETCH_OTLP_HTTP_ENDPOINT`
          (default: http://localhost:4318/v1/traces).

    Args:
        service_name (str): The name of the service to identify traces in the backend.
    """
    if not is_enabled():
        return

    resource = Resource(
        attributes={
            "service.name": service_name,
            "service.version": get_version(),
            "deployment.environment": os.environ.get("TIMESKETCH_ENV", "development"),
        }
    )

    otel_mode = os.environ.get("TIMESKETCH_OTEL_MODE", "").lower()
    trace_exporter = None

    if otel_mode == "otlp-grpc":
        endpoint = os.environ.get("TIMESKETCH_OTLP_GRPC_ENDPOINT", "localhost:4317")
        insecure = os.environ.get("TIMESKETCH_OTLP_INSECURE", "true").lower() == "true"
        trace_exporter = grpc_exporter.OTLPSpanExporter(
            endpoint=endpoint, insecure=insecure
        )
    elif otel_mode == "otlp-http":
        endpoint = os.environ.get(
            "TIMESKETCH_OTLP_HTTP_ENDPOINT", "http://localhost:4318/v1/traces"
        )
        trace_exporter = http_exporter.OTLPSpanExporter(endpoint=endpoint)
    elif otel_mode == "otlp-default-gce":
        if not HAS_GCP_TRACE:
            logger.error(
                "GCP trace libraries are not installed. Cannot use 'otlp-default-gce'."
            )
            return
        # Explicitly pass credentials from the GKE Metadata Server
        # This ignores GOOGLE_APPLICATION_CREDENTIALS
        credentials = compute_engine.Credentials()
        trace_client = TraceServiceClient(credentials=credentials)
        # pylint: disable=import-outside-toplevel,no-name-in-module
        from opentelemetry.exporter import cloud_trace

        trace_exporter = cloud_trace.CloudTraceSpanExporter(
            project_id=_get_gcp_project_id(),
            resource_regex=r"service.*",
            client=trace_client,
        )
    else:
        logger.error(
            "Unsupported OTEL tracing mode %s. "
            "Valid values for TIMESKETCH_OTEL_MODE are: "
            "'otlp-grpc', 'otlp-http', 'otlp-default-gce'",
            otel_mode,
        )
        return

    # --- Tracing Setup ---
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(trace_provider)


def instrument_celery_app(celery_app, **kwargs):
    """Instruments a Celery application instance.

    Args:
        celery_app (celery.app.Celery): The Celery application to instrument.
        **kwargs: Additional arguments passed to CeleryInstrumentor().instrument().
    """
    if not is_enabled():
        return
    CeleryInstrumentor().instrument(celery_app=celery_app, **kwargs)


def instrument_flask_app(app, **kwargs):
    """Instruments a Flask application instance.

    Args:
        app (flask.Flask): The Flask application to instrument.
        **kwargs: Additional arguments passed to FlaskInstrumentor().instrument_app().
    """
    if not is_enabled():
        return
    FlaskInstrumentor().instrument_app(app, **kwargs)


def add_event_to_current_span(event: str):
    """Adds a named event (annotation) to the currently active span.

    Args:
        event (str): The name or message of the event to record.
    """
    if not is_enabled():
        return

    otel_span = trace.get_current_span()
    if otel_span != INVALID_SPAN:
        otel_span.add_event(event)


def add_attribute_to_current_span(name: str, value: object):
    """Adds a key-value attribute (tag) to the active OpenTelemetry span.

    If OpenTelemetry is disabled or there is no active recording span, this
    function returns early. Primitive types (str, bool, int, float) are stored
    as-is. Complex objects are automatically serialized to JSON strings before
    being added to the span to guarantee valid storage compatibility.

    Args:
        name: The key name for the span attribute (e.g. 'search.sketch_id').
        value: The value to record. Complex objects must be JSON serializable.
    """
    if not is_enabled():
        return

    otel_span = trace.get_current_span()
    if otel_span != INVALID_SPAN:
        if isinstance(value, (str, bool, int, float)):
            otel_span.set_attribute(name, value)
        else:
            otel_span.set_attribute(name, json.dumps(value))


def add_wildcard_query_metrics(
    query_string: Optional[str], fields_targeted: Optional[List[str]]
):
    """Extracts and records detailed structural query pattern metrics.

    Only records metrics under active debug log levels.
    """
    if not logger.isEnabledFor(logging.DEBUG) or not query_string:
        return

    query_char_length = len(query_string)
    fields_targeted_count = len(fields_targeted) if fields_targeted else 0
    wildcard_symbols_count = query_string.count("*") + query_string.count("?")

    has_leading_wildcard = query_string.startswith("*") or query_string.startswith("?")
    has_trailing_wildcard = query_string.endswith("*") or query_string.endswith("?")

    stripped = query_string.strip("*?")
    has_midpoint_wildcard = "*" in stripped or "?" in stripped

    boolean_operators_count = (
        query_string.upper().count(" AND ")
        + query_string.upper().count(" OR ")
        + query_string.upper().count(" NOT ")
    )
    nested_clauses_count = query_string.count("(")

    add_attribute_to_current_span(
        "wildcard_search.query_char_length", query_char_length
    )
    add_attribute_to_current_span(
        "wildcard_search.fields_targeted_count", fields_targeted_count
    )
    add_attribute_to_current_span(
        "wildcard_search.has_leading_wildcard", has_leading_wildcard
    )
    add_attribute_to_current_span(
        "wildcard_search.has_trailing_wildcard", has_trailing_wildcard
    )
    add_attribute_to_current_span(
        "wildcard_search.has_midpoint_wildcard", has_midpoint_wildcard
    )
    add_attribute_to_current_span(
        "wildcard_search.wildcard_symbols_count", wildcard_symbols_count
    )
    add_attribute_to_current_span(
        "wildcard_search.boolean_operators_count", boolean_operators_count
    )
    add_attribute_to_current_span(
        "wildcard_search.nested_clauses_count", nested_clauses_count
    )
