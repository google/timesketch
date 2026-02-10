#!/usr/bin/env python
# Copyright 2015 Google Inc. All rights reserved.
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
"""This module is for creating the app for a WSGI server.

It initializes a single instance of the Flask application based on the
environment variable `TIMESKETCH_UI_MODE`.

Supported modes:
- ng (default): Loads the default Vuetify 2 frontend (frontend-ng).
- v3: Loads the new Vuetify 3 frontend (frontend-v3).
- legacy: Loads the old Vuetify2 frontend.

Example with Gunicorn:
    # Run the NG UI
    gunicorn -b 127.0.0.1:8000 --timeout 120 timesketch.wsgi:application

    # Run the V3 UI
    export TIMESKETCH_UI_MODE=v3
    gunicorn -b 127.0.0.1:8000 --timeout 120 timesketch.wsgi:application
"""

import os
import logging
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics
from timesketch.app import configure_logger
from timesketch.app import create_app
from timesketch.models import db_session

logger = logging.getLogger("timesketch.wsgi_server")

configure_logger()

# Determine which UI to load based on environment variable
ui_mode = os.environ.get("TIMESKETCH_UI_MODE", "ng")

if ui_mode == "legacy":
    application = create_app(legacy_ui=True)
    logger.info("Starting Timesketch with Legacy UI")
elif ui_mode == "v3":
    application = create_app(v3_ui=True)
    logger.info("Starting Timesketch with V3 UI")
else:
    application = create_app()
    logger.info("Starting Timesketch with NG UI")

# Setup metrics endpoint.
if os.environ.get("PROMETHEUS_MULTIPROC_DIR"):
    logger.info("Metrics server enabled")
    GunicornPrometheusMetrics(application, group_by="endpoint")


@application.teardown_appcontext
def shutdown_session(_exception=None):
    """Remove the database session after every request or app shutdown.

    Args:
        _exception: An exception that occurred during the request, if any.
                    (Unused, but required by the Flask teardown signal).
    """
    db_session.remove()
