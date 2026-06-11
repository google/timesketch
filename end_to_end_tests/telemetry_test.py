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
"""End-to-end test for OpenTelemetry connectivity and tracing."""

import os
import time
import uuid

import requests

from end_to_end_tests import interface
from end_to_end_tests import manager


class TelemetryTest(interface.BaseEndToEndTest):
    """End-to-end test for OpenTelemetry connectivity and tracing."""

    NAME = "telemetry_test"

    def _wait_for_jaeger(self):
        """Wait for Jaeger API to become reachable."""
        jaeger_api_url = "http://jaeger:16686/api"
        last_error = None
        for _ in range(30):
            try:
                response = requests.get(f"{jaeger_api_url}/services", timeout=5)
                response.raise_for_status()
                return
            except requests.exceptions.RequestException as e:
                last_error = e
                time.sleep(1)

        self.assertions.fail(
            f"Jaeger is not reachable at {jaeger_api_url}: {last_error}"
        )

    def setup(self):
        """Import a test timeline to ensure search works."""
        self._wait_for_jaeger()
        self.import_timeline("evtx_direct.csv")

    def test_telemetry_connectivity(self):
        """Verify that OpenTelemetry spans are successfully exported to Jaeger."""
        jaeger_api_url = "http://jaeger:16686/api"

        # 1. Trigger a simple API request to generate some telemetry
        self.api.list_sketches()

        # 2. Poll Jaeger API until a trace is received or timeout (30 seconds) is hit
        query_url = f"{jaeger_api_url}/traces?service=timesketch"
        traces = []
        last_error = None
        for _ in range(30):
            try:
                response = requests.get(query_url, timeout=5)
                response.raise_for_status()
                traces_data = response.json()
                traces = traces_data.get("data", [])
                if traces:
                    break
            except requests.exceptions.RequestException as e:
                last_error = e
            time.sleep(1)

        # 3. Assert that at least one trace has been received by Jaeger
        error_msg = "No telemetry traces were found in Jaeger for service 'timesketch'"
        if last_error and not traces:
            error_msg += f" (Last connection error: {last_error})"

        self.assertions.assertGreater(
            len(traces),
            0,
            error_msg,
        )
        print("Telemetry infrastructure E2E connectivity verified successfully!")

    def test_opensearch_telemetry(self):
        """Verify that OpenSearch telemetry spans are exported."""
        jaeger_api_url = "http://jaeger:16686/api"

        # 1. Trigger a search to generate OpenSearch telemetry
        self.sketch.explore("hello_opensearch_telemetry")

        # 2. Poll Jaeger API for opensearch.search spans
        query_url = (
            f"{jaeger_api_url}/traces?service=timesketch&operation=opensearch.search"
        )
        traces = []
        last_error = None
        found_took_ms = False
        for _ in range(30):
            try:
                response = requests.get(query_url, timeout=5)
                response.raise_for_status()
                traces_data = response.json()
                traces = traces_data.get("data", [])

                # Check if we found the took_ms tag in any span
                for trace in traces:
                    for span in trace.get("spans", []):
                        tags = {
                            t.get("key"): t.get("value") for t in span.get("tags", [])
                        }
                        if "db.opensearch.took_ms" in tags and str(
                            tags.get("timesketch.sketch_id")
                        ) == str(self.sketch.id):
                            found_took_ms = True
                            break
                    if found_took_ms:
                        break

                if found_took_ms:
                    break
            except requests.exceptions.RequestException as e:
                last_error = e
            time.sleep(1)

        # 3. Assert trace exists and has the attribute
        error_msg = "No opensearch.search telemetry traces found in Jaeger"
        if last_error and not traces:
            error_msg += f" (Last connection error: {last_error})"
        self.assertions.assertGreater(len(traces), 0, error_msg)

        self.assertions.assertTrue(
            found_took_ms, "Expected db.opensearch.took_ms tag in OpenSearch spans."
        )

    # pylint: disable=too-many-nested-blocks
    def test_sqlalchemy_telemetry(self):
        """Verify that SQLAlchemy telemetry is exported without db.statement."""
        # 1. Trigger an API request that uses the DB (saves to SearchHistory)
        start_time = int(time.time() * 1000000)
        secret_term = f"secret_search_term_{uuid.uuid4().hex}"
        self.sketch.explore(secret_term)

        # 2. Poll Jaeger API until a trace with SQLAlchemy spans is received
        jaeger_api_url = "http://jaeger:16686/api"
        query_url = f"{jaeger_api_url}/traces?service=timesketch&start={start_time}"

        found_db_system = False
        found_db_statement = False
        found_secret_leak = False

        for _ in range(30):
            try:
                response = requests.get(query_url, timeout=5)
                response.raise_for_status()
                traces_data = response.json()
                traces = traces_data.get("data", [])

                for trace in traces:
                    for span in trace.get("spans", []):
                        tags = {
                            tag["key"]: tag["value"] for tag in span.get("tags", [])
                        }
                        if tags.get("db.system") in [
                            "postgresql",
                            "sqlite",
                            "mysql",
                            "mariadb",
                            "oracle",
                            "mssql",
                        ]:
                            found_db_system = True
                            if "db.statement" in tags:
                                found_db_statement = True

                            for val in tags.values():
                                if secret_term in str(val):
                                    found_secret_leak = True

                if found_db_system:
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        self.assertions.assertTrue(
            found_db_system, "No SQLAlchemy spans (db.system) found in Jaeger."
        )
        self.assertions.assertFalse(
            found_db_statement,
            "Expected db.statement to be redacted in SQLAlchemy spans.",
        )
        self.assertions.assertFalse(
            found_secret_leak,
            "Security Risk: The secret search term leaked into SQLAlchemy "
            "span attributes!",
        )

    def test_celery_telemetry_upload(self):
        """Verify that telemetry is generated during a file upload (Celery task)."""
        # 1. Trigger an upload which runs a Celery task
        start_time = int(time.time() * 1000000)
        rand = uuid.uuid4().hex
        sketch = self.api.create_sketch(name=f"test_telemetry_upload_{rand}")
        self.import_timeline("sigma_events.jsonl", sketch=sketch)

        # 2. Poll Jaeger API to ensure traces were recorded
        jaeger_api_url = "http://jaeger:16686/api"
        query_url = f"{jaeger_api_url}/traces?service=timesketch&start={start_time}"

        found_db_system = False
        for _ in range(30):
            try:
                response = requests.get(query_url, timeout=5)
                response.raise_for_status()
                traces_data = response.json()
                traces = traces_data.get("data", [])

                for trace in traces:
                    for span in trace.get("spans", []):
                        tags = {
                            tag["key"]: tag["value"] for tag in span.get("tags", [])
                        }
                        if tags.get("db.system") in ["postgresql", "sqlite"]:
                            found_db_system = True

                if found_db_system:
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        self.assertions.assertTrue(
            found_db_system,
            "No DB telemetry traces found in Jaeger after uploading a file.",
        )


if os.environ.get("TIMESKETCH_OTEL_MODE", "").lower().startswith("otlp-"):
    manager.EndToEndTestManager.register_test(TelemetryTest)
