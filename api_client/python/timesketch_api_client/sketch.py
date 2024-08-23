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
from __future__ import unicode_literals

import copy
import os
import json
import logging

import pandas

from . import analyzer
from . import aggregation
from . import definitions
from . import error
from . import graph
from . import index as api_index
from . import resource
from . import search
from . import searchtemplate
from . import story
from . import timeline
from . import scenario as scenario_lib


logger = logging.getLogger("timesketch_api.sketch")


class Sketch(resource.BaseResource):
    """Timesketch sketch object.

    A sketch in Timesketch is a collection of one or more timelines. It has
    access control and its own namespace for things like labels and comments.

    Attributes:
        id: The ID of the sketch.
        api: An instance of TimesketchApi object.
    """

    # Add in necessary fields in data ingested via a different mechanism.
    _NECESSARY_DATA_FIELDS = frozenset(["timestamp", "datetime", "message"])

    def __init__(self, sketch_id, api, sketch_name=None):
        """Initializes the Sketch object.

        Args:
            sketch_id: Primary key ID of the sketch.
            api: An instance of TimesketchApi object.
            sketch_name: Name of the sketch (optional).
        """
        self.id = sketch_id
        self.api = api
        self._archived = None
        self._sketch_name = sketch_name
        super().__init__(api=api, resource_uri=f"sketches/{self.id}")

    @property
    def acl(self):
        """Property that returns back a ACL dict."""
        data = self.lazyload_data(refresh_cache=True)
        objects = data.get("objects")
        if not objects:
            return {}
        data_object = objects[0]
        permission_string = data_object.get("all_permissions")
        if not permission_string:
            return {}
        return json.loads(permission_string)

    @property
    def attributes(self):
        """Property that returns the sketch attributes."""
        data = self.lazyload_data(refresh_cache=True)
        meta = data.get("meta", {})
        return meta.get("attributes", {})

    @property
    def attributes_table(self):
        """DEPRECATED: Property that returns the sketch attributes
        as a data frame.

        Given the fluid setup of attributes, this is not a good way to
        represent the data. Use the attributes property instead."""
        data = self.lazyload_data(refresh_cache=True)
        meta = data.get("meta", {})
        attributes = meta.get("attributes", [])

        data_frame = pandas.DataFrame(attributes)
        data_frame.columns = ["attribute", "values", "ontology"]

        return data_frame

    @property
    def description(self):
        """Property that returns sketch description.

        Returns:
            Sketch description as string.
        """
        sketch = self.lazyload_data()
        return sketch["objects"][0]["description"]

    @description.setter
    def description(self, description_value):
        """Change the sketch description to a new value."""
        if not isinstance(description_value, str):
            logger.error("Unable to change the name to a non string value")
            return

        resource_url = "{0:s}/sketches/{1:d}/".format(self.api.api_root, self.id)

        data = {
            "description": description_value,
        }
        response = self.api.session.post(resource_url, json=data)
        _ = error.check_return_status(response, logger)

        # Force the new description to be re-loaded.
        _ = self.lazyload_data(refresh_cache=True)

    @property
    def labels(self):
        """Property that returns the sketch labels."""
        data = self.lazyload_data(refresh_cache=True)
        objects = data.get("objects", [])
        if not objects:
            return []

        sketch_data = objects[0]
        label_string = sketch_data.get("label_string", "")
        if label_string:
            return json.loads(label_string)

        return []

    @property
    def last_activity(self):
        """Property that returns the last activity.

        Returns:
            Sketch last activity as a string.
        """
        data = self.lazyload_data(refresh_cache=True)
        meta = data.get("meta", {})
        return meta.get("last_activity", "")

    @property
    def my_acl(self):
        """Property that returns back the ACL for the current user."""
        data = self.lazyload_data(refresh_cache=True)
        objects = data.get("objects")
        if not objects:
            return []
        data_object = objects[0]
        permission_string = data_object.get("my_permissions")
        if not permission_string:
            return []
        return json.loads(permission_string)

    @property
    def name(self):
        """Property that returns sketch name.

        Returns:
            Sketch name as string.
        """
        if not self._sketch_name:
            sketch = self.lazyload_data()
            self._sketch_name = sketch["objects"][0]["name"]
        return self._sketch_name

    @name.setter
    def name(self, name_value):
        """Change the name of the sketch to a new value."""
        if not isinstance(name_value, str):
            logger.error("Unable to change the name to a non string value")
            return

        resource_url = "{0:s}/sketches/{1:d}/".format(self.api.api_root, self.id)

        data = {
            "name": name_value,
        }
        response = self.api.session.post(resource_url, json=data)
        _ = error.check_return_status(response, logger)

        # Force the new name to be re-loaded.
        self._sketch_name = ""
        _ = self.lazyload_data(refresh_cache=True)

    @property
    def status(self):
        """Property that returns sketch status.

        Returns:
            Sketch status as string.
        """
        data = self.lazyload_data(refresh_cache=True)
        objects = data.get("objects")
        if not objects:
            return "Unknown"

        if not isinstance(objects, (list, tuple)):
            return "Unknown"

        first_object = objects[0]
        status_list = first_object.get("status")

        if not status_list:
            return "Unknown"

        if len(status_list) < 1:
            return "Unknown"

        return status_list[0].get("status", "Unknown")

    def add_attribute_list(self, name, values, ontology="text"):
        """Adds or modifies attributes to the sketch.

        Args:
            name (str): The name of the attribute.
            values (list): A list of values (in their correct type according
                to the ontology).
            ontology (str): The ontology (matches with
                /data/ontology.yaml), which defines how the attribute
                is interpreted.

        Raises:
            ValueError: If any of the parameters are of the wrong type.

        Returns:
            A dict with the results from the operation.
        """
        if not isinstance(name, str):
            raise ValueError("Name needs to be a string.")

        if not isinstance(ontology, str):
            raise ValueError("Ontology needs to be a string.")

        resource_url = "{0:s}/sketches/{1:d}/attribute/".format(
            self.api.api_root, self.id
        )

        data = {
            "name": name,
            "values": values,
            "ontology": ontology,
        }
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            logger.error("Unable to add the attribute to the sketch.")

        return error.get_response_json(response, logger)

    def add_attribute(self, name, value, ontology="text"):
        """Adds or modifies an attribute to the sketch.

        Args:
            name (str): The name of the attribute.
            value (str): Value of the attribute, stored as a string.
            ontology (str): The ontology (matches with
                /data/ontology.yaml), which defines
                how the attribute is interpreted.

        Raises:
            ValueError: If any of the parameters are of the wrong type.

        Returns:
            A dict with the results from the operation.
        """
        if not isinstance(name, str):
            raise ValueError("Name needs to be a string.")

        return self.add_attribute_list(name=name, values=[value], ontology=ontology)

    def add_sketch_label(self, label):
        """Add a label to the sketch.

        Args:
            label (str): A string with the label to add to the sketch.

        Returns:
            bool: A boolean to indicate whether the label was successfully
                  added to the sketch.
        """
        if label in self.labels:
            logger.error("Label [{0:s}] already applied to sketch.".format(label))
            return False

        resource_url = "{0:s}/sketches/{1:d}/".format(self.api.api_root, self.id)

        data = {
            "labels": [label],
            "label_action": "add",
        }
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            logger.error("Unable to add the label [{0:s}] to the sketch.".format(label))

        return status

    def remove_attribute(self, name, ontology):
        """Remove an attribute from the sketch.

        Args:
            name (str): The name of the attribute.
            ontology (str): The ontology (matches with
                /data/ontology.yaml), which defines how the attribute
                is interpreted.

        Raises:
            ValueError: If any of the parameters are of the wrong type.

        Returns:
            Boolean value whether the attribute was successfully
            removed or not.
        """
        if not isinstance(name, str):
            raise ValueError("Name needs to be a string.")

        resource_url = "{0:s}/sketches/{1:d}/attribute/".format(
            self.api.api_root, self.id
        )

        data = {
            "name": name,
            "ontology": ontology,
        }
        response = self.api.session.delete(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            logger.error("Unable to remove the attribute from the sketch.")

        return status

    def remove_sketch_label(self, label):
        """Remove a label from the sketch.

        Args:
            label (str): A string with the label to remove from the sketch.

        Returns:
            bool: A boolean to indicate whether the label was successfully
                  removed from the sketch.
        """
        if label not in self.labels:
            logger.error(
                "Unable to remove label [{0:s}], not a label "
                "attached to this sketch.".format(label)
            )
            return False

        resource_url = "{0:s}/sketches/{1:d}/".format(self.api.api_root, self.id)

        data = {
            "labels": [label],
            "label_action": "remove",
        }
        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            logger.error("Unable to remove the label from the sketch.")

        return status

    def create_view(self, name, query_string="", query_dsl="", query_filter=None):
        """Create a view object.

        Args:
            name (str): the name of the view.
            query_string (str): OpenSearch query string. This is optional
                yet either a query string or a query DSL is required.
            query_dsl (str): OpenSearch query DSL as JSON string. This is
                optional yet either a query string or a query DSL is required.
            query_filter (dict): Filter for the query as a dict.

        Raises:
            ValueError: if neither query_string nor query_dsl is provided or
                if query_filter is not a dict.
            RuntimeError: if a view wasn't created for some reason.

        Returns:
            A search.Search object that has been saved to the database.
        """
        logger.warning(
            "View objects will be deprecated shortly, use search.Search "
            "and call the search_obj.save() function to save a search."
        )

        if not (query_string or query_dsl):
            raise ValueError("You need to supply a query string or a dsl")

        if self.is_archived():
            raise RuntimeError("Unable create a view on an archived sketch.")

        search_obj = search.Search(sketch=self)
        search_obj.from_manual(
            query_string=query_string,
            query_dsl=query_dsl,
            query_filter=query_filter,
        )
        search_obj.name = name
        search_obj.save()
        return search_obj

    def create_story(self, title):
        """Create a story object.

        Args:
            title: the title of the story.

        Raises:
            RuntimeError: if a story wasn't created for some reason.

        Returns:
            A story object (instance of Story) for the newly
            created story.
        """
        if self.is_archived():
            raise RuntimeError("Unable to create a story in an archived sketch.")

        resource_url = "{0:s}/sketches/{1:d}/stories/".format(
            self.api.api_root, self.id
        )
        data = {"title": title, "content": ""}

        response = self.api.session.post(resource_url, json=data)

        status = error.check_return_status(response, logger)
        if not status:
            error.error_message(
                response, "Unable to create a story", error=RuntimeError
            )

        response_json = error.get_response_json(response, logger)
        story_dict = response_json.get("objects", [{}])[0]
        return story.Story(story_id=story_dict.get("id", 0), sketch=self, api=self.api)

    def delete(self):
        """Deletes the sketch."""
        if self.is_archived():
            raise RuntimeError(
                "Unable to delete an archived sketch, first unarchive then delete."
            )

        resource_url = "{0:s}/sketches/{1:d}/".format(self.api.api_root, self.id)
        response = self.api.session.delete(resource_url)
        return error.check_return_status(response, logger)

    def add_to_acl(
        self,
        user_list=None,
        group_list=None,
        make_public=False,
        permissions=None,
    ):
        """Add users or groups to the sketch ACL.

        Args:
            user_list: optional list of users to add to the ACL
                of the sketch. Each user is a string.
            group_list: optional list of groups to add to the ACL
                of the sketch. Each user is a string.
            make_public: Optional boolean indicating the sketch should be
                marked as public.
            permissions: optional list of permissions (read, write, delete).
                If not the default set of permissions are applied (read, write)

        Returns:
            A boolean indicating whether the ACL change was successful.
        """
        if not user_list and not group_list and not make_public:
            return False

        resource_url = "{0:s}/sketches/{1:d}/collaborators/".format(
            self.api.api_root, self.id
        )

        data = {}
        if group_list:
            group_list_corrected = [str(x).strip() for x in group_list]
            data["groups"] = group_list_corrected

        if user_list:
            user_list_corrected = [str(x).strip() for x in user_list]
            data["users"] = user_list_corrected

        if make_public:
            data["public"] = "true"

        if permissions:
            allowed_permissions = set(["read", "write", "delete"])
            use_permissions = list(allowed_permissions.intersection(set(permissions)))
            if set(use_permissions) != set(permissions):
                logger.warning(
                    "Some permissions are invalid: {0:s}".format(
                        ", ".join(
                            list(set(permissions).difference(set(use_permissions)))
                        )
                    )
                )

            if not use_permissions:
                logger.error("No permissions left to add.")
                return False

            data["permissions"] = json.dumps(use_permissions)

        if not data:
            return True

        response = self.api.session.post(resource_url, json=data)
        # Refresh the sketch data to reflect ACL changes.
        _ = self.lazyload_data(refresh_cache=True)
        return error.check_return_status(response, logger)

    def list_aggregation_groups(self):
        """List all saved aggregation groups for this sketch.

        Returns:
            List of aggregation groups (instances of AggregationGroup objects)
        """
        if self.is_archived():
            raise RuntimeError(
                "Unable to list aggregation groups on an archived sketch."
            )
        groups = []
        data = self.api.fetch_resource_data(f"sketches/{self.id}/aggregation/group/")

        for group_dict in data.get("objects", []):
            if not group_dict.get("id"):
                continue
            group = aggregation.AggregationGroup(sketch=self)
            group.from_saved(group_dict.get("id"))
            groups.append(group)
        return groups

    def list_aggregations(self, include_labels=None, exclude_labels=None):
        """List all saved aggregations for this sketch.

        Args:
            include_labels (list): list of strings with labels. If defined
                then only return aggregations that have the label in the list.
            exclude_labels (list): list of strings with labels. If defined
                then only return aggregations that don't have a label in the
                list. include_labels will be processed first in case both are
                defined.

        Returns:
            List of aggregations (instances of Aggregation objects)
        """
        if self.is_archived():
            raise RuntimeError("Unable to list aggregations on an archived sketch.")
        aggregations = []

        data = self.api.fetch_resource_data(f"sketches/{self.id}/aggregation/")
        objects = data.get("objects")
        if not objects:
            return aggregations

        if not isinstance(objects, (list, tuple)):
            return aggregations

        object_list = objects[0]
        if not isinstance(object_list, (list, tuple)):
            return aggregations

        for aggregation_dict in object_list:
            agg_id = aggregation_dict.get("id")
            group_id = aggregation_dict.get("aggregationgroup_id")
            if group_id:
                continue
            label_string = aggregation_dict.get("label_string", "")
            if label_string:
                labels = json.loads(label_string)
            else:
                labels = []

            if include_labels:
                if not any(x in include_labels for x in labels):
                    continue

            if exclude_labels:
                if any(x in exclude_labels for x in labels):
                    continue

            aggregation_obj = aggregation.Aggregation(sketch=self)
            aggregation_obj.from_saved(aggregation_id=agg_id)
            aggregations.append(aggregation_obj)
        return aggregations

    def list_graphs(self):
        """Returns a list of stored graphs."""
        if self.is_archived():
            raise RuntimeError("Unable to list graphs on an archived sketch.")

        resource_uri = f"{self.api.api_root}/sketches/{self.id}/graphs/"

        response = self.api.session.get(resource_uri)
        response_json = error.get_response_json(response, logger)
        objects = response_json.get("objects")
        if not objects:
            logger.warning("No graphs discovered.")
            return []

        return_list = []
        graph_list = objects[0]
        for graph_dict in graph_list:
            graph_obj = graph.Graph(sketch=self)
            graph_obj.from_saved(graph_dict.get("id"))
            return_list.append(graph_obj)
        return return_list

    def get_analyzer_status(self, as_sessions=False):
        """Returns a list of started analyzers and their status.

        Args:
            as_sessions (bool): optional, if set to True then a list of
                AnalyzerResult objects will be returned. Defaults to
                returning a list of dicts.
        Returns:
            If "as_sessions" is set then a list of AnalyzerResult gets
            returned, otherwise a list of dict objects that contains
            status information of each analyzer run. The dict contains
            information about what timeline it ran against, the
            results and current status of the analyzer run.
        """
        if self.is_archived():
            raise RuntimeError("Unable to list analyzer status on an archived sketch.")
        stats_list = []
        sessions = []
        for timeline_obj in self.list_timelines():
            resource_uri = ("{0:s}/sketches/{1:d}/timelines/{2:d}/analysis").format(
                self.api.api_root, self.id, timeline_obj.id
            )
            response = self.api.session.get(resource_uri)
            response_json = error.get_response_json(response, logger)
            objects = response_json.get("objects")
            if not objects:
                continue
            for result in objects[0]:
                session_id = result.get("analysissession_id")
                if as_sessions and session_id:
                    sessions.append(
                        analyzer.AnalyzerResult(
                            timeline_id=timeline_obj.id,
                            session_id=session_id,
                            sketch_id=self.id,
                            api=self.api,
                        )
                    )
                status = result.get("status", [])
                if len(status) == 1:
                    result["status"] = status[0].get("status", "N/A")
                stats_list.append(result)

        if as_sessions:
            return sessions

        return stats_list

    def get_aggregation(self, aggregation_id):
        """Return a stored aggregation.

        Args:
            aggregation_id: id of the stored aggregation.

        Returns:
            An aggregation object, if stored (instance of Aggregation),
            otherwise None object.
        """
        if self.is_archived():
            raise RuntimeError("Unable to get aggregations on an archived sketch.")
        for aggregation_obj in self.list_aggregations():
            if aggregation_obj.id == aggregation_id:
                return aggregation_obj
        return None

    def get_aggregation_group(self, group_id):
        """Return a stored aggregation group.

        Args:
            group_id: id of the stored aggregation group.

        Returns:
            An aggregation group object (instance of AggregationGroup)
            if stored, otherwise None object.
        """
        if self.is_archived():
            raise RuntimeError(
                "Unable to get aggregation groups on an archived sketch."
            )

        for group_obj in self.list_aggregation_groups():
            if group_obj.id == group_id:
                return group_obj
        return None

    def get_story(self, story_id=None, story_title=None):
        """Returns a story object that is stored in the sketch.

        Args:
            story_id: an integer indicating the ID of the story to
                be fetched. Defaults to None.
            story_title: a string with the title of the story. Optional
                and defaults to None.

        Returns:
            A story object (instance of Story) if one is found. Returns
            a None if neither story_id or story_title is defined or if
            the view does not exist. If a story title is defined and
            not a story id, the first story that is found with the same
            title will be returned.
        """
        if self.is_archived():
            raise RuntimeError("Unable to get stories on an archived sketch.")

        if story_id is None and story_title is None:
            return None

        for story_obj in self.list_stories():
            if story_id and story_id == story_obj.id:
                return story_obj
            if story_title and story_title.lower() == story_obj.title.lower():
                return story_obj
        return None

    def get_view(self, view_id=None, view_name=None):
        """Returns a saved search object that is stored in the sketch.

        Args:
            view_id: an integer indicating the ID of the saved search to
                be fetched. Defaults to None.
            view_name: a string with the name of the saved search. Optional
                and defaults to None.

        Returns:
            A search object (instance of search.Search) if one is found.
            Returns a None if neither view_id or view_name is defined or if
            the search does not exist.
        """
        logger.warning(
            "This function is about to be deprecated, use "
            "get_saved_search() instead."
        )

        return self.get_saved_search(search_id=view_id, search_name=view_name)

    def get_saved_search(self, search_id=None, search_name=None):
        """Returns a saved search object that is stored in the sketch.

        Args:
            view_id: an integer indicating the ID of the view to
                be fetched. Defaults to None.
            view_name: a string with the name of the view. Optional
                and defaults to None.

        Returns:
            A search object (instance of search.Search) if one is found.
            Returns a None if neither search_id or search_name is defined or if
            the search does not exist.
        """
        if self.is_archived():
            raise RuntimeError("Unable to get saved searches on an archived sketch.")

        if search_id is None and search_name is None:
            return None

        for search_obj in self.list_saved_searches():
            if search_id and search_id == search_obj.id:
                return search_obj
            if search_name and search_name.lower() == search_obj.name.lower():
                return search_obj
        return None

    def get_timeline(self, timeline_id=None, timeline_name=None):
        """Returns a timeline object that is stored in the sketch.

        Args:
            timeline_id: an integer indicating the ID of the timeline to
                be fetched. Defaults to None.
            timeline_name: a string with the name of the timeline. Optional
                and defaults to None.

        Returns:
            A timeline object (instance of Timeline) if one is found. Returns
            a None if neither timeline_id or timeline_name is defined or if
            the timeline does not exist.
        """
        if self.is_archived():
            raise RuntimeError("Unable to get timelines on an archived sketch.")

        if timeline_id is None and timeline_name is None:
            return None

        for timeline_ in self.list_timelines():
            if timeline_id and timeline_id == timeline_.id:
                return timeline_
            if timeline_name:
                if timeline_name.lower() == timeline_.name.lower():
                    return timeline_
        return None

    def get_intelligence_attribute(self):
        """Returns a timeline object that is stored in the sketch.

        Returns:
            A list of dicts with indicators stored in the intelligence
            attribute of the sketch.
        """
        if self.is_archived():
            raise RuntimeError("Unable to get attributes on an archived sketch.")

        intel_attribute = (
            self.attributes.get("intelligence", {}).get("value", {}).get("data", {})
        )

        return intel_attribute

    def list_stories(self):
        """Get a list of all stories that are attached to the sketch.

        Returns:
            List of stories (instances of Story objects)
        """
        if self.is_archived():
            raise RuntimeError("Unable to list stories on an archived sketch.")

        story_list = []
        resource_url = "{0:s}/sketches/{1:d}/stories/".format(
            self.api.api_root, self.id
        )
        response = self.api.session.get(resource_url)
        response_json = error.get_response_json(response, logger)
        story_objects = response_json.get("objects")
        if not story_objects:
            return story_list

        if not len(story_objects) == 1:
            return story_list
        stories = story_objects[0]
        for story_dict in stories:
            story_list.append(
                story.Story(
                    story_id=story_dict.get("id", -1),
                    sketch=self,
                    api=self.api,
                )
            )
        return story_list

    def list_views(self):
        """List all saved views for this sketch.

        Returns:
            List of search object (instance of search.Search).
        """
        logger.warning(
            "This function will soon be deprecated, use list_saved_searches() "
            "instead."
        )
        return self.list_saved_searches()

    def list_saved_searches(self):
        """List all saved searches for this sketch.

        Returns:
            List of search object (instance of search.Search).
        """
        if self.is_archived():
            raise RuntimeError("Unable to list saved searches on an archived sketch.")

        data = self.lazyload_data()
        searches = []
        meta = data.get("meta", {})
        for saved_search in meta.get("views", []):
            search_obj = search.Search(sketch=self)
            try:
                search_obj.from_saved(saved_search.get("id"))
                searches.append(search_obj)
            except ValueError:
                logger.error(
                    "Unable to load a saved search with ID: {0:d}".format(
                        saved_search.get("id", 0)
                    ),
                    exc_info=True,
                )

        return searches

    def list_search_templates(self):
        """Get a list of all search templates that are available.

        Returns:
            List of searchtemplate.SearchTemplate object instances.
        """
        response = self.api.fetch_resource_data("searchtemplates/")
        objects = response.get("objects", [])
        if not objects:
            return []

        template_dicts = objects[0]

        template_list = []
        for template_dict in template_dicts:
            template_obj = searchtemplate.SearchTemplate(api=self.api)
            template_obj.from_saved(template_dict.get("id"), sketch_id=self.id)

            template_list.append(template_obj)

        return template_list

    def list_timelines(self):
        """List all timelines for this sketch.

        Returns:
            List of timelines (instances of Timeline objects)
        """
        if self.is_archived():
            raise RuntimeError("Unable to list timelines on an archived sketch.")

        timelines = []

        data = self.lazyload_data()
        objects = data.get("objects")
        if not objects:
            return timelines

        for timeline_dict in objects[0].get("timelines", []):
            timeline_obj = timeline.Timeline(
                timeline_id=timeline_dict["id"],
                sketch_id=self.id,
                api=self.api,
                name=timeline_dict["name"],
                searchindex=timeline_dict["searchindex"]["index_name"],
            )
            timelines.append(timeline_obj)
        return timelines

    # pylint: disable=unused-argument
    def upload(self, timeline_name, file_path, es_index=None):
        """Deprecated function to upload data, does nothing.

        Args:
            timeline_name: Name of the resulting timeline.
            file_path: Path to the file to be uploaded.
            es_index: Index name for the ES database

        Raises:
            RuntimeError: If this function is used, since it has been
                deprecated in favor of the importer client.
        """
        message = (
            "This function has been deprecated, use the CLI tool: "
            "timesketch_importer: https://github.com/google/timesketch/blob/"
            "master/docs/UploadData.md#using-the-importer-clie-tool or the "
            "importer library: https://github.com/google/timesketch/blob/"
            "master/docs/UploadDataViaAPI.md"
        )
        logger.error(message)
        raise RuntimeError(message)

    # pylint: disable=unused-argument
    def add_timeline(self, searchindex):
        """Deprecated function to add timeline to sketch.

        Args:
            searchindex: SearchIndex object instance.

        Raises:
            RuntimeError: If this function is called.
        """
        message = (
            "This function has been deprecated, since adding already existing "
            "indices to a sketch is no longer supported."
        )

        logger.error(message)
        raise RuntimeError(message)

    def explore(
        self,
        query_string=None,
        query_dsl=None,
        query_filter=None,
        view=None,
        return_fields=None,
        as_pandas=False,
        max_entries=None,
        file_name="",
        as_object=False,
    ):
        """Explore the sketch.

        Args:
            query_string (str): OpenSearch query string.
            query_dsl (str): OpenSearch query DSL as JSON string.
            query_filter (dict): Filter for the query as a dict.
            view: View object instance (optional).
            return_fields (str): A comma separated string with a list of fields
                that should be included in the response. Optional and defaults
                to None.
            as_pandas (bool): Optional bool that determines if the results
                should be returned back as a dictionary or a Pandas DataFrame.
            max_entries (int): Optional integer denoting a best effort to limit
                the output size to the number of events. Events are read in,
                10k at a time so there may be more events in the answer back
                than this number denotes, this is a best effort.
            file_name (str): Optional filename, if provided the results of
                the query will be exported to a ZIP file instead of being
                returned back as a dict or a pandas DataFrame. The ZIP file
                will contain a METADATA file and a CSV with the results from
                the query.
            as_object (bool): Optional bool that determines whether the
                function will return a search object back instead of raw
                results.

        Returns:
            Dictionary with query results, a pandas DataFrame if as_pandas
            is set to True or a search.Search object if as_object is set
            to True. If file_name is provided then no value will be
            returned.

        Raises:
            ValueError: if unable to query for the results.
            RuntimeError: if the query is missing needed values, or if the
                sketch is archived.
        """
        logger.warning(
            "Using this function is discouraged, please consider using "
            "the search.Search object instead, which is more flexible."
        )

        if not (query_string or query_filter or query_dsl or view):
            raise RuntimeError("You need to supply a query or view")

        if self.is_archived():
            raise RuntimeError("Unable to query an archived sketch.")

        search_obj = search.Search(sketch=self)

        if view:
            logger.warning(
                "View objects will be deprecated soon, use search.Search "
                "objects instead."
            )
            search_obj.from_saved(view.id)

        else:
            search_obj.from_manual(
                query_string=query_string,
                query_dsl=query_dsl,
                query_filter=query_filter,
                return_fields=return_fields,
                max_entries=max_entries,
            )
        if as_object:
            return search_obj

        if file_name:
            return search_obj.to_file(file_name)

        if as_pandas:
            return search_obj.to_pandas()

        return search_obj.to_dict()

    def list_available_analyzers(self):
        """Returns a list of available analyzers."""
        resource_url = "{0:s}/sketches/{1:d}/analyzer/".format(
            self.api.api_root, self.id
        )

        response = self.api.session.get(resource_url)

        return error.get_response_json(response, logger)

    def run_analyzer(
        self,
        analyzer_name,
        analyzer_kwargs=None,
        timeline_id=None,
        timeline_name=None,
    ):
        """Run an analyzer on a timeline.

        Args:
            analyzer_name: the name of the analyzer class to run against the
                timeline.
            analyzer_kwargs: optional dict with parameters for the analyzer.
                This is optional and just for those analyzers that can accept
                further parameters.
            timeline_id: the ID of the timeline. This is optional and only
                required if timeline_name is not set.
            timeline_name: the name of the timeline in the timesketch UI. This
                is optional and only required if timeline_id is not set. If
                there are more than a single timeline with the same name a
                timeline_id is required.

        Raises:
            error.UnableToRunAnalyzer: if not able to run the analyzer.

        Returns:
            If the analyzer runs successfully return back an AnalyzerResult
            object.
        """
        # TODO: Deprecate this function.
        logger.warning(
            "This function is about to be deprecated, please use the "
            "`.run_analyzer()` function of a timeline object instead. "
            "This function does not support all functionality of the newer "
            "implementation in the timeline object."
        )

        if self.is_archived():
            raise error.UnableToRunAnalyzer(
                "Unable to run an analyzer on an archived sketch."
            )

        if not timeline_id and not timeline_name:
            return "Unable to run analyzer, need to define either timeline ID or name"

        if timeline_name:
            sketch = self.lazyload_data(refresh_cache=True)
            timelines = []
            for timeline_dict in sketch["objects"][0]["timelines"]:
                name = timeline_dict.get("name", "")
                if timeline_name.lower() == name.lower():
                    timelines.append(timeline_dict.get("id"))

            if not timelines:
                raise error.UnableToRunAnalyzer(
                    "No timelines with the name: {0:s} were found".format(timeline_name)
                )

            if len(timelines) != 1:
                raise error.UnableToRunAnalyzer(
                    "There are {0:d} timelines defined in the sketch with "
                    "this name, please use a unique name or a "
                    "timeline ID".format(len(timelines))
                )

            timeline_id = timelines[0]

        if not timeline_id:
            raise error.UnableToRunAnalyzer(
                "Unable to run an analyzer, not able to find a timeline."
            )

        timeline_obj = timeline.Timeline(
            timeline_id=timeline_id, sketch_id=self.id, api=self.api
        )

        return timeline_obj.run_analyzer(
            analyzer_name=analyzer_name, analyzer_kwargs=analyzer_kwargs
        )

    def remove_acl(
        self,
        user_list=None,
        group_list=None,
        remove_public=False,
        permissions=None,
    ):
        """Remove users or groups to the sketch ACL.

        Args:
            user_list: optional list of users to remove from the ACL
                of the sketch. Each user is a string.
            group_list: optional list of groups to remove from the ACL
                of the sketch. Each user is a string.
            remove_public: Optional boolean indicating the sketch should be
                no longer marked as public.
            permissions: optional list of permissions (read, write, delete).
                If not the default set of permissions are applied (read, write)

        Returns:
            A boolean indicating whether the ACL change was successful.
        """
        if not user_list and not group_list:
            return True

        resource_url = "{0:s}/sketches/{1:d}/collaborators/".format(
            self.api.api_root, self.id
        )

        data = {}
        if group_list:
            group_list_corrected = [str(x).strip() for x in group_list]
            data["remove_groups"] = group_list_corrected

        if user_list:
            user_list_corrected = [str(x).strip() for x in user_list]
            data["remove_users"] = user_list_corrected

        if remove_public:
            data["public"] = "false"

        if permissions:
            allowed_permissions = set(["read", "write", "delete"])
            permissions = list(allowed_permissions.intersection(set(permissions)))
            data["permissions"] = json.dumps(permissions)

        if not data:
            return True

        response = self.api.session.post(resource_url, json=data)
        # Refresh the sketch data to reflect ACL changes.
        _ = self.lazyload_data(refresh_cache=True)
        return error.check_return_status(response, logger)

    def aggregate(self, aggregate_dsl):
        """Run an aggregation request on the sketch.

        Args:
            aggregate_dsl: OpenSearch aggregation query DSL string.

        Returns:
            An aggregation object (instance of Aggregation).

        Raises:
            ValueError: if unable to query for the results.
        """
        if self.is_archived():
            raise ValueError("Unable to run an aggregation on an archived sketch.")

        if not aggregate_dsl:
            raise RuntimeError("You need to supply an aggregation query DSL string.")

        aggregation_obj = aggregation.Aggregation(sketch=self)
        aggregation_obj.from_manual(aggregate_dsl)

        return aggregation_obj

    def list_available_aggregators(self):
        """Return a list of all available aggregators in the sketch."""
        data = self.lazyload_data()
        meta = data.get("meta", {})
        always_supported = [
            {
                "parameter": "index",
                "notes": ("List of indices or timeline IDS to limit the aggregation"),
                "type": "text-input",
            }
        ]

        entries = []
        for name, options in iter(meta.get("aggregators", {}).items()):
            for field in options.get("form_fields", []):
                entry = {
                    "aggregator_name": name,
                    "parameter": field.get("name"),
                    "notes": field.get("label"),
                }
                if field.get("type") == "ts-dynamic-form-select-input":
                    entry["value"] = "|".join(field.get("options", []))
                    entry["type"] = "selection"
                else:
                    _, _, entry["type"] = field.get("type").partition(
                        "ts-dynamic-form-"
                    )
                entries.append(entry)

            for entry_dict in always_supported:
                entry = copy.copy(entry_dict)
                entry["aggregator_name"] = name
                entries.append(entry)

        return pandas.DataFrame(entries)

    def run_aggregator(self, aggregator_name, aggregator_parameters):
        """Run an aggregator class.

        Args:
            aggregator_name: Name of the aggregator to run.
            aggregator_parameters: A dict with key/value pairs of parameters
                the aggregator needs to run.

        Returns:
            An aggregation object (instance of Aggregator).
        """
        if self.is_archived():
            raise RuntimeError("Unable to run an aggregator on an archived sketch.")

        aggregation_obj = aggregation.Aggregation(sketch=self)
        aggregation_obj.from_aggregator_run(
            aggregator_name=aggregator_name,
            aggregator_parameters=aggregator_parameters,
        )

        return aggregation_obj

    def store_aggregation(
        self,
        name,
        description,
        aggregator_name,
        aggregator_parameters,
        chart_type="",
    ):
        """Store an aggregation in the sketch.

        Args:
            name: a name that will be associated with the aggregation.
            description: description of the aggregation, visible in the UI.
            aggregator_name: name of the aggregator class.
            aggregator_parameters: parameters of the aggregator.
            chart_type: string representing the chart type.

        Raises:
            RuntimeError: if the client is unable to store the aggregation.

        Returns:
          A stored aggregation object or None if not stored.
        """
        if self.is_archived():
            raise RuntimeError("Unable to store an aggregator on an archived sketch.")

        # TODO: Deprecate this function.
        logger.warning(
            "This function is about to be deprecated, please use the "
            "`.save()` function of an aggregation object instead"
        )

        aggregator_obj = self.run_aggregator(aggregator_name, aggregator_parameters)
        aggregator_obj.name = name
        aggregator_obj.description = description
        if chart_type:
            aggregator_obj.chart_type = chart_type
        if aggregator_obj.save():
            _ = self.lazyload_data(refresh_cache=True)
            return aggregator_obj

        return None

    def comment_event(self, event_id, index, comment_text):
        """Adds a comment to a single event.

        Args:
            event_id: id of the event
            index: The OpenSearch index name
            comment_text: text to add as a comment
        Returns:
             a json data of the query.
        """
        if self.is_archived():
            raise RuntimeError("Unable to comment on an event in an archived sketch.")

        form_data = {
            "annotation": comment_text,
            "annotation_type": "comment",
            "events": {
                "_id": event_id,
                "_index": index,
                "_type": "generic_event",
            },
        }
        resource_url = "{0:s}/sketches/{1:d}/event/annotate/".format(
            self.api.api_root, self.id
        )
        response = self.api.session.post(resource_url, json=form_data)
        return error.get_response_json(response, logger)

    def add_event_attributes(self, events):
        """Add attributes to one or more events.

        Args:
            events: List of JSON objects representing events. Each event should
              have an 'attributes' key with attributes to be added.
        Returns:
             A dict with the results of adding attributes.
        """
        if self.is_archived():
            raise RuntimeError("Unable to add attributes to an archived sketch.")

        if not isinstance(events, list):
            raise ValueError("Events need to be a list.")

        form_data = {"events": events}
        resource_url = "{0:s}/sketches/{1:d}/event/attributes/".format(
            self.api.api_root, self.id
        )
        response = self.api.session.post(resource_url, json=form_data)

        return error.get_response_json(response, logger)

    def get_event(self, event_id, index_id):
        """Gets information about an event, including raw event and meta data.

        Args:
            event_id: id of the event.
            index_id: The OpenSearch index identifier.

        Returns:
            a json data containing the event details.
        """
        if self.is_archived():
            raise RuntimeError("Unable to retrieve an event in an archived sketch.")

        resource_url_base = "{0:s}/sketches/{1:d}/event/".format(
            self.api.api_root, self.id
        )

        resource_url_params = "?searchindex_id={0:s}&event_id={1:s}".format(
            index_id, event_id
        )

        response = self.api.session.get(resource_url_base + resource_url_params)
        return error.get_response_json(response, logger)

    def label_events(self, events, label_name):
        """Labels one or more events with label_name.

        Args:
            events: Array of JSON objects representing events.
            label_name: String to label the event with.

        Returns:
            Dictionary with query results.
        """
        if self.is_archived():
            raise RuntimeError("Unable to label events in an archived sketch.")

        form_data = {
            "annotation": label_name,
            "annotation_type": "label",
            "events": events,
        }
        resource_url = "{0:s}/sketches/{1:d}/event/annotate/".format(
            self.api.api_root, self.id
        )
        response = self.api.session.post(resource_url, json=form_data)
        return error.get_response_json(response, logger)

    def untag_events(self, events, tags_to_remove: list):
        """Removes a list of tags from a list of events.

        The upper limit is 500 (events or tags) based on the API.

        Args:
            events: events dict. Must have the structure:
                "events": [
                {
                    "_id": event_id,
                    "_index": index,
                }
            tags_to_remove: list of tags to remove

        Returns:
            HTTP response object.
        """
        if self.is_archived():
            raise RuntimeError("Unable to untag events in an archived sketch.")

        form_data = {
            "tags_to_remove": tags_to_remove,
            "events": events,
        }
        resource_url = "{0:s}/sketches/{1:d}/event/untag/".format(
            self.api.api_root, self.id
        )
        response = self.api.session.post(resource_url, json=form_data)
        return error.get_response_json(response, logger)

    def untag_event(self, event_id: str, index, tag: str):
        """Removes a tag from an event.

        This method can be used if just one events needs to be untagged.

        Note if called multiple times in a loop it is more efficient to use
        the untag_events method.

        To remove a list of tags from a list of tags, use a different method.

        Args:
            event_id: id of the event
            index: The OpenSearch index name
            tag: tag to remove

        Returns:
            HTTP response object.
        """
        if self.is_archived():
            raise RuntimeError("Unable to untag events in an archived sketch.")

        form_data = {
            "tags_to_remove": [tag],
            "events": [
                {
                    "_id": event_id,
                    "_index": index,
                }
            ],
        }
        resource_url = "{0:s}/sketches/{1:d}/event/untag/".format(
            self.api.api_root, self.id
        )
        response = self.api.session.post(resource_url, json=form_data)
        return error.get_response_json(response, logger)

    def tag_events(self, events, tags, verbose=False):
        """Tags one or more events with a list of tags.

        Args:
            events: Array of JSON objects representing events.
            tags: List of tags (str) to add to the events.
            verbose: Bool that determines whether extra information
                is added to the meta dict that gets returned.

        Raises:
            ValueError: if tags is not a list of strings.
            RuntimeError: if the sketch is archived.

        Returns:
            A dict with the results from the tagging operation.
        """
        if self.is_archived():
            raise RuntimeError("Unable to tag events in an archived sketch.")

        if not isinstance(tags, list):
            raise ValueError("Tags need to be a list.")

        if not all(isinstance(x, str) for x in tags):
            raise ValueError("Tags need to be a list of strings.")

        form_data = {
            "tag_string": json.dumps(tags),
            "events": events,
            "verbose": verbose,
        }
        resource_url = "{0:s}/sketches/{1:d}/event/tagging/".format(
            self.api.api_root, self.id
        )
        response = self.api.session.post(resource_url, json=form_data)
        status = error.check_return_status(response, logger)
        if not status:
            return {
                "number_of_events": len(events),
                "number_of_events_with_tag": 0,
                "success": status,
            }

        response_json = error.get_response_json(response, logger)
        meta = response_json.get("meta", {})
        meta["total_number_of_events_sent_by_client"] = len(events)
        return meta

    def search_by_label(
        self, label_name, return_fields=None, max_entries=None, as_pandas=False
    ):
        """Searches for all events containing a given label.

        Args:
            label_name: A string representing the label to search for.
            return_fields (str): A comma separated string with a list of fields
                that should be included in the response. Optional and defaults
                to None.
            max_entries (int): Optional integer denoting a best effort to limit
                the output size to the number of events. Events are read in,
                10k at a time so there may be more events in the answer back
                than this number denotes, this is a best effort.
            as_pandas: Optional bool that determines if the results should
                be returned back as a dictionary or a Pandas DataFrame.

        Returns:
            A dictionary with query results.
        """
        if self.is_archived():
            raise RuntimeError("Unable to search for labels in an archived sketch.")

        logger.warning(
            "This function will be deprecated soon. Use the search.Search "
            "object instead and add a search.LabelChip to search for labels."
        )

        query = {
            "nested": {
                "path": "timesketch_label",
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"timesketch_label.name": label_name}},
                            {"term": {"timesketch_label.sketch_id": self.id}},
                        ]
                    }
                },
            }
        }
        return self.explore(
            query_dsl=json.dumps({"query": query}),
            return_fields=return_fields,
            max_entries=max_entries,
            as_pandas=as_pandas,
        )

    def add_scenario(self, uuid=None, dfiq_id=None, name=None):
        """Adds an investigative scenario to the sketch.

        Args:
            uuid (str): [Optional] UUID of the DFIQ scenario template to add.
            dfiq_id (str): [Optional] ID of the DFIQ scenario template to add.
            name (str): [Optional] Name of the scenario to add.

        Raises:
            ValueError: If none or more than one of uuid, dfiq_id, or name are provided.
            ValueError: If a scenario template with the given name is not found.
            RuntimeError: If the sketch is archived.
            RuntimeError: If the scenario cannot be added to the sketch.

        Returns:
            Scenario object.
        """
        if self.is_archived():
            raise RuntimeError("Unable to add a scenario to an archived sketch")

        # Ensure only one argument is provided
        if sum([bool(uuid), bool(dfiq_id), bool(name)]) != 1:
            raise ValueError(
                "Exactly one of 'uuid', 'dfiq_id', or 'name' must be provided."
            )

        form_data = {}
        if uuid:
            form_data["uuid"] = uuid
        elif dfiq_id:
            form_data["template_id"] = dfiq_id
        else:  # name is provided
            scenario_templates = scenario_lib.getScenarioTemplateList(self.api)
            for template in scenario_templates:
                if template.get("name") == name:
                    form_data["uuid"] = template.get("uuid")
                    break
            else:
                raise ValueError(f"No DFIQ scenario template found with name '{name}'")

        resource_url = f"{self.api.api_root}/sketches/{self.id}/scenarios/"
        response = self.api.session.post(resource_url, json=form_data)
        response_json = error.get_response_json(response, logger)

        scenario_objects = response_json.get("objects", [])
        if len(scenario_objects) != 1:
            raise RuntimeError(
                f"Failed to add scenario to sketch {self.id}. "
                f"Unexpected response: {response_json}"
            )

        scenario_data = scenario_objects[0]
        return scenario_lib.Scenario(
            uuid=scenario_data.get("uuid", -1),
            scenario_id=scenario_data.get("id", -1),
            sketch_id=self.id,
            api=self.api,
        )

    def list_scenarios(self):
        """Get a list of all scenarios that are attached to the sketch.

        Returns:
            List of scenarios (instances of Scenario objects)
        """
        if self.is_archived():
            raise RuntimeError("Unable to list scenarios on an archived sketch.")

        resource_url = f"{self.api.api_root}/sketches/{self.id}/scenarios/"
        response = self.api.session.get(resource_url)
        response_json = error.get_response_json(response, logger)

        scenario_objects = response_json.get("objects", [])
        # Check if it's a nested list or a single list
        if scenario_objects and isinstance(scenario_objects[0], list):
            scenario_objects = scenario_objects[0]

        return [
            scenario_lib.Scenario(
                uuid=scenario_data.get("uuid"),
                scenario_id=scenario_data.get("id"),
                sketch_id=self.id,
                api=self.api,
            )
            for scenario_data in scenario_objects
        ]

    def add_question(self, dfiq_id=None, uuid=None, question_text=None):
        """Adds an investigative question to the sketch.

        Args:
            dfiq_id (str): [Optional] ID of the DFIQ question template to add.
            uuid (str): [Optional] UUID of the DFIQ question template to add.
            question_text (str): [Optional] Question text to add.

        Raises:
            ValueError: If none or more than one of dfiq_id, uuid, or
                        question_text are provided.
            RuntimeError: If the sketch is archived.
            RuntimeError: If the question cannot be added to the sketch.

        Returns:
            Question object.
        """
        if self.is_archived():
            raise RuntimeError("Unable to add a question to an archived sketch!")

        # Ensure only one argument is provided
        if sum([bool(dfiq_id), bool(uuid), bool(question_text)]) != 1:
            raise ValueError(
                "Exactly one of 'dfiq_id', 'uuid', or 'question_text' must be "
                "provided."
            )

        form_data = {}
        if dfiq_id:
            form_data["template_id"] = dfiq_id
        elif uuid:
            form_data["uuid"] = uuid
        else:  # question_text is provided
            question_templates = scenario_lib.getQuestionTemplateList(self.api)
            for template in question_templates:
                if template.get("name") == question_text:
                    form_data["uuid"] = template.get("uuid")
                    break
            else:
                form_data["question_text"] = question_text

        resource_url = f"{self.api.api_root}/sketches/{self.id}/questions/"
        response = self.api.session.post(resource_url, json=form_data)
        response_json = error.get_response_json(response, logger)

        question_objects = response_json.get("objects", [])
        if len(question_objects) != 1:
            raise RuntimeError(
                f"Failed to add question to sketch {self.id}. "
                f"Unexpected response: {response_json}"
            )

        question_data = question_objects[0]
        return scenario_lib.Question(
            question_id=question_data.get("id"),
            uuid=question_data.get("uuid"),
            sketch_id=self.id,
            api=self.api,
        )

    def list_questions(self):
        """Get a list of all questions attached to the sketch.

        Returns:
            List of Question objects. An empty list is returned if no questions
            are found or if the sketch is archived.
        """
        if self.is_archived():
            raise RuntimeError("Unable to list a question of an archived sketch!")

        resource_url = f"{self.api.api_root}/sketches/{self.id}/questions/"
        response = self.api.session.get(resource_url)
        response_json = error.get_response_json(response, logger)

        question_objects = response_json.get("objects", [])
        # Check if it's a nested list or a single list
        if question_objects and isinstance(question_objects[0], list):
            question_objects = question_objects[0]

        return [
            scenario_lib.Question(
                question_id=question_data.get("id"),
                uuid=question_data.get("uuid"),
                sketch_id=self.id,
                api=self.api,
            )
            for question_data in question_objects
        ]

    def add_event(self, message, date, timestamp_desc, attributes=None, tags=None):
        """Adds an event to the sketch specific timeline.

        Args:
            message: A string that will be used as the message string.
            date: A string with the timestamp of the message. This should be
                in a human readable format, eg: "2020-09-03T22:52:21".
            timestamp_desc : Description of the timestamp.
            attributes: A dict of extra attributes to add to the event.
            tags: A list of strings to include as tags.

        Raises:
            ValueError: If tags is not a list of strings or attributes
                is not a dict.

        Returns:
            Dictionary with query results.
        """
        if self.is_archived():
            raise RuntimeError("Unable to add an event to an archived sketch.")

        if tags is None:
            tags = []

        if not isinstance(tags, list):
            raise ValueError("Tags needs to be a list.")

        if any(not isinstance(tag, str) for tag in tags):
            raise ValueError("Tags needs to be a list of strings.")

        if attributes is None:
            attributes = {}

        if not isinstance(attributes, dict):
            raise ValueError("Attributes needs to be a dict.")

        form_data = {
            "date_string": date,
            "timestamp_desc": timestamp_desc,
            "message": message,
            "tag": tags,
        }

        duplicate_attributes = [key for key in attributes if key in form_data]

        if duplicate_attributes:
            duplicates = ", ".join(duplicate_attributes)
            raise ValueError(
                f"Following attributes cannot overwrite values "
                f"already set: {duplicates}"
            )

        form_data["attributes"] = attributes

        resource_url = "{0:s}/sketches/{1:d}/event/create/".format(
            self.api.api_root, self.id
        )
        response = self.api.session.post(resource_url, json=form_data)
        return error.get_response_json(response, logger)

    def is_archived(self):
        """Return a boolean indicating whether the sketch has been archived."""
        if self._archived is not None:
            return self._archived

        resource_url = "{0:s}/sketches/{1:d}/archive/".format(
            self.api.api_root, self.id
        )
        response = self.api.session.get(resource_url)
        data = error.get_response_json(response, logger)
        meta = data.get("meta", {})
        self._archived = meta.get("is_archived", False)
        return self._archived

    def archive(self):
        """Archive a sketch and return a boolean whether it was successful."""
        if self.is_archived():
            logger.error("Sketch already archived.")
            return False

        resource_url = "{0:s}/sketches/{1:d}/archive/".format(
            self.api.api_root, self.id
        )
        data = {"action": "archive"}
        response = self.api.session.post(resource_url, json=data)
        return_status = error.check_return_status(response, logger)
        self._archived = return_status

        return return_status

    def unarchive(self):
        """Unarchives a sketch and return boolean whether it was successful."""
        if not self.is_archived():
            logger.error("Sketch wasn't archived.")
            return False

        resource_url = "{0:s}/sketches/{1:d}/archive/".format(
            self.api.api_root, self.id
        )
        data = {"action": "unarchive"}
        response = self.api.session.post(resource_url, json=data)
        return_status = error.check_return_status(response, logger)

        # return_status = True means unarchive is successful or that
        # the archive status is False.
        self._archived = not return_status
        return return_status

    def export(self, file_path):
        """Exports the content of the sketch to a ZIP file.

        Args:
            file_path (str): a file path where the ZIP file will be saved.

        Raises:
            RuntimeError: if sketch cannot be exported.
        """
        directory = os.path.dirname(file_path)
        if not os.path.isdir(directory):
            raise RuntimeError(
                "The directory needs to exist, please create: "
                "{0:s} first".format(directory)
            )

        if not file_path.lower().endswith(".zip"):
            logger.warning("File does not end with a .zip, adding it.")
            file_path = "{0:s}.zip".format(file_path)

        if os.path.isfile(file_path):
            raise RuntimeError("File [{0:s}] already exists.".format(file_path))

        form_data = {"action": "export"}
        resource_url = "{0:s}/sketches/{1:d}/archive/".format(
            self.api.api_root, self.id
        )

        response = self.api.session.post(resource_url, json=form_data)
        status = error.check_return_status(response, logger)
        if not status:
            error.error_message(
                response,
                message="Failed exporting the sketch",
                error=RuntimeError,
            )

        with open(file_path, "wb") as fw:
            fw.write(response.content)

    def generate_timeline_from_es_index(
        self,
        es_index_name,
        name,
        index_name="",
        description="",
        provider="Manually added to OpenSearch",
        context="Added via API client",
        data_label="OpenSearch",
        status="ready",
    ):
        """Creates and returns a Timeline from OpenSearch data.

        This function can be used to import data into a sketch that was
        ingested via different mechanism, such as ELK, etc.

        The function creates the necessary structures (SearchIndex and a
        Timeline) for Timesketch to be able to properly support it.

        Args:
            es_index_name: name of the index in OpenSearch.
            name: string with the name of the timeline.
            index_name: optional string for the SearchIndex name, defaults
                to the same as the es_index_name.
            description: optional string with a description of the timeline.
            provider: optional string with the provider name for the data
                source of the imported data. Defaults to "Manually added
                to OpenSearch".
            context: optional string with the context for the data upload,
                defaults to "Added via API client".
            data_label: optional string with the data label of the OpenSearch
                data, defaults to "OpenSearch".
            status: Optional string, if provided will be used as a status
                for the searchindex, valid options are: "ready", "fail",
                "processing", "timeout". Defaults to "ready".

        Raises:
            ValueError: If there are errors in the generation of the
            timeline.

        Returns:
            Instance of a Timeline object.
        """
        if not es_index_name:
            raise ValueError("ES index needs to be provided.")

        if not name:
            raise ValueError("Timeline name needs to be provided.")

        # Step 1: Make sure the index doesn't exist already.
        for index_obj in self.api.list_searchindices():
            if index_obj is None:
                continue
            if index_obj.index_name == es_index_name:
                raise ValueError("Unable to add the ES index, since it already exists.")

        # Step 2: Create a SearchIndex.
        resource_url = f"{self.api.api_root}/searchindices/"
        form_data = {
            "searchindex_name": index_name or es_index_name,
            "es_index_name": es_index_name,
        }
        response = self.api.session.post(resource_url, json=form_data)

        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            error.error_message(
                response,
                message="Error creating searchindex",
                error=ValueError,
            )

        response_dict = error.get_response_json(response, logger)
        objects = response_dict.get("objects")
        if not objects:
            raise ValueError(
                "Unable to create a SearchIndex, try again or file an "
                "issue on GitHub."
            )

        searchindex_id = objects[0].get("id")

        # Step 3: Verify mappings to make sure data conforms.
        index_obj = api_index.SearchIndex(searchindex_id, api=self.api)
        index_fields = set(index_obj.fields)

        if not self._NECESSARY_DATA_FIELDS.issubset(index_fields):
            index_obj.status = "fail"
            raise ValueError(
                "Unable to ingest data since it is missing required "
                "fields: {0:s} [ingested data contains these fields: "
                "{1:s}]".format(
                    ", ".join(self._NECESSARY_DATA_FIELDS.difference(index_fields)),
                    "|".join(index_fields),
                )
            )

        if status:
            index_obj.status = status

        # Step 4: Create the Timeline.
        resource_url = f"{self.api.api_root}/sketches/{self.id}/timelines/"
        form_data = {"timeline": searchindex_id, "timeline_name": name}
        response = self.api.session.post(resource_url, json=form_data)

        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            error.error_message(
                response,
                message="Error creating a timeline object",
                error=ValueError,
            )

        response_dict = error.get_response_json(response, logger)
        objects = response_dict.get("objects")
        if not objects:
            raise ValueError(
                "Unable to create a Timeline, try again or file an issue on GitHub."
            )

        timeline_dict = objects[0]

        timeline_obj = timeline.Timeline(
            timeline_id=timeline_dict["id"],
            sketch_id=self.id,
            api=self.api,
            name=timeline_dict["name"],
            searchindex=timeline_dict["searchindex"]["index_name"],
        )

        # Step 5: Add the timeline ID into the dataset.
        resource_url = f"{self.api.api_root}/sketches/{self.id}/event/add_timeline_id/"
        form_data = {
            "searchindex_id": searchindex_id,
            "timeline_id": timeline_dict["id"],
        }
        response = self.api.session.post(resource_url, json=form_data)

        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            error.error_message(
                response,
                message="Unable to add timeline identifier to data",
                error=ValueError,
            )

        # Step 6: Add a DataSource object.
        resource_url = f"{self.api.api_root}/sketches/{self.id}/datasource/"
        form_data = {
            "timeline_id": timeline_dict["id"],
            "provider": provider,
            "context": context,
            "data_label": data_label,
        }
        response = self.api.session.post(resource_url, json=form_data)
        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            error.error_message(
                response,
                message="Error creating a datasource object",
                error=ValueError,
            )

        _ = error.get_response_json(response, logger)

        return timeline_obj

    def run_data_finder(self, start_date, end_date, rule_names, timelines=None):
        """Runs the data finder .

        Args:
            start_date (str): Start date as a ISO 8601 formatted string.
            end_date (str): End date as a ISO 8601 formatted string.
            rule_names (list): A list of strings with rule names to run
                against the dataset in the sketch.
            timelines (list): Optional list of timeline identifiers or
                timeline names to limit the data search to certain
                timelines within the sketch. Defaults to search all
                timelines.

        Returns:
            A list of dictionaries, one dict for each rule that was run,
            alongside it's results.
        """
        if timelines is None:
            timeline_ids = [t.id for t in self.list_timelines()]
        else:
            timeline_ids = []
            valid_ids = set()
            name_to_id = {}
            for _timeline in self.list_timelines():
                valid_ids.add(_timeline.id)
                name_to_id[_timeline.name.lower()] = _timeline.id

            for _timeline in timelines:
                if isinstance(_timeline, int) and _timeline in valid_ids:
                    timeline_ids.append(_timeline)
                    continue

                if not isinstance(_timeline, str):
                    logger.error(
                        "Unable to use timeline, it needs to either be "
                        "a string or an integer."
                    )
                    continue

                if _timeline.lower() not in name_to_id:
                    logger.error(
                        "Unable to add timeline, name not found in active "
                        "timelines in the sketch."
                    )
                    continue
                timeline_ids.append(name_to_id[_timeline.lower()])

        data = {
            "start_date": start_date,
            "end_date": end_date,
            "timeline_ids": timeline_ids,
            "rule_names": rule_names,
        }
        resource_url = f"{self.api.api_root}/sketches/{self.id}/data/find/"
        response = self.api.session.post(resource_url, json=data)

        if response.status_code not in definitions.HTTP_STATUS_CODE_20X:
            error.error_message(
                response, message="Unable to find data", error=ValueError
            )

        response_dict = error.get_response_json(response, logger)

        return response_dict.get("objects", [])
