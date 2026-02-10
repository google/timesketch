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
"""Gunicorn configuration file for Timesketch.

This is used to configure Gunicorn for structured logging.
If the environment variable ENABLE_STRUCTURED_LOGGING is set to "true",
it will configure Gunicorn to output logs in JSON format.
"""

import json
import logging
import time
import os


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


USE_STRUCTURED_LOGGING = (
    os.environ.get("ENABLE_STRUCTURED_LOGGING", "false").lower() == "true"
)

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
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
        "gunicorn.access": {
            "level": "INFO",
            "handlers": ["console"],
            "propagate": False,
        },
    },
}

if USE_STRUCTURED_LOGGING:
    logconfig_dict = STRUCTURED_LOGGING_CONFIG
