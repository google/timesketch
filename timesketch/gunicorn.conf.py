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
"""Gunicorn configuration file for Timesketch."""

import json
import logging
import time
import os
import glob
import pathlib
import runpy

# Metrics imports
try:
    from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

    HAS_METRICS = True
except ImportError:
    HAS_METRICS = False


def get_config_path():
    """Returns the path to the configuration file."""
    if "TIMESKETCH_SETTINGS" in os.environ:
        return os.environ["TIMESKETCH_SETTINGS"]

    # Standard locations
    default_path = "/etc/timesketch/timesketch.conf"
    legacy_path = "/etc/timesketch.conf"

    if os.path.isfile(default_path):
        return default_path
    if os.path.isfile(legacy_path):
        return legacy_path

    return None


def get_debug_status():
    """Read configuration file and return DEBUG status."""
    config_path = get_config_path()
    if not config_path:
        return False

    try:
        config = runpy.run_path(config_path)
        return config.get("DEBUG", False)
    except Exception:  # pylint: disable=broad-exception-caught
        return False


DEBUG = get_debug_status()

# Metrics Configuration
METRICS_HTTP_HOST = os.environ.get("TIMESKETCH_METRICS_HOST", "0.0.0.0")
METRICS_HTTP_PORT = os.environ.get("TIMESKETCH_METRICS_PORT", 8080)
METRICS_DB_DIR = os.environ.get("PROMETHEUS_MULTIPROC_DIR", None)
METRICS_ENABLED = METRICS_DB_DIR and HAS_METRICS

# Logging Configuration
USE_STRUCTURED_LOGGING = (
    os.environ.get("ENABLE_STRUCTURED_LOGGING", "false").lower() == "true"
)

# Determine Log Level based on DEBUG setting
if DEBUG:
    error_log_level = "DEBUG"
    access_log_level = "INFO"
else:
    error_log_level = "INFO"
    access_log_level = "WARNING"


class JSONFormatter(logging.Formatter):
    def format(self, record):
        level = record.levelname.upper()
        severity = "WARNING" if level == "WARN" else level
        log_record = {
            "message": record.getMessage(),
            "severity": severity,
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)
            ),
            "logger": record.name,
        }
        return json.dumps(log_record)


STRUCTURED_LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": JSONFormatter,
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "json",
        }
    },
    "loggers": {
        "gunicorn.error": {
            "level": error_log_level,
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": access_log_level,
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

if USE_STRUCTURED_LOGGING:
    logconfig_dict = STRUCTURED_LOGGING_CONFIG


# Gunicorn Hooks for Metrics
def when_ready(_server):
    """Start metrics server when Timesketch app is ready."""
    if not METRICS_ENABLED:
        return

    # Clean up any old prometheus database files
    if os.path.isdir(METRICS_DB_DIR):
        files = glob.glob(METRICS_DB_DIR + "/*.db")
        for file in files:
            os.remove(file)
    else:
        pathlib.Path(METRICS_DB_DIR).mkdir(parents=True, exist_ok=True)

    GunicornPrometheusMetrics.start_http_server_when_ready(
        int(METRICS_HTTP_PORT), METRICS_HTTP_HOST
    )


def child_exit(_server, worker):
    """Mark a child worker as exited."""
    if METRICS_ENABLED:
        GunicornPrometheusMetrics.mark_process_dead_on_child_exit(worker.pid)
