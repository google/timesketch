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

import time

import requests

from end_to_end_tests import interface
from end_to_end_tests import manager


class TelemetryTest(interface.BaseEndToEndTest):
    """End-to-end test for OpenTelemetry connectivity and tracing."""

    NAME = "telemetry_test"

    def test_telemetry_connectivity(self):
        """Verify that OpenTelemetry spans are successfully exported to Jaeger."""
        # 1. Check if Jaeger API is reachable. If not, skip gracefully.
        jaeger_api_url = "http://jaeger:16686/api"
        try:
            response = requests.get(f"{jaeger_api_url}/services", timeout=5)
            response.raise_for_status()
        except requests.exceptions.RequestException:
            print("Jaeger is not reachable. Telemetry profile is not active. Skipping.")
            return

        # 2. Trigger a simple API request to generate some telemetry
        self.api.list_sketches()

        # 3. Wait for the asynchronously buffered spans to flush to the collector
        time.sleep(5)

        # 4. Query Jaeger's REST API for traces of the default 'timesketch' service
        query_url = f"{jaeger_api_url}/traces?service=timesketch"
        response = requests.get(query_url, timeout=5)
        response.raise_for_status()
        traces_data = response.json()

        # 5. Assert that at least one trace has been received by Jaeger
        traces = traces_data.get("data", [])
        self.assertions.assertGreater(
            len(traces),
            0,
            "No telemetry traces were found in Jaeger for service 'timesketch'",
        )
        print("Telemetry infrastructure E2E connectivity verified successfully!")


manager.EndToEndTestManager.register_test(TelemetryTest)
