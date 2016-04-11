# Copyright 2015 Google Inc. All rights reserved.
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
"""Celery task for processing Plaso storage files."""

import os
import sys

from flask import current_app
# We currently don't have plaso in our Travis setup. This is a workaround
# for that until we fix the Travis environment.
# TODO: Add Plaso to our Travis environment we are running our tests in.
try:
    from plaso.frontend import psort
except ImportError:
    pass

from timesketch import create_celery_app

celery = create_celery_app()


def get_data_location():
    """Path to the plaso data directory.

    Returns:
        The path to where the plaso data directory is or None if not existing.
    """
    data_location = current_app.config.get(u'PLASO_DATA_LOCATION', None)
    if not data_location:
        data_location = os.path.join(sys.prefix, u'share', u'plaso')
    if not os.path.exists(data_location):
        data_location = None
    return data_location


@celery.task(track_started=True)
def run_plaso(source_file_path, timeline_name, index_name):
    """Create a Celery task for processing Plaso storage file.

    Args:
        source_file_path: Path to plaso storage file.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.

    Returns:
        Dictionary with count of processed events.
    """
    plaso_data_location = get_data_location()
    analysis_plugins = None
    flush_interval_ms = 1000

    # Use the Psort frontend for processing.
    frontend = psort.PsortFrontend()
    frontend.SetDataLocation(plaso_data_location)
    storage_file = frontend.OpenStorage(
        source_file_path, read_only=True)

    # Setup the Timesketch output module.
    frontend.SetOutputFormat(u'timesketch')
    output_module = frontend.GetOutputModule(storage_file)
    output_module.SetFlushInterval(flush_interval_ms)
    output_module.SetIndex(index_name)
    output_module.SetName(timeline_name)

    plugins, queue_producers = frontend.GetAnalysisPluginsAndEventQueues(
        analysis_plugins)
    counter = frontend.ProcessStorage(
        output_module, storage_file, source_file_path, plugins, queue_producers)

    return dict(counter)
