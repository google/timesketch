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

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Union, TYPE_CHECKING

from . import resource

if TYPE_CHECKING:
    from .client import TimesketchApi

logger = logging.getLogger("timesketch_api.view")


class View(resource.BaseResource):
    """Saved view object.

    Attributes:
        id: Primary key of the view.
        name: Name of the view.
    """

    def __init__(
        self, view_id: int, view_name: str, sketch_id: int, api: TimesketchApi
    ) -> None:
        """Initializes the View object.

        Args:
            view_id (int): Primary key ID for the view.
            view_name (str): The name of the view.
            sketch_id (int): ID of a sketch.
            api (TimesketchApi): Instance of a TimesketchApi object.
        """
        logger.info(
            "View objects will be deprecated soon, consider transitioning "
            "into using the search.Search object instead"
        )
        self.id = view_id
        self.name = view_name
        resource_uri = "sketches/{0:d}/views/{1:d}/".format(sketch_id, self.id)
        super().__init__(api, resource_uri)

    def _get_top_level_attribute(
        self, name: str, default_value: Any = None, refresh: bool = False
    ) -> Any:
        """Returns a top level attribute from a view object.

        Args:
            name (str): String with the attribute name.
            default_value (Any): The default value if the attribute does not exit,
                defaults to None.
            refresh (bool): If set to True then the data will be refreshed.

        Returns:
            Any: The value of the key "name".
        """
        view = self.lazyload_data(refresh_cache=refresh)
        view_objects = view.get("objects")
        if not view_objects:
            return default_value
        if not len(view_objects) == 1:
            return default_value

        first_object = view_objects[0]
        return first_object.get(name, default_value)

    @property
    def description(self) -> str:
        """Property that returns the description value of a view.

        Returns:
            str: Description of the view.
        """
        return self._get_top_level_attribute("description", default_value="")

    @property
    def user(self) -> str:
        """Property that returns the username of the view creator.

        Returns:
            str: The username of the user generating the view.
        """
        user_dict = self._get_top_level_attribute("user", default_value={})
        username = user_dict.get("username")
        if not username:
            return "System"
        return str(username)

    @property
    def query_string(self) -> str:
        """Property that returns the views query string.

        Returns:
            str: OpenSearch query as string.
        """
        return self._get_top_level_attribute("query_string", default_value="")

    @property
    def query_filter(self) -> Union[Dict[str, Any], str]:
        """Property that returns the views filter.

        Returns:
            dict: OpenSearch filter as a dict.
        """
        query_filter_string = self._get_top_level_attribute(
            "query_filter", default_value=""
        )
        if not query_filter_string:
            return ""
        return json.loads(query_filter_string)

    @property
    def query_dsl(self) -> Union[Dict[str, Any], str]:
        """Property that returns the views query DSL.

        Returns:
            dict: OpenSearch DSL as a dict.
        """
        dsl_string = self._get_top_level_attribute("query_dsl", default_value="")
        if not dsl_string:
            return ""
        return json.loads(dsl_string)
