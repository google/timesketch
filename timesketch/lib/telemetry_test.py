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
"""Tests for OpenTelemetry capabilities."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from timesketch.lib import telemetry
from timesketch.lib.testlib import BaseTest


class TestTelemetry(BaseTest):
    """Tests for telemetry module."""

    def test_sensitive_data_scrubber(self):
        """Test that the SensitiveDataScrubber correctly redacts data."""
        if not telemetry.HAS_OTEL:
            self.skipTest("OpenTelemetry not installed")

        # Setup an in-memory exporter and the scrubber
        exporter = InMemorySpanExporter()
        scrubber = telemetry.SensitiveDataScrubber()

        provider = TracerProvider()
        # The scrubber must run BEFORE the exporter
        provider.add_span_processor(scrubber)
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        tracer = provider.get_tracer(__name__)

        with tracer.start_as_current_span("test-redaction") as span:
            # 1. Test Credential Key Redaction
            span.set_attribute("password", "supersecret")
            span.set_attribute("api_token", "12345-token")

            # 2. Test Keyword in Value Redaction
            span.set_attribute("custom_field", "this is a secret value")

            # 3. Test PII (Email) Redaction in string
            span.set_attribute(
                "db.statement", "SELECT * FROM users WHERE email = 'victim@gmail.com'"
            )

            # 4. Test Analyst Identity Exemption
            span.set_attribute("user.name", "analyst@google.com")
            span.set_attribute("user.id", 123)

        # Get the exported span
        spans = exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        exported_span = spans[0]
        attrs = exported_span.attributes

        # Assertions
        self.assertEqual(attrs["password"], "[REDACTED]")
        self.assertEqual(attrs["api_token"], "[REDACTED]")
        self.assertEqual(attrs["custom_field"], "[REDACTED]")

        # Verify targeted redaction (PII is stripped but query structure remains)
        self.assertEqual(
            attrs["db.statement"], "SELECT * FROM users WHERE email = '[REDACTED_PII]'"
        )

        # Verify analyst identity is NOT redacted
        self.assertEqual(attrs["user.name"], "analyst@google.com")
        self.assertEqual(attrs["user.id"], 123)

        # Verify audit trail
        redacted_keys = attrs["otel.redacted_keys"]
        self.assertIn("password", redacted_keys)
        self.assertIn("api_token", redacted_keys)
        self.assertIn("custom_field (value)", redacted_keys)
        self.assertIn("db.statement (PII)", redacted_keys)
        self.assertNotIn("user.name", redacted_keys)
