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

import os
import sys

from celery import Celery
from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_restful import Api
from flask_wtf import CsrfProtect

from timesketch.api.v1.resources import AggregationResource
from timesketch.api.v1.resources import ExploreResource
from timesketch.api.v1.resources import EventResource
from timesketch.api.v1.resources import EventAnnotationResource
from timesketch.api.v1.resources import SketchResource
from timesketch.api.v1.resources import SketchListResource
from timesketch.api.v1.resources import ViewResource
from timesketch.api.v1.resources import ViewListResource
from timesketch.api.v1.resources import CannedViewListResource
from timesketch.api.v1.resources import UploadFileResource
from timesketch.api.v1.resources import TaskResource
from timesketch.api.v1.resources import StoryListResource
from timesketch.api.v1.resources import StoryResource
from timesketch.api.v1.resources import QueryResource
from timesketch.lib.errors import ApiHTTPError
from timesketch.models import configure_engine
from timesketch.models import init_db
from timesketch.models.sketch import Sketch
from timesketch.models.user import User
from timesketch.ui.views.home import home_views
from timesketch.ui.views.sketch import sketch_views
from timesketch.ui.views.story import story_views
from timesketch.ui.views.user import user_views


def create_app(config=None):
    """Create the Flask app instance that is used throughout the application.

    Args:
        config: Path to configuration file as a string or an object with config
        directives.

    Returns:
        Application object (instance of flask.Flask).
    """
    # Setup the Flask app and load the config.
    app = Flask(
        __name__, template_folder=u'ui/templates', static_folder=u'ui/static')

    if not config:
        config = u'/etc/timesketch.conf'

    if isinstance(config, unicode):
        os.environ[u'TIMESKETCH_SETTINGS'] = config
        try:
            app.config.from_envvar(u'TIMESKETCH_SETTINGS')
        except IOError:
            sys.stderr.write(
                u'Config file {0} does not exist.\n'.format(config))
            sys.exit()
    else:
        app.config.from_object(config)

    # Make sure that SECRET_KEY is configured.
    if not app.config[u'SECRET_KEY']:
        sys.stderr.write(u'ERROR: Secret key not present. '
                         u'Please update your configuration.\n'
                         u'To generate a key you can use openssl:\n\n'
                         u'$ openssl rand -base64 32\n\n')
        sys.exit()

    # Setup the database.
    configure_engine(app.config[u'SQLALCHEMY_DATABASE_URI'])
    db = init_db()

    # Alembic migration support:
    # http://alembic.zzzcomputing.com/en/latest/
    migrate = Migrate()
    migrate.init_app(app, db)

    # Register blueprints. Blueprints are a way to organize your Flask
    # Flask application. See this for more information:
    # http://flask.pocoo.org/docs/latest/blueprints/
    app.register_blueprint(user_views)
    app.register_blueprint(home_views)
    app.register_blueprint(sketch_views)
    app.register_blueprint(story_views)

    # Setup URL routes for the API.
    api_v1 = Api(app, prefix=u'/api/v1')
    api_v1.add_resource(SketchListResource, u'/sketches/')
    api_v1.add_resource(SketchResource, u'/sketches/<int:sketch_id>/')
    api_v1.add_resource(
        AggregationResource, u'/sketches/<int:sketch_id>/aggregation/')
    api_v1.add_resource(ExploreResource, u'/sketches/<int:sketch_id>/explore/')
    api_v1.add_resource(EventResource, u'/sketches/<int:sketch_id>/event/')
    api_v1.add_resource(
        EventAnnotationResource, u'/sketches/<int:sketch_id>/event/annotate/')
    api_v1.add_resource(ViewListResource, u'/sketches/<int:sketch_id>/views/')
    api_v1.add_resource(
        ViewResource, u'/sketches/<int:sketch_id>/views/<int:view_id>/')
    api_v1.add_resource(CannedViewListResource, u'/sketches/<int:sketch_id>/views/canned/')
    api_v1.add_resource(UploadFileResource, u'/upload/')
    api_v1.add_resource(TaskResource, u'/tasks/')
    api_v1.add_resource(
        StoryListResource, u'/sketches/<int:sketch_id>/stories/')
    api_v1.add_resource(
        StoryResource, u'/sketches/<int:sketch_id>/stories/<int:story_id>/')
    api_v1.add_resource(
        QueryResource, u'/sketches/<int:sketch_id>/explore/query/')

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
    login_manager.login_view = u'user_views.login'

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
        return User.query.get(user_id)

    # Setup CSRF protection for the whole application
    CsrfProtect(app)

    return app


def create_celery_app():
    """Create a Celery app instance."""
    app = create_app()
    celery = Celery(app.import_name, broker=app.config[u'CELERY_BROKER_URL'])
    celery.conf.update(app.config)
    TaskBase = celery.Task

    # pylint: disable=no-init
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
    celery.app = app
    return celery
