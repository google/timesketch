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
"""Timesketch API analyzer result object."""

from __future__ import annotations

import datetime
import json
import logging
from typing import Any, Dict, Generator, List, TYPE_CHECKING

from . import error
from . import resource

if TYPE_CHECKING:
    from .client import TimesketchApi

logger = logging.getLogger("timesketch_api.analyzer")


class AnalyzerResult(resource.BaseResource):
    """Class to store and retrieve session information for an analyzer."""

    def __init__(
        self, timeline_id: int, session_id: int, sketch_id: int, api: TimesketchApi
    ) -> None:
        """Initialize the class.

        Args:
            timeline_id (int): The ID of the timeline.
            session_id (int): The ID of the analyzer session.
            sketch_id (int): The ID of the sketch.
            api (TimesketchApi): An instance of TimesketchApi.
        """
        self._session_id = session_id
        self._sketch_id = sketch_id
        self._timeline_id = timeline_id
        resource_uri = ("{0:s}/sketches/{1:d}/timelines/{2:d}/analysis/").format(
            api.api_root, sketch_id, timeline_id
        )
        super().__init__(api, resource_uri)

    def _get_status_data(self) -> Generator[Dict[str, str], None, None]:
        """Yields a dict for each analyzer status."""
        data = self._fetch_data()
        for entry in data.get("analyzers", []):
            yield {
                "log": str(entry.get("log", "No recorded logs.")),
                "name": str(entry.get("name", "No Name")),
                "results": str(entry.get("results", "")),
                "status": str(entry.get("status", "Unknown")),
                "date": str(
                    entry.get("status_date", datetime.datetime.utcnow().isoformat())
                ),
            }

    def _fetch_data(self) -> Dict[str, Any]:
        """Returns a dict with the analyzer results."""
        response = self.api.session.get(self.resource_uri)
        if not error.check_return_status(response, logger):
            return {}

        data = error.get_response_json(response, logger)

        objects = data.get("objects")
        if not objects:
            return {}

        result_dict: Dict[str, Any] = {}
        for result in objects[0]:
            result_id = result.get("analysissession_id")
            if result_id != self._session_id:
                continue
            status_list = result.get("status", [])
            if len(status_list) != 1:
                continue
            status = status_list[0]

            timeline = result.get("timeline", {})

            result_dict["id"] = result_id
            result_dict.setdefault("analyzers", [])
            result_dict["analyzers"].append(
                {
                    "name": result.get("analyzer_name", "N/A"),
                    "results": result.get("result"),
                    "description": result.get("description", "N/A"),
                    "user": result.get("user", {}).get("username", "System"),
                    "parameters": json.loads(result.get("parameters", "{}")),
                    "status": status.get("status", "Unknown"),
                    "status_date": status.get("updated_at", ""),
                    "log": result.get("log", ""),
                    "created": result.get("created_at"),
                    "timeline": timeline.get("name", "N/A"),
                    "timeline_id": timeline.get("id", -1),
                    "timeline_user": timeline.get("user", {}).get("username", "System"),
                    "timeline_name": timeline.get("name", "N/A"),
                    "timeline_deleted": timeline.get("deleted", False),
                }
            )

        return result_dict

    @property
    def id(self) -> int:
        """Returns the session ID."""
        return self._session_id

    @property
    def log(self) -> str:
        """Returns back logs from the analyzer session, if there are any."""
        return_strings: List[str] = []
        for entry in self._get_status_data():
            return_strings.append(
                "[{0:s}] = {1:s}".format(
                    entry.get("name", "No Name"),
                    entry.get("log", "No recorded logs."),
                )
            )
        return "\n".join(return_strings)

    @property
    def results(self) -> str:
        """Returns the results from the analyzer session."""
        return_strings: List[str] = []
        for entry in self._get_status_data():
            results = entry.get("results")
            if not results:
                results = "No results yet."
            return_strings.append(
                "[{0:s}] = {1:s}".format(entry.get("name", "No Name"), results)
            )
        return "\n".join(return_strings)

    @property
    def results_dict(self) -> Dict[str, List[str]]:
        """Returns the results from the analyzer session as a dict."""
        result_dict: Dict[str, List[str]] = {}
        for entry in self._get_status_data():
            results = entry.get("results")
            if not results:
                results = "No results yet."
            name = entry.get("name", "No Name")
            result_dict.setdefault(name, [])
            result_dict[name].append(results)
        return result_dict

    @property
    def status(self) -> str:
        """Returns the current status of the analyzer run."""
        return_strings: List[str] = []
        for entry in self._get_status_data():
            return_strings.append(
                "[{0:s}] = {1:s}".format(
                    entry.get("name", "No Name"),
                    entry.get("status", "Unknown."),
                )
            )
        return "\n".join(return_strings)

    @property
    def status_dict(self) -> Dict[str, List[str]]:
        """Returns the current status of the analyzers run as a dict."""
        return_dict: Dict[str, List[str]] = {}
        for entry in self._get_status_data():
            name = entry.get("name", "No Name")

            return_dict.setdefault(name, [])
            return_dict[name].append(entry.get("status", "Unknown"))
        return return_dict

    @property
    def status_string(self) -> str:
        """Returns a longer version of a status string."""
        return_strings: List[str] = []
        for entry in self._get_status_data():
            return_strings.append(
                "{0:s} - {1:s}: {2:s}".format(
                    entry.get("name", "No Name"),
                    entry.get("status_date", datetime.datetime.utcnow().isoformat()),
                    entry.get("status", "Unknown."),
                )
            )
        return "\n".join(return_strings)
