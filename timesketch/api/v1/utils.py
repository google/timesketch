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
"""This module holds utility functions for the version 1 of the API."""
import logging
import json
import time
import os
import pathlib
import re
import yaml

from flask import abort
from flask import jsonify
from flask import current_app
from flask_login import current_user


import altair as alt
import pandas as pd

from timesketch.lib import ontology
from timesketch.lib.aggregators import manager as aggregator_manager
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.models import db_session
from timesketch.models.sketch import View


logger = logging.getLogger("timesketch.api_utils")


def bad_request(message):
    """Function to set custom error message for HTTP 400 requests.

    Args:
        message: Message as string to return to the client.

    Returns: Response object (instance of flask.wrappers.Response)

    """
    response = jsonify({"message": message})
    response.status_code = HTTP_STATUS_CODE_BAD_REQUEST
    return response


def get_sketch_attributes(sketch):
    """Returns a dict with all attributes of a sketch."""
    attributes = {}
    ontology_def = ontology.ONTOLOGY
    for attribute in sketch.attributes:
        if attribute.sketch_id != sketch.id:
            continue
        name = attribute.name
        attribute_values = []
        ontology_string = attribute.ontology
        ontology_dict = ontology_def.get(ontology_string, {})
        cast_as_str = ontology_dict.get("cast_as", "str")

        for attr_value in attribute.values:
            try:
                value = ontology.OntologyManager.decode_value(
                    attr_value.value, cast_as_str
                )
            except ValueError:
                value = "Unable to cast"
            except NotImplementedError:
                value = f"Ontology {cast_as_str} not yet defined."

            attribute_values.append(value)

        values = attribute_values
        if len(attribute_values) == 1:
            values = attribute_values[0]

        attributes[name] = {
            "value": values,
            "ontology": ontology_string,
        }
    return attributes


def get_sketch_last_activity(sketch):
    """Returns a date string with the last activity from a sketch."""
    try:
        last_activity = (
            View.query.filter_by(sketch=sketch, name="")
            .order_by(View.updated_at.desc())
            .first()
            .updated_at
        )
    except AttributeError:
        return ""
    return last_activity.isoformat()


def update_sketch_last_activity(sketch):
    """Update the last activity date of a sketch."""
    view = View.get_or_create(user=current_user, sketch=sketch, name="")
    view.update_modification_time()

    db_session.add(view)
    db_session.commit()


def run_aggregator(
    sketch_id, aggregator_name, aggregator_parameters=None, indices=None
):
    """Run an aggregator and return back results.

    Args:
        sketch_id (int): the sketch ID.
        aggregator_name (str): the name of the aggregator class to run.
        aggregator_parameters (dict): dict containing the parameters used
            for running the aggregator.
        indices (list): the list of OpenSearch index names to use.

    Returns:
        Tuple[Object, Dict]: a tuple containing the aggregator result object
            (instance of AggregationResult) and a dict containing metadata
            from the aggregator run.
    """
    agg_class = aggregator_manager.AggregatorManager.get_aggregator(aggregator_name)
    if not agg_class:
        return None, {}
    if not aggregator_parameters:
        aggregator_parameters = {}

    aggregator = agg_class(sketch_id=sketch_id, indices=indices)

    chart_type = aggregator_parameters.pop("supported_charts", None)
    chart_color = aggregator_parameters.pop("chart_color", "")

    time_before = time.time()
    result_obj = aggregator.run(**aggregator_parameters)
    time_after = time.time()

    aggregator_description = aggregator.describe

    meta = {
        "method": "aggregator_run",
        "chart_type": chart_type,
        "chart_color": chart_color,
        "name": aggregator_description.get("name"),
        "description": aggregator_description.get("description"),
        "es_time": time_after - time_before,
    }

    if chart_type:
        meta["vega_spec"] = result_obj.to_chart(
            chart_name=chart_type, chart_title=aggregator.chart_title, color=chart_color
        )
        meta["vega_chart_title"] = aggregator.chart_title

    return result_obj, meta


