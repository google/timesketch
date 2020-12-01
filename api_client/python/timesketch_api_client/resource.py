# Copyright 2019 Google Inc. All rights reserved.
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
"""Timesketch API client library."""
import json


class BaseResource:
    """Base resource object."""

    def __init__(self, api, resource_uri):
        """Initialize object.

        Args:
            api: An instance of TimesketchApi object.
            resource_uri: The URI part of the API resource to call.
        """
        self.api = api
        self.resource_uri = resource_uri
        self.resource_data = None

    def lazyload_data(self, refresh_cache=False):
        """Load resource data once and cache the result.

        Args:
            refresh_cache: Boolean indicating if to update cache.

        Returns:
            Dictionary with resource data.
        """
        if not self.resource_data or refresh_cache:
            self.resource_data = self.api.fetch_resource_data(self.resource_uri)
        return self.resource_data

    @property
    def data(self):
        """Property to fetch resource data.

        Returns:
            Dictionary with resource data.
        """
        return self.lazyload_data()


class SketchResource(BaseResource):
    """Sketch resource object."""

    def __init__(self, resource_uri, sketch):
        """Initialize the sketch resource object.

        Args:
            resource_uri: The URI part of the API resource to call.
            sketch: The sketch object of the sketch this resource is tied to.
        """
        super().__init__(sketch.api, resource_uri)

        self._labels = []
        self._resource_id = 0
        self._sketch = sketch
        self._username = ''

    def _get_top_level_attribute(self, name, default_value=None, refresh=False):
        """Returns a top level attribute from a resource object.

        Args:
            name: String with the attribute name.
            default_value: The default value if the attribute does not exit,
                defaults to None.
            refresh: If set to True then the data will be refreshed.

        Returns:
            The dict value of the key "name".
        """
        resource = self.lazyload_data(refresh_cache=refresh)
        resource_objects = resource.get('objects')
        if not resource_objects:
            return default_value

        if not len(resource_objects) == 1:
            return default_value

        first_object = resource_objects[0]
        return first_object.get(name, default_value)

    def add_label(self, label):
        """Add a label to the resource.

        Args:
            label (str): string with the label information.
        """
        if label in self._labels:
            return
        self._labels.append(label)
        self.save()

    def commit(self):
        """Calls the save function if the object has already been saved."""
        if not self._resource_id:
            return
        self.save()

    def delete(self):
        """Deletes the resource from the list of stored resources."""
        raise NotImplementedError

    @property
    def dict(self):
        """Property that returns back a Dict with the results."""
        return self.to_dict()

    def from_manual(self, **kwargs):
        """Initialize the resource object by running a raw API request.

        The API request functionality should be implemented by other functions
        that inherit this as a base class.

        Args:
            kwargs (dict[str, object]): Depending on the resource they may
                require different sets of arguments to be able to run a raw
                API request.

        Raises:
            ValueError: If there are any unused keyword arguments passed to
                the function.
        """
        if kwargs:
            raise ValueError('Unused keyword arguments: {0:s}.'.format(
                ', '.join(kwargs.keys())))

    def from_saved(self, resource_id):
        """Initialize the resource object from a saved resource.

        Args:
            resource_id: integer value for the saved resource (primary key).
        """
        raise NotImplementedError

    @property
    def id(self):
        """Property that returns back the resource ID."""
        return self._resource_id

    @property
    def json(self):
        """Property that returns back a JSON object with the results."""
        return json.dumps(self.dict)

    @property
    def labels(self):
        """Property that returns a list of the resource labels."""
        return self._labels

    @property
    def table(self):
        """Property that returns a pandas DataFrame."""
        return self.to_pandas()

    @property
    def user(self):
        """Property that returns the username of who ran the aggregation."""
        if not self._username:
            return 'System'
        return self._username

    def to_dict(self):
        """Returns a dict."""
        raise NotImplementedError

    def to_pandas(self):
        """Returns a pandas DataFrame."""
        raise NotImplementedError

    def save(self):
        """Sends a request to save the resource."""
        raise NotImplementedError
