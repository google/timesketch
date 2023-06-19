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
import datetime
import getpass
import json
import logging

import altair
import pandas

from . import error
from . import resource


logger = logging.getLogger("timesketch_api.aggregation")


class Aggregation(resource.SketchResource):
    """Aggregation object.

    Attributes:
        aggregator_name: name of the aggregator class used to
            generate the aggregation.
        chart_color: the color of the chart.
        chart_type: the type of chart that will be generated
            from this aggregation object.
        type: the type of aggregation object.
        search_id: a search ID if the aggregation is tied to a specific
            saved search.
    """

    def __init__(self, sketch):
        self._created_at = ""
        self._name = ""
        self._parameters = {}
        self._updated_at = ""
        self._group_id = None
        self._aggregator_name = ""
        self.chart_color = ""
        self.chart_type = ""
        self.chart_title = ""
        self.search_id = None
        self.type = None
        resource_uri = "sketches/{0:d}/aggregation/explore/".format(sketch.id)
        super().__init__(sketch=sketch, resource_uri=resource_uri)

    @property
    def created_at(self):
        """Returns a timestamp when the aggregation was created."""
        return self._created_at

    def _get_aggregation_buckets(self, entry, name=""):
        """Yields all buckets from an aggregation result object.

        Args:
            entry: result dict from an aggregation request.
            name: name of aggregation results that contains
                all aggregation buckets.

        Yields:
            A dict with each aggregation bucket as well as
            the bucket_name.
        """
        if "buckets" in entry:
            for bucket in entry.get("buckets", []):
                bucket["bucket_name"] = name
                yield bucket
        else:
            for key, value in iter(entry.items()):
                if not isinstance(value, dict):
                    continue
                for bucket in self._get_aggregation_buckets(value, name=key):
                    yield bucket

    def _run_aggregator(
        self, aggregator_name, parameters, search_id=None, chart_type=None
    ):
        """Run an aggregator class.

        Args:
            aggregator_name: the name of the aggregator class.
            parameters: a dict with the parameters for the aggregation class.
            search_id: an optional integer value with a primary key to a
                saved search.
            chart_type: string with the chart type.

        Returns:
            A dict with the aggregation results.
        """
        resource_url = "{0:s}/sketches/{1:d}/aggregation/explore/".format(
            self.api.api_root, self._sketch.id
        )

        if chart_type is None and parameters.get("supported_charts"):
            chart_type = parameters.get("supported_charts")
            if isinstance(chart_type, (list, tuple)):
                chart_type = chart_type[0]

        if chart_type:
            self.chart_type = chart_type

        if search_id:
            self.search_id = search_id

        self._aggregator_name = aggregator_name
        self.chart_color = parameters.get("chart_color", "")
        self._parameters = parameters

        form_data = {
            "aggregator_name": aggregator_name,
            "aggregator_parameters": parameters,
            "chart_type": chart_type,
            "view_id": search_id,
        }

        response = self.api.session.post(resource_url, json=form_data)
        if not error.check_return_status(response, logger):
            error.error_message(
                response, message="Unable to query results", error=ValueError
            )

        return error.get_response_json(response, logger)

    # pylint: disable=arguments-differ
    def from_saved(self, aggregation_id):
        """Initialize the aggregation object from a saved aggregation.

        Args:
            aggregation_id: integer value for the stored
                aggregation (primary key).
        """
        resource_uri = "sketches/{0:d}/aggregation/{1:d}/".format(
            self._sketch.id, aggregation_id
        )
        self._resource_id = aggregation_id
        resource_data = self.api.fetch_resource_data(resource_uri)
        data = resource_data.get("objects", [None])[0]
        if not data:
            return

        self._aggregator_name = data.get("agg_type")
        self.type = "stored"

        self._name = data.get("name", "")
        self._created_at = data.get("created_at", "")
        self._updated_at = data.get("updated_at", "")
        self._group_id = data.get("aggregationgroup_id")

        label_string = data.get("label_string", "")
        if label_string:
            self._labels = json.loads(label_string)
        else:
            self._labels = []

        chart_type = data.get("chart_type")
        param_string = data.get("parameters", "")
        if param_string:
            parameters = json.loads(param_string)
        else:
            parameters = {}

        self._parameters = parameters

        self._username = data.get("user", {}).get("username", "System")
        self.resource_data = self._run_aggregator(
            aggregator_name=self._aggregator_name,
            parameters=parameters,
            chart_type=chart_type,
        )

    # pylint: disable=arguments-differ
    def from_manual(self, aggregate_dsl, **kwargs):
        """Initialize the aggregation object by running an aggregation DSL.

        Args:
            aggregate_dsl: OpenSearch aggregation query DSL string.
        """
        super().from_manual(**kwargs)
        resource_url = "{0:s}/sketches/{1:d}/aggregation/explore/".format(
            self.api.api_root, self._sketch.id
        )

        self._aggregator_name = "DSL"
        self._username = getpass.getuser()
        self.type = "DSL"

        date_now = datetime.datetime.now(datetime.timezone.utc)
        self._created_at = date_now.isoformat()
        self._updated_at = date_now.isoformat()

        form_data = {
            "aggregation_dsl": aggregate_dsl,
        }

        response = self.api.session.post(resource_url, json=form_data)
        if not error.check_return_status(response, logger):
            error.error_message(
                response, message="Unable to query results", error=ValueError
            )

        self.resource_data = error.get_response_json(response, logger)

    def from_aggregator_run(
        self,
        aggregator_name,
        aggregator_parameters,
        search_id=None,
        chart_type=None,
    ):
        """Initialize the aggregation object by running an aggregator class.

        Args:
            aggregator_name: name of the aggregator class to run.
            aggregator_parameters: a dict with the parameters of the aggregator
                class.
            search_id: an optional integer value with a primary key to a saved
                search.
            chart_type: optional string with the chart type.
        """
        self.type = "aggregator_run"
        self._parameters = aggregator_parameters
        self._username = getpass.getuser()

        date_now = datetime.datetime.now(datetime.timezone.utc)
        self._created_at = date_now.isoformat()
        self._updated_at = date_now.isoformat()

        self.resource_data = self._run_aggregator(
            aggregator_name, aggregator_parameters, search_id, chart_type
        )

    def lazyload_data(self, refresh_cache=False):
        """Load resource data once and cache the result.

        Args:
            refresh_cache: Boolean indicating if to update cache.

        Returns:
            Dictionary with resource data.
        """
        if self.resource_data and not refresh_cache:
            return self.resource_data

        # TODO: Implement a method to refresh cache.
        return self.resource_data

    @property
    def parameters(self):
        """Property that returns the parameters of the aggregation."""
        return self._parameters

    @property
    def is_part_of_group(self):
        """Property that returns whether an agg is part of a group or not."""
        if self._group_id is None:
            return False

        return bool(self._group_id)

    @property
    def title(self):
        """Property that returns the chart title of an aggregation."""
        if self.chart_title:
            return self.chart_title

        data = self.lazyload_data()
        if not data:
            return ""
        meta = data.get("meta", {})
        self.chart_title = meta.get("vega_chart_title", "")

        return self.chart_title

    @title.setter
    def title(self, new_title):
        """Set the chart title of an aggregation."""
        self.chart_title = new_title

    @property
    def chart(self):
        """Property that returns an altair Vega-lite chart."""
        return self.generate_chart()

    @property
    def description(self):
        """Property that returns the description string."""
        data = self.lazyload_data()
        if not data:
            return ""
        meta = data.get("meta", {})
        return meta.get("description", "")

    @description.setter
    def description(self, description):
        """Set the description of an aggregation."""
        if "meta" not in self.resource_data:
            return
        meta = self.resource_data.get("meta")
        meta["description"] = description

    @property
    def name(self):
        """Property that returns the name of the aggregation."""
        return self._name

    @name.setter
    def name(self, name):
        """Set the name of the aggregation."""
        if "meta" not in self.resource_data:
            return
        meta = self.resource_data.get("meta")
        meta["name"] = name

    @property
    def aggregator_name(self):
        """Property that returns the aggregator name."""
        if self._aggregator_name:
            return self._aggregator_name

        data = self.resource_data
        meta = data.get("meta", {})
        self._aggregator_name = meta.get("name")

        return self._aggregator_name

    def add_label(self, label):
        """Add a label to the aggregation.

        Args:
            label (str): string with the label information.
        """
        if label in self._labels:
            return
        self._labels.append(label)
        self.save()

    def to_dict(self):
        """Returns a dict."""
        entries = {}
        entry_index = 1
        data = self.lazyload_data()
        for entry in data.get("objects", []):
            for bucket in self._get_aggregation_buckets(entry):
                entries["entry_{0:d}".format(entry_index)] = bucket
                entry_index += 1
        return entries

    def to_pandas(self):
        """Returns a pandas DataFrame."""
        panda_list = []
        data = self.lazyload_data()
        for entry in data.get("objects", []):
            for bucket in self._get_aggregation_buckets(entry):
                panda_list.append(bucket)
        return pandas.DataFrame(panda_list)

    @property
    def updated_at(self):
        """Returns a timestamp when the aggregation was last updated."""
        return self._updated_at

    def generate_chart(self):
        """Returns an altair Vega-lite chart."""
        if not self.chart_type:
            raise TypeError("Unable to generate chart, missing a chart type.")

        if not self._parameters.get("supported_charts"):
            self._parameters["supported_charts"] = self.chart_type

        data = self.lazyload_data()
        meta = data.get("meta", {})
        vega_spec = meta.get("vega_spec")

        if not vega_spec:
            return altair.Chart(pandas.DataFrame()).mark_point()

        vega_spec_string = json.dumps(vega_spec)
        return altair.Chart.from_json(vega_spec_string)

    def save(self):
        """Save the aggregation in the database."""
        data = {
            "name": self.name,
            "description": self.description,
            "agg_type": self._aggregator_name,
            "parameters": self._parameters,
            "chart_type": self.chart_type,
        }
        if self.search_id:
            data["view_id"] = self.search_id
        if self._labels:
            data["labels"] = json.dumps(self._labels)

        if self._resource_id:
            resource_url = "{0:s}/sketches/{1:d}/aggregation/{2:d}/".format(
                self.api.api_root, self._sketch.id, self._resource_id
            )
        else:
            resource_url = "{0:s}/sketches/{1:d}/aggregation/".format(
                self.api.api_root, self._sketch.id
            )

        response = self.api.session.post(resource_url, json=data)
        if not error.check_return_status(response, logger):
            return "Unable to save the aggregation"

        response_json = response.json()
        objects = response_json.get("objects")
        if not objects:
            return "Unable to determine ID of saved object."
        agg_data = objects[0]
        self._resource_id = agg_data.get("id", 0)
        return "Saved aggregation to ID: {0:d}".format(self._resource_id)

    def delete(self):
        """Deletes the aggregation from the store."""
        if not self._resource_id:
            logger.warning(
                "Unable to delete the aggregation, it does not appear to be "
                "saved in the first place."
            )
            return False

        resource_uri = "{0:s}/sketches/{1:d}/aggregation/{2:d}/".format(
            self.api.api_root, self._sketch.id, self._resource_id
        )
        response = self.api.session.delete(resource_uri)
        return error.check_return_status(response, logger)


