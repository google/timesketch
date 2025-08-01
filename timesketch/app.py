# Copyright 2014 Google Inc. All rights reserved.
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
"""Entry point for the application."""


import logging
import os
import sys
from typing import Optional, Union


from flask import Flask
from celery import Celery

from flask_login import LoginManager
from flask_login import login_required
from flask_migrate import Migrate
from flask_restful import Api
from flask_wtf import CSRFProtect

from timesketch.api.v1.routes import API_ROUTES as V1_API_ROUTES
from timesketch.lib.errors import ApiHTTPError
from timesketch.models import configure_engine
from timesketch.models import init_db
from timesketch.models.user import User
from timesketch.views.auth import auth_views
from timesketch.views.spa import spa_views


def create_app(
    config: Optional[Union[str, object]] = None,
    legacy_ui: bool = False,
    v3_ui: bool = False,
):
    """Create the Flask app instance that is used throughout the application.

    Args:
        config: (str or object, optional) Path to configuration file as a string
                or an object with config directives.
        legacy_ui: (bool, optional) Temporary flag to indicate to serve the old UI.
                  TODO: Remove this when the old UI has been removed.
        v3_ui: (bool, optional) Flag to indicate to serve the v3 UI.

    Returns:
        Application object (instance of flask.Flask).
    """
    # Determine which frontend assets to serve
    if legacy_ui:
        template_folder = "frontend/dist"
        static_folder = "frontend/dist"
    elif v3_ui:
        template_folder = "frontend-v3/dist"
        static_folder = "frontend-v3/dist/assets"
    else:
        template_folder = "frontend-ng/dist"
        static_folder = "frontend-ng/dist"

    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

    if not config:
        # Where to find the config file
        default_path = "/etc/timesketch/timesketch.conf"
        # Fall back to legacy location of the config file
        legacy_path = "/etc/timesketch.conf"
        if os.path.isfile(default_path):
            config = default_path
        else:
            config = legacy_path

    if isinstance(config, str):
        os.environ["TIMESKETCH_SETTINGS"] = config
        try:
            app.config.from_envvar("TIMESKETCH_SETTINGS")

            if "EMAIL_USER_WHITELIST" in app.config:
                sys.stderr.write(
                    "Warning, EMAIL_USER_WHITELIST has been deprecated. "
                    "Please update timesketch.conf."
                )
        except OSError:
            sys.stderr.write(f"Config file {config} does not exist.\n")
            sys.exit()
    else:
        app.config.from_object(config)

    # Load config values from environment variables.
    # See: https://flask.palletsprojects.com/en/2.3.x/config/
    app.config.from_prefixed_env()

    # Make sure that SECRET_KEY is configured.
    if not app.config["SECRET_KEY"]:
        sys.stderr.write(
            "ERROR: Secret key not present. "
            "Please update your configuration.\n"
            "To generate a key you can use openssl:\n\n"
            "$ openssl rand -base64 32\n\n"
        )
        sys.exit()

    # Plaso version that we support
    if app.config["UPLOAD_ENABLED"]:
        try:
            # pylint: disable=import-outside-toplevel
            from plaso import __version__ as plaso_version

            app.config["PLASO_VERSION"] = plaso_version
        except ImportError:
            pass

    # Setup the database.
    configure_engine(app.config["SQLALCHEMY_DATABASE_URI"])
    db = init_db()

    # Alembic migration support:
    # http://alembic.zzzcomputing.com/en/latest/
    migrate = Migrate()
    migrate.init_app(app, db)

    # Register blueprints. Blueprints are a way to organize your Flask
    # Flask application. See this for more information:
    # http://flask.pocoo.org/docs/latest/blueprints/
    app.register_blueprint(spa_views)
    app.register_blueprint(auth_views)

    # Setup URL routes for the API.
    api_v1 = Api(app, prefix="/api/v1")
    for route in V1_API_ROUTES:
        api_v1.add_resource(*route)

    # Returns 404 for invalid api routes
    # pylint: disable=unused-variable
    @app.route("/api/v1/<path:path>")
    @login_required
    def handle_invalid_api_route(path):
        """Error handler for non-existent API routes.

        Raises:
            ApiHTTPError: Error 404 - not found
        """
        raise ApiHTTPError(
            "The requested URL was not found on the server. If you entered the "
            "URL manually please check your spelling and try again.",
            404,
        )

    # Register error handlers
    # pylint: disable=unused-variable
    @app.errorhandler(ApiHTTPError)
    def handle_api_http_error(error):
        """Error handler for API HTTP errors.

        Returns:
            HTTP response object (instance of flask.wrappers.Response)
        """
        return error.build_response()

    # Setup the login manager.
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "user_views.login"

    # This is used by the flask_login extension.
    # pylint: disable=unused-variable
    @login_manager.user_loader
    def load_user(user_id):
        """Based on a user_id (database primary key for a user) this function
        loads a user from the database. It is used by the Flask-Login extension
        to setup up the session for the user.

        Args:
            user_id: Integer primary key for the user.

        Returns:
            A user object (Instance of timesketch.models.user.User).
        """
        return User.session.get(User, user_id)

    # Setup CSRF protection for the whole application
    CSRFProtect(app)

    return app


def configure_logger():
    """Configure the logger."""

    class NoESFilter(logging.Filter):
        """Custom filter to filter out ES logs"""

        def filter(self, record):
            """Filter out records."""
            return not record.name.lower() == "opensearch"

    logger_formatter = logging.Formatter(
        "[%(asctime)s] %(name)s/%(levelname)s %(message)s"
    )
    logger_filter = NoESFilter()
    logger_object = logging.getLogger("timesketch")

    for handler in logger_object.parent.handlers:
        handler.setFormatter(logger_formatter)
        handler.addFilter(logger_filter)


def create_celery_app():
    """Create a Celery app instance."""
    app = create_app()
    celery = Celery(app.import_name, broker=app.config["CELERY_BROKER_URL"])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        """Add Flask context to the Celery tasks created."""

        abstract = True

        def __call__(self, *args, **kwargs):
            """Return Task within a Flask app context.

            Returns:
                A Task (instance of Celery.celery.Task)
            """
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery
