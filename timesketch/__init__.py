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

from flask import Flask
from flask_login import LoginManager
from flask_restful import Api
from flask_wtf import CsrfProtect
from timesketch.api.v1.resources import ExploreResource
from timesketch.api.v1.resources import EventResource
from timesketch.api.v1.resources import EventAnnotationResource
from timesketch.api.v1.resources import SketchResource
from timesketch.api.v1.resources import SketchListResource
from timesketch.api.v1.resources import ViewResource
from timesketch.api.v1.resources import ViewListResource
from timesketch.models import configure_engine
from timesketch.models import init_db
from timesketch.models.sketch import Sketch
from timesketch.models.user import User
from timesketch.ui.views.home import home_views
from timesketch.ui.views.sketch import sketch_views
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
        __name__, template_folder='ui/templates', static_folder='ui/static')

    if not config:
        config = '/etc/timesketch.conf'
    if isinstance(config, basestring):
        os.environ['TIMESKETCH_SETTINGS'] = config
        app.config.from_envvar('TIMESKETCH_SETTINGS')
    else:
        app.config.from_object(config)

    # Setup the database.
    configure_engine(app.config['SQLALCHEMY_DATABASE_URI'])
    init_db()

    # Register blueprints. Blueprints are a way to organize your Flask
    # Flask application. See this for more information:
    # http://flask.pocoo.org/docs/latest/blueprints/
    app.register_blueprint(user_views)
    app.register_blueprint(home_views)
    app.register_blueprint(sketch_views)

    # Setup URL routes for the API.
    api_v1 = Api(app, prefix='/api/v1')
    api_v1.add_resource(SketchListResource, '/sketches/')
    api_v1.add_resource(SketchResource, '/sketches/<int:sketch_id>/')
    api_v1.add_resource(ExploreResource, '/sketches/<int:sketch_id>/explore/')
    api_v1.add_resource(EventResource, '/sketches/<int:sketch_id>/event/')
    api_v1.add_resource(
        EventAnnotationResource, '/sketches/<int:sketch_id>/event/annotate/')
    api_v1.add_resource(ViewListResource, '/sketches/<int:sketch_id>/views/')
    api_v1.add_resource(
        ViewResource, '/sketches/<int:sketch_id>/views/<int:view_id>/')

    # Setup the login manager.
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'user_views.login'

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
