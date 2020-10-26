# Copyright 2020 Google Inc. All rights reserved.
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
"""Attribute resources for version 1 of the Timesketch API."""

import logging

from flask import request
from flask import abort
from flask_restful import Resource
from flask_login import login_required
from flask_login import current_user

from timesketch.api.v1 import resources
from timesketch.api.v1 import utils
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.models import db_session
from timesketch.models.sketch import AttributeContainer
from timesketch.models.sketch import Attribute
from timesketch.models.sketch import Sketch


logger = logging.getLogger('timesketch.sketch_api')


class AttributeResource(resources.ResourceMixin, Resource):
    """Resource for sketch attributes."""

    def _validate_form_entry(self, form, key_to_check):
        """Check a form value and return an error string if applicable.

        Args:
            form (dict): the dict that keeps the form data.
            key_to_check (str): the key in the form data to check against.

        Returns:
            An empty string if there are no issues, otherwise an
            error string to use to abort.
        """
        value = form.get(key_to_check)
        if not value:
            return 'Unable to save an attribute without a {0:s}.'.format(
                key_to_check)

        if not isinstance(value, str):
            return 'Unable to save an attribute without a {0:s}.'.format(
                key_to_check)

        return ''

    @login_required
    def get(self, sketch_id):
        """Handles GET request to the resource.

        Returns:
            An analysis in JSON (instance of flask.wrappers.Response)
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        if not sketch.has_permission(current_user, 'read'):
            abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'User does not have read access to sketch')

        return self.to_json(utils.get_sketch_attributes(sketch))

    @login_required
    def post(self, sketch_id):
        """Handles POST request to the resource.

        Returns:
            A string with the response from running the analyzer.
        """
        sketch = Sketch.query.get_with_acl(sketch_id)
        if not sketch:
            abort(
                HTTP_STATUS_CODE_NOT_FOUND, 'No sketch found with this ID.')

        if not sketch.has_permission(current_user, 'write'):
            return abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'User does not have write permission on the sketch.')

        form = request.json
        if not form:
            form = request.data

        if not form:
            return abort(
                HTTP_STATUS_CODE_FORBIDDEN,
                'Unable to add or remove an attribute from a '
                'sketch without any data submitted.')

        for check in ['name', 'ontology']:
            error_message = self._validate_form_entry(form, check)
            if error_message:
                return abort(
                    HTTP_STATUS_CODE_BAD_REQUEST, error_message)

        action = form.get('action', '')
        if action not in ('post', 'delete'):
            return abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                'Action needs to be either "post" or "delete"')

        name = form.get('name')
        ontology = form.get('ontology', 'text')

        if action == 'post':
            values = form.get('values')
            if not values:
                return abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    'Missing values from the request.')

            if not isinstance(values, (list, tuple)):
                return abort(
                    HTTP_STATUS_CODE_BAD_REQUEST, 'Values needs to be a list.')

            if any([not isinstance(x, str) for x in values]):
                return abort(
                    HTTP_STATUS_CODE_BAD_REQUEST,
                    'All values needs to be stored as strings.')

            for container in sketch.attributes:
                if container.name == name:
                    return abort(
                        HTTP_STATUS_CODE_BAD_REQUEST,
                        'Unable to add the attribute, it already exists.')

            container = AttributeContainer(
                user=current_user,
                sketch=sketch,
                name=name,
                ontology=ontology)
            db_session.add(container)
            db_session.commit()

            for value in values:
                attribute = Attribute(
                    user=current_user,
                    attributecontainer=container,
                    value=value)
                container.attributes.append(attribute)
                db_session.add(attribute)
                db_session.commit()

            db_session.add(container)
            db_session.commit()

            return HTTP_STATUS_CODE_OK

        if action != 'delete':
            return abort(
                HTTP_STATUS_CODE_BAD_REQUEST, 'Unable to proceed.')

        for container in sketch.attributes:
            if container.name != name:
                continue
            for attribute in container.attributes:
                container.attributes.remove(attribute)
            sketch.attributes.remove(container)
            db_session.commit()

        return HTTP_STATUS_CODE_OK
