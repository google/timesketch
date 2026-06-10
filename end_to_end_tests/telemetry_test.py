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
        try:
            response = requests.get(f"{jaeger_api_url}/services", timeout=5)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.assertions.fail(f"Jaeger is not reachable at {jaeger_api_url}: {e}")

        # 2. Trigger a simple API request to generate some telemetry
        self.api.list_sketches()

        # 3. Poll Jaeger API until a trace is received or timeout (30 seconds) is hit
        query_url = f"{jaeger_api_url}/traces?service=timesketch"
        traces = []
        for _ in range(30):
            try:
                response = requests.get(query_url, timeout=5)
                response.raise_for_status()
                traces_data = response.json()
                traces = traces_data.get("data", [])
                if traces:
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)

        # 4. Assert that at least one trace has been received by Jaeger
        self.assertions.assertGreater(
            len(traces),
            0,
            "No telemetry traces were found in Jaeger for service 'timesketch'",
        )
        print("Telemetry infrastructure E2E connectivity verified successfully!")


if os.environ.get("TIMESKETCH_OTEL_MODE", "").lower().startswith("otlp-"):
    manager.EndToEndTestManager.register_test(TelemetryTest)
