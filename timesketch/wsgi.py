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

Example with Gunicorn:
gunicorn -b 127.0.0.1:80 --log-file - --timeout 120 timesketch.wsgi:application

Example configuration for Apache with mod_wsgi (a2enmod mod_wsgi):
<VirtualHost *:443>
        ServerAdmin root@localhost
        SSLEngine On
        SSLCertificateFile    /etc/apache2/cert.crt
        SSLCertificateKeyFile /etc/apache2/cert.key
        WSGIScriptAlias / /path/to/this/file/wsgi.py
</VirtualHost>
"""

# If you installed Timesketch in a virtualenv you need to activate it.
# This needs to be before any imports in order to import from the virtualenv.
# activate_virtualenv = '/path/to/your/virtualenv/bin/activate_this.py'
# execfile(activate_virtualenv, dict(__file__=activate_virtualenv))
import os
import logging

from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

from timesketch.app import configure_logger
from timesketch.app import create_app
from timesketch.models import db_session

logger = logging.getLogger("timesketch.wsgi_server")

configure_logger()
application = create_app()
application_legacy = create_app(legacy_ui=True)

# Setup metrics endpoint.
if os.environ.get("prometheus_multiproc_dir"):
    logger.info("Metrics server enabled")
    GunicornPrometheusMetrics(application, group_by="endpoint")


# pylint: disable=unused-argument
@application.teardown_appcontext
def shutdown_session(exception=None):
    """Remove the database session after every request or app shutdown."""
    db_session.remove()


# pylint: disable=unused-argument
@application_legacy.teardown_appcontext
def shutdown_session_legacy(exception=None):
    """Remove the database session after every request or app shutdown."""
    db_session.remove()