def run_aggregator_group(group, sketch_id):
    """Run an aggregator group and return back results.

    Args:
        group (models.sketch.Group): a group object.
        sketch_id (int): the sketch ID.

    Returns:
        Tuple[Object, List, Dict]: a tuple containing the altair chart object,
            a list of result object dicts and a dict containing metadata from
            the aggregator group run.
    """
    result_chart = None
    orientation = group.orientation
    objects = []
    time_before = time.time()
    for aggregator in group.aggregations:
        if aggregator.aggregationgroup_id != group.id:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "All aggregations in a group must belong to the group.",
            )
        if aggregator.sketch_id != group.sketch_id:
            abort(
                HTTP_STATUS_CODE_BAD_REQUEST,
                "All aggregations in a group must belong to the group " "sketch",
            )

        if aggregator.parameters:
            aggregator_parameters = json.loads(aggregator.parameters)
        else:
            aggregator_parameters = {}

        agg_class = aggregator_manager.AggregatorManager.get_aggregator(
            aggregator.agg_type
        )
        if not agg_class:
            continue
        aggregator_obj = agg_class(sketch_id=sketch_id)
        chart_type = aggregator_parameters.pop("supported_charts", None)
        color = aggregator_parameters.pop("chart_color", "")
        result_obj = aggregator_obj.run(**aggregator_parameters)

        chart = result_obj.to_chart(
            chart_name=chart_type,
            chart_title=aggregator_obj.chart_title,
            as_chart=True,
            interactive=True,
            color=color,
        )

        if result_chart is None:
            result_chart = chart
        elif orientation == "horizontal":
            result_chart = alt.hconcat(chart, result_chart)
        elif orientation == "vertical":
            result_chart = alt.vconcat(chart, result_chart)
        else:
            result_chart = alt.layer(chart, result_chart)

        buckets = result_obj.to_dict()
        buckets["buckets"] = buckets.pop("values")
        result = {"aggregation_result": {aggregator.name: buckets}}
        objects.append(result)

    parameters = {}
    if group.parameters:
        parameters = json.loads(group.parameters)

    result_chart.title = parameters.get("chart_title", group.name)
    time_after = time.time()

    meta = {
        "method": "aggregator_group",
        "chart_type": "compound: {0:s}".format(orientation),
        "name": group.name,
        "description": group.description,
        "es_time": time_after - time_before,
        "vega_spec": result_chart.to_dict(),
        "vega_chart_title": group.name,
    }

    return result_chart, objects, meta


def load_yaml_config(config_parameter_name):
    """Load a YAML file.
    Args:
        config_paramater_name (str): Name of the config paramter to get the
        path to the YAML file from.

    Returns:
        A dictionary with the YAML data.
    """
    yaml_path = current_app.config.get(config_parameter_name, "")
    if not yaml_path:
        logger.error(
            "The path to the YAML file isn't defined in the " "main configuration file"
        )
        return {}
    if not os.path.isfile(yaml_path):
        logger.error(
            "Unable to read the config, file: "
            "[{0:s}] does not exist".format(yaml_path)
        )
        return {}

    with open(yaml_path, "r") as fh:
        return yaml.safe_load(fh)


def load_csv_file(config_parametre_name):
    """Load a CSV file.
    Args:
        config_paramater_name (str): Name of the config paramter to get the
        path to the CSV file from.

    Returns:
        A data frame with the CSV content
    """
    csv_file = current_app.config.get(config_parametre_name, "")
    if not csv_file:
        logger.error(
            "The path to the CSV file isn't defined in the " "main configuration file"
        )
        return {}
    if not os.path.isfile(csv_file):
        logger.error(
            "Unable to read the config, file: "
            "[{0:s}] does not exist".format(csv_file)
        )
        return {}

    return pd.read_csv(csv_file)


def escape_query_string(query_string):
    """Escape a search query string to support Opensearch queries.

    Args:
        query_string: Opensearch query string.

    Returns:
        Query string with certain characters escaped.
    """
    escaped_query_string = query_string.translate(
        str.maketrans(
            {
                "/": r"\/",
                ".": r"\.",
                "\\": r"\\",
            }
        )
    )
    return escaped_query_string


def is_valid_index_name(index_name):
    """Validate index name.

    Args:
        index_name: string with the index name in uuid.uuid4.hex format.

    Returns:
        A boolean indicating whether the index name is valid or not.
    """
    regex = re.compile(r"[0-9a-f]{32}", re.I)
    match = regex.match(index_name)
    return bool(match)


def format_upload_path(upload_path, index_name):
    """Format upload path.

    Args:
        upload_path: string with the upload path.
        index_name: string with the index name in uuid.uuid4.hex format.

    Returns:
        A string with the formatted upload path.
    """
    base_path = pathlib.Path(upload_path)
    index_name_path = pathlib.Path(index_name)
    if not base_path.is_absolute():
        raise ValueError("Upload path must be absolute")

    if not index_name_path.is_absolute():
        full_path = base_path / index_name_path
        return full_path.as_posix()

    full_path = base_path / index_name_path.relative_to(base_path.anchor)
    return full_path.as_posix()
