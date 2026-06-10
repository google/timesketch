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

    def test_telemetry_connectivity(self):
        """Verify that OpenTelemetry spans are successfully exported to Jaeger."""
        # 1. Check if Jaeger API is reachable.
        jaeger_api_url = "http://jaeger:16686/api"
        last_error = None
        for _ in range(30):
            try:
                response = requests.get(f"{jaeger_api_url}/services", timeout=5)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as e:
                last_error = e
                time.sleep(1)
        else:
            self.assertions.fail(
                f"Jaeger is not reachable at {jaeger_api_url}: {last_error}"
            )

        # 2. Trigger a simple API request to generate some telemetry
        self.api.list_sketches()

        # 3. Poll Jaeger API until a trace is received or timeout (30 seconds) is hit
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

        # 4. Assert that at least one trace has been received by Jaeger
        error_msg = "No telemetry traces were found in Jaeger for service 'timesketch'"
        if last_error and not traces:
            error_msg += f" (Last connection error: {last_error})"

        self.assertions.assertGreater(
            len(traces),
            0,
            error_msg,
        )
        print("Telemetry infrastructure E2E connectivity verified successfully!")

    def test_sqlalchemy_telemetry(self):
        """Verify that SQLAlchemy telemetry is exported without db.statement."""
        # 1. Trigger an API request that uses the DB
        self.api.list_sketches()

        # 2. Poll Jaeger API until a trace with SQLAlchemy spans is received
        jaeger_api_url = "http://jaeger:16686/api"
        query_url = f"{jaeger_api_url}/traces?service=timesketch"
        
        found_db_system = False
        found_db_statement = False

        for _ in range(30):
            try:
                response = requests.get(query_url, timeout=5)
                response.raise_for_status()
                traces_data = response.json()
                traces = traces_data.get("data", [])

                for trace in traces:
                    for span in trace.get("spans", []):
                        tags = {tag["key"]: tag["value"] for tag in span.get("tags", [])}
                        if tags.get("db.system") in ["postgresql", "sqlite", "mysql", "mariadb", "oracle", "mssql"]:
                            found_db_system = True
                            if "db.statement" in tags:
                                found_db_statement = True

                if found_db_system:
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        self.assertions.assertTrue(
            found_db_system, "No SQLAlchemy spans (db.system) found in Jaeger."
        )
        self.assertions.assertFalse(
            found_db_statement, "Expected db.statement to be redacted in SQLAlchemy spans."
        )

    def test_celery_telemetry_upload(self):
        """Verify that telemetry is generated during a file upload (Celery task)."""
        # 1. Trigger an upload which runs a Celery task
        rand = uuid.uuid4().hex
        sketch = self.api.create_sketch(name=f"test_telemetry_upload_{rand}")
        file_path = "/usr/local/src/timesketch/end_to_end_tests/test_data/sigma_events.jsonl"
        self.import_timeline(file_path, sketch=sketch)

        # 2. Poll Jaeger API to ensure traces were recorded
        jaeger_api_url = "http://jaeger:16686/api"
        query_url = f"{jaeger_api_url}/traces?service=timesketch"
        
        found_db_system = False
        for _ in range(30):
            try:
                response = requests.get(query_url, timeout=5)
                response.raise_for_status()
                traces_data = response.json()
                traces = traces_data.get("data", [])

                for trace in traces:
                    for span in trace.get("spans", []):
                        tags = {tag["key"]: tag["value"] for tag in span.get("tags", [])}
                        if tags.get("db.system") in ["postgresql", "sqlite"]:
                            found_db_system = True

                if found_db_system:
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        self.assertions.assertTrue(
            found_db_system, "No DB telemetry traces found in Jaeger after uploading a file."
        )


if os.environ.get("TIMESKETCH_OTEL_MODE", "").lower().startswith("otlp-"):
    manager.EndToEndTestManager.register_test(TelemetryTest)