class AggregationGroup(resource.SketchResource):
    """Aggregation Group object."""

    def __init__(self, sketch):
        """Initialize the aggregation group."""
        resource_uri = "sketches/{0:d}/aggregation/group/".format(sketch.id)
        super().__init__(resource_uri=resource_uri, sketch=sketch)

        self._name = "N/A"
        self._created_at = ""
        self._description = "N/A"
        self._orientation = ""
        self._parameters = {}
        self._aggregations = []
        self._updated_at = ""

    def __str__(self):
        """Return a string representation of the group."""
        return "[{0:d}] {1:s} - {2:s}".format(
            self._resource_id, self._name, self._description
        )

    @property
    def aggregations(self):
        """Property that returns a list of aggregations in the group."""
        return self._aggregations

    @property
    def created_at(self):
        """Returns a timestamp when the aggregation group was created."""
        return self._created_at

    @property
    def updated_at(self):
        """Returns a timestamp when the aggregation group was updated."""
        return self._updated_at

    def to_dict(self):
        """Returns the aggregation values as a dict."""
        data_frame = self.to_pandas()
        return data_frame.to_dict(orient="records")

    @property
    def chart(self):
        """Property that returns an altair Vega-lite chart."""
        if not self._aggregations:
            return altair.Chart()
        return self.generate_chart()

    @property
    def description(self):
        """Returns the description of the aggregation group."""
        return self._description

    @description.setter
    def description(self, description):
        """Sets the description of the aggregation group."""
        self._description = description
        self.save()

    @property
    def name(self):
        """Returns the name of the aggregation group."""
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of the aggregation group."""
        self._name = name
        self.save()

    @property
    def orientation(self):
        """Returns the chart orientation."""
        return self._orientation

    @orientation.setter
    def orientation(self, orientation):
        """Sets the chart orientation."""
        self._orientation = orientation
        self.save()

    @property
    def parameters(self):
        """Returns a dict with the group parameters."""
        return self._parameters

    @parameters.setter
    def parameters(self, parameters):
        """Sets the group parameters."""
        self._parameters = parameters
        self.save()

    def delete(self):
        """Deletes the group from the store."""
        if not self._resource_id:
            logger.warning(
                "Unable to delete the group, it does not appear to be saved "
                "in the first place."
            )
            return False

        resource_uri = "{0:s}/sketches/{1:d}/aggregation/group/{2:d}/".format(
            self.api.api_root, self._sketch.id, self._resource_id
        )
        response = self.api.session.delete(resource_uri)
        return error.check_return_status(response, logger)

    def from_dict(self, group_dict):
        """Feed group data from a dictionary.

        Args:
            group_dict (dict): a dictionary with the aggregation group
                information.

        Raises:
            TypeError: if the dictionary does not contain the correct
                information.
        """
        group_id = group_dict.get("id")
        if not group_id:
            raise TypeError("Group ID is missing.")
        self._resource_id = group_id
        self.resource_uri = "sketches/{0:d}/aggregation/group/{1:d}/".format(
            self._sketch.id, group_id
        )

        self._name = group_dict.get("name", "")
        self._description = group_dict.get("description", "")

        self._created_at = group_dict.get("created_at", "")
        self._updated_at = group_dict.get("updated_at", "")

        self._orientation = group_dict.get("orientation")
        if not self._orientation:
            raise TypeError("How a group is connected needs to be defined.")

        parameter_string = group_dict.get("parameters", "")
        if parameter_string:
            self._parameters = json.loads(parameter_string)

        aggs = group_dict.get("agg_ids")
        if not aggs:
            raise TypeError("Group contains no aggregations")

        if isinstance(aggs, str):
            aggs = json.loads(aggs)

        if not isinstance(aggs, (list, tuple)):
            raise TypeError("Aggregations need to be a list.")

        self._aggregations = []
        for agg_id in aggs:
            agg_obj = Aggregation(self._sketch)
            agg_obj.from_saved(agg_id)
            self._aggregations.append(agg_obj)

    # pylint: disable=arguments-differ
    def from_saved(self, group_id):
        """Feed group data from a group ID.

        Args:
            group_id (int): the group ID to fetch from the store.

        Raises:
            TypeError: if the group ID does not exist.
        """
        self._resource_id = group_id
        resource_uri = f"sketches/{self._sketch.id}/aggregation/group/{group_id}/"
        resource_data = self.api.fetch_resource_data(resource_uri)

        objects = resource_data.get("objects")
        if not objects:
            raise TypeError("Group ID not found.")

        group_dict = objects[0]
        group_dict["id"] = group_id
        self.from_dict(group_dict)

    def generate_chart(self):
        """Returns an altair Vega-lite chart."""
        if not self._aggregations:
            return altair.Chart()

        data = self.lazyload_data()
        if not data:
            return None

        meta = data.get("meta", {})
        vega_spec = meta.get("vega_spec")

        if not vega_spec:
            return altair.Chart(pandas.DataFrame()).mark_point()

        vega_spec_string = json.dumps(vega_spec)
        return altair.Chart.from_json(vega_spec_string)

    def get_charts(self):
        """Returns a list of altair Chart objects from each aggregation."""
        return [x.chart for x in self._aggregations]

    def get_tables(self):
        """Returns a list of pandas DataFrame from each aggregation."""
        return [x.table for x in self._aggregations]

    def save(self):
        """Save the aggregation group in the database."""
        if not self._aggregations:
            return False

        data = {
            "name": self._name,
            "description": self._description,
            "parameters": json.dumps(self._parameters),
            "aggregations": json.dumps([x.id for x in self._aggregations]),
            "orientation": self._orientation,
        }

        if self._resource_id:
            res_url = "{0:s}/sketches/{1:d}/aggregation/group/{2:d}/".format(
                self.api.api_root, self._sketch.id, self._resource_id
            )
        else:
            res_url = "{0:s}/sketches/{1:d}/aggregation/group/".format(
                self.api.api_root, self._sketch.id
            )

        response = self.api.session.post(res_url, json=data)
        _ = self.lazyload_data(refresh_cache=True)
        return error.check_return_status(response, logger)

    def to_pandas(self):
        """Returns a pandas DataFrame.

        Aggregation groups are meant for charts, not data frames. However
        there are situations where you may want to be able to produce
        a DataFrame, and in that case all DataFrame objects from each
        aggregation are concatenated to return a single one.

        Returns:
            A single DataFrame that consists of a DataFrame from each
            aggregation in the group concatenated.
        """
        if not self._aggregations:
            return pandas.DataFrame()

        data_frames = []
        for agg_obj in self._aggregations:
            data_frames.append(agg_obj.to_pandas())

        return pandas.concat(data_frames)
