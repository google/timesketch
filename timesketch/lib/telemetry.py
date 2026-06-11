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
import functools
import logging
import os

# --- OpenTelemetry Imports (Guarded) ---
try:
    from google.auth import compute_engine
    from google.auth import exceptions as auth_exceptions
    from google.auth import transport
    from google.cloud.trace_v2 import TraceServiceClient

    from opentelemetry import trace
    from opentelemetry.trace import StatusCode
    from opentelemetry.exporter import cloud_trace
    from opentelemetry.exporter.otlp.proto.grpc import trace_exporter as grpc_exporter
    from opentelemetry.exporter.otlp.proto.http import trace_exporter as http_exporter
    from opentelemetry.instrumentation.celery import CeleryInstrumentor
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    HAS_OTEL = True
except (ImportError, ModuleNotFoundError) as e:
    HAS_OTEL = False
    trace = None
    StatusCode = None
    logger = logging.getLogger("timesketch.telemetry")
    logger.info("OpenTelemetry is not installed. Error: %s", e)

from timesketch.version import get_version

logger = logging.getLogger("timesketch.telemetry")


def instrument_search(func):
    """Decorator to instrument OpenSearch search calls with OpenTelemetry.

    This decorator wraps OpenSearch search methods to automatically create
    telemetry spans ("opensearch.search") for each query. It extracts useful
    context from the query, such as the `sketch_id`, and records it as an
    attribute (`timesketch.sketch_id`) to help correlate backend performance
    with specific user sketches.

    Additionally, if the OpenSearch client returns a dictionary containing a
    "took" field, the decorator captures this value and adds it to the span
    under the attribute `db.opensearch.took_ms`.

    If the query fails and raises an exception, the exception is recorded
    on the span and the span's status is set to ERROR.

    If OpenTelemetry is not installed or enabled via `TIMESKETCH_OTEL_MODE`,
    this decorator acts as a no-op and safely runs the function without spans.
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not is_enabled():
            return func(*args, **kwargs)

        tracer = trace.get_tracer("timesketch.lib.datastores.opensearch")
        with tracer.start_as_current_span("opensearch.search") as span:
            sketch_id = kwargs.get("sketch_id")
            if sketch_id is None and len(args) > 1:
                sketch_id = args[1]
            if sketch_id is not None:
                span.set_attribute("timesketch.sketch_id", sketch_id)

            try:
                result = func(*args, **kwargs)
                if isinstance(result, dict) and "took" in result:
                    span.set_attribute("db.opensearch.took_ms", result.get("took", 0))
                return result
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise

    return wrapper


def safe_telemetry_call(func):
    """Decorator to ensure telemetry calls never crash the application.

    This makes telemetry 'best-effort'. If a telemetry operation fails
    (e.g. due to serialization errors), it logs a warning and allows
     the primary business logic to continue.
    """

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:  # pylint: disable=broad-except
            logger.warning("Telemetry operation %s failed: %s", func.__name__, e)
            return None

    return wrapper


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

    # Prevent overriding if already set (e.g. by Flask auto-reloader)
    if isinstance(trace.get_tracer_provider(), TracerProvider):
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
        # Explicitly pass credentials from the GKE Metadata Server
        # This ignores GOOGLE_APPLICATION_CREDENTIALS
        credentials = compute_engine.Credentials()
        trace_client = TraceServiceClient(credentials=credentials)
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


@safe_telemetry_call
def set_status_on_current_span(status_name: str, description: str = None):
    """Sets the status on the currently active span.

    Args:
        status_name (str): The name of the status code (e.g. 'OK', 'ERROR').
        description (str): Optional description of the status.
    """
    if not is_enabled():
        return

    otel_span = trace.get_current_span()
    if otel_span.is_recording():
        code = getattr(StatusCode, status_name.upper(), StatusCode.UNSET)
        otel_span.set_status(code, description)


@safe_telemetry_call
def add_event_to_current_span(event: str):
    """Adds a named event (annotation) to the currently active span.

    Args:
        event (str): The name or message of the event to record.
    """
    if not is_enabled() or not HAS_OTEL:
        return

    otel_span = trace.get_current_span()
    if otel_span.is_recording():
        otel_span.add_event(event)


@safe_telemetry_call
def add_attribute_to_current_span(name: str, value: object):
    """Adds a key-value attribute (tag) to the currently active span.

    Simple types (str, bool, int, float) are stored as-is. Complex objects
    are automatically serialized to JSON strings.
    Args:
        name (str): The key name for the attribute.
        value (object): The value to store. Needs to be JSON serializable.
    """
    if not is_enabled() or not HAS_OTEL:
        return

    otel_span = trace.get_current_span()
    if otel_span.is_recording():
        if isinstance(value, (str, bool, int, float)):
            otel_span.set_attribute(name, value)
        else:
            otel_span.set_attribute(name, json.dumps(value))
