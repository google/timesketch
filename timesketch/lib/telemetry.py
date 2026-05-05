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
import re

try:
    from google.auth import compute_engine
    from google.auth import exceptions as auth_exceptions
    from google.auth import transport
    from google.cloud.trace_v2 import TraceServiceClient

    from opentelemetry import trace
    from opentelemetry.trace.span import INVALID_SPAN
    from opentelemetry.exporter import cloud_trace
    from opentelemetry.exporter.otlp.proto.grpc import trace_exporter as grpc_exporter
    from opentelemetry.exporter.otlp.proto.http import trace_exporter as http_exporter
    from opentelemetry.instrumentation.celery import CeleryInstrumentor
    from opentelemetry.instrumentation.flask import FlaskInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider, SpanProcessor, StatusCode
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    HAS_OTEL = True

    # --- Optional Instrumentors ---
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        HAS_SQLALCHEMY_OTEL = True
    except ImportError:
        HAS_SQLALCHEMY_OTEL = False

    # --- Identity & Context ---
    try:
        from flask_login import current_user

        HAS_FLASK_LOGIN = True
    except ImportError:
        HAS_FLASK_LOGIN = False

    # --- Privacy & Security ---

    # Keywords that indicate an attribute name or value might be sensitive.
    SENSITIVE_KEYWORDS = [
        "password",
        "token",
        "secret",
        "key",
        "session",
        "cookie",
        "auth",
        "credential",
    ]

    # Attributes that are explicitly exempt from PII redaction (e.g. analyst identity)
    EXEMPT_PII_ATTRIBUTES = {"user.name", "user.id", "timesketch.user_id"}

    class SensitiveDataScrubber(SpanProcessor):
        """SpanProcessor that redacts sensitive attributes from spans."""

        def on_start(self, span, parent_context=None):
            """No-op on span start."""

        def on_end(self, span):
            """Redact attributes when a span ends."""
            if not span.attributes:
                return

            redacted_keys = []
            # Create a copy of keys to avoid modification during iteration
            for key in list(span.attributes.keys()):
                # Protect our own audit info
                if key == "otel.redacted_keys":
                    continue

                value = span.attributes[key]
                if not isinstance(value, str):
                    continue

                lower_key = key.lower()
                is_credential_key = any(
                    keyword in lower_key for keyword in SENSITIVE_KEYWORDS
                )

                # 1. If it's a credential key, redact the whole thing
                if is_credential_key:
                    redacted_keys.append(key)
                    # pylint: disable=protected-access
                    span._attributes[key] = "[REDACTED]"
                    continue

                # 2. Check for sensitive keywords in the value
                lower_val = value.lower()
                if any(keyword in lower_val for keyword in SENSITIVE_KEYWORDS):
                    redacted_keys.append(f"{key} (value)")
                    # pylint: disable=protected-access
                    span._attributes[key] = "[REDACTED]"
                    continue

            if redacted_keys:
                # pylint: disable=protected-access
                span._attributes["otel.redacted_keys"] = redacted_keys

    def flask_request_hook(span, environ):
        """Hook to add user context to Flask spans.

        Args:
            span (opentelemetry.trace.Span): The span representing the request.
            environ (dict): The WSGI environment.
        """
        if not HAS_FLASK_LOGIN:
            return

        try:
            # We check if we are in a request context and if current_user is valid
            if current_user and hasattr(current_user, "is_authenticated"):
                if current_user.is_authenticated:
                    span.set_attribute("user.id", current_user.id)
                    span.set_attribute("user.name", current_user.username)
                    span.set_attribute("timesketch.user_id", current_user.id)
        except Exception:  # pylint: disable=broad-except
            # Best effort - if we are not in a context where current_user is
            # available (e.g. some early middleware), we just skip.
            pass

    class TraceLogFilter(logging.Filter):
        """Logging filter that adds trace ID and span ID to log records.

        This filter acts as a bridge between OpenTelemetry and the standard
        Python logging system. It extracts the current trace_id and span_id
        from the OpenTelemetry context and injects them into the log record.

        This allows log formatters (e.g. in timesketch/app.py) to use
        '%(trace_id)s' and '%(span_id)s' in their format strings without
        raising a KeyError, even if no trace is currently active.
        """

        def filter(self, record):
            if not HAS_OTEL:
                return True

            span_context = trace.get_current_span().get_span_context()
            if span_context.is_valid:
                record.trace_id = trace.format_trace_id(span_context.trace_id)
                record.span_id = trace.format_span_id(span_context.span_id)
            else:
                record.trace_id = "0" * 32
                record.span_id = "0" * 16
            return True

except ImportError:
    HAS_OTEL = False


from timesketch.version import get_version

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


_TRACER_PROVIDER = None


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
    global _TRACER_PROVIDER

    if not is_enabled():
        return

    if _TRACER_PROVIDER:
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
    _TRACER_PROVIDER = TracerProvider(resource=resource)
    # Add the scrubber first to ensure it processes spans before they are batched
    _TRACER_PROVIDER.add_span_processor(SensitiveDataScrubber())
    _TRACER_PROVIDER.add_span_processor(BatchSpanProcessor(trace_exporter))
    trace.set_tracer_provider(_TRACER_PROVIDER)

    # Ensure traces are flushed on shutdown
    import atexit

    atexit.register(_TRACER_PROVIDER.shutdown)


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

    FlaskInstrumentor().instrument_app(
        app,
        request_hook=flask_request_hook,
        **kwargs,
    )


def get_tracer(name: str):
    """Returns a tracer instance.

    Args:
        name (str): The name of the tracer.

    Returns:
        opentelemetry.trace.Tracer: A tracer instance.
    """
    return trace.get_tracer(name)


def get_status_code(name: str):
    """Returns an OpenTelemetry status code.

    Args:
        name (str): The name of the status code (e.g. 'OK', 'ERROR').

    Returns:
        opentelemetry.trace.StatusCode: The status code instance.
    """
    if not HAS_OTEL:
        return None
    return getattr(StatusCode, name.upper(), StatusCode.UNSET)


def set_status_on_current_span(status_code: str, description: str = None):
    """Sets the status on the currently active span.

    Args:
        status_code (str): The status code ('OK' or 'ERROR').
        description (str): Optional description of the status.
    """
    if not is_enabled():
        return

    otel_span = trace.get_current_span()
    if otel_span != INVALID_SPAN:
        code = get_status_code(status_code)
        if code is not None:
            otel_span.set_status(code, description)


def instrument_sqlalchemy(engine, **kwargs):
    """Instruments a SQLAlchemy engine instance.

    This enables automatic capturing of spans for all database operations.

    Args:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine to instrument.
        **kwargs: Additional arguments passed to SQLAlchemyInstrumentor().instrument().
    """
    if not is_enabled() or not HAS_SQLALCHEMY_OTEL:
        return
    SQLAlchemyInstrumentor().instrument(engine=engine, **kwargs)


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
    """Adds a key-value attribute (tag) to the currently active span.

    Simple types (str, bool, int, float) are stored as-is. Complex objects
    are automatically serialized to JSON strings.
    Args:
        name (str): The key name for the attribute.
        value (object): The value to store. Needs to be JSON serializable.
    """
    if not is_enabled():
        return

    otel_span = trace.get_current_span()
    if otel_span != INVALID_SPAN:
        if isinstance(value, (str, bool, int, float)):
            otel_span.set_attribute(name, value)
        else:
            otel_span.set_attribute(name, json.dumps(value))
