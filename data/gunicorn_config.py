# Copyright 2021 Google Inc. All rights reserved.
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
"""Gunicorn configuration for metrics endpoint."""
import os
import glob
import pathlib

from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

METRICS_HTTP_HOST = os.environ.get("TIMESKETCH_METRICS_HOST", "0.0.0.0")
METRICS_HTTP_PORT = os.environ.get("TIMESKETCH_METRICS_PORT", 8080)
METRICS_DB_DIR = os.environ.get("prometheus_multiproc_dir", None)
METRICS_ENABLED = METRICS_DB_DIR


# Reference: https://github.com/rycus86/prometheus_flask_exporter#wsgi
# pylint: disable=unused-argument
def when_ready(server):
    """Start metrics server when Timesketch app is ready."""
    # Exit early if we don't have the necessary environment set up.
    if not METRICS_ENABLED:
        return

    # Clean up andy old prometheus database files
    if os.path.isdir(METRICS_DB_DIR):
        files = glob.glob(METRICS_DB_DIR + "/*.db")
        for file in files:
            os.remove(file)
    else:
        pathlib.Path(METRICS_DB_DIR).mkdir(parents=True, exist_ok=True)

    GunicornPrometheusMetrics.start_http_server_when_ready(
        int(METRICS_HTTP_PORT), METRICS_HTTP_HOST
    )


def child_exit(server, worker):
    """Mark a child worker as exited."""
    if METRICS_ENABLED:
        GunicornPrometheusMetrics.mark_process_dead_on_child_exit(worker.pid)
