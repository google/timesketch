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
import logging
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
from timesketch.lib.datastores.elastic import ElasticSearchDataStore
from timesketch.lib.utils import read_csv
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex

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
def run_plaso(source_file_path, timeline_name, index_name, username=None):
    """Create a Celery task for processing Plaso storage file.

    Args:
        source_file_path: Path to plaso storage file.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.
        username: Username of the user who will own the timeline.

    Returns:
        Dictionary with count of processed events.
    """
    plaso_data_location = get_data_location()
    flush_interval = 1000  # events to queue before bulk index
    doc_type = u'plaso_event'  # Document type for Elasticsearch

    # Use Plaso psort frontend tool.
    frontend = psort.PsortFrontend()
    frontend.SetDataLocation(plaso_data_location)
    storage_reader = frontend.CreateStorageReader(source_file_path)

    # Setup the Timesketch output module.
    output_module = frontend.CreateOutputModule(u'timesketch')
    output_module.SetIndexName(index_name)
    output_module.SetTimelineName(timeline_name)
    output_module.SetFlushInterval(flush_interval)
    output_module.SetDocType(doc_type)
    if username:
        output_module.SetUserName(username)

    # Start process the Plaso storage file.
    counter = frontend.ExportEvents(storage_reader, output_module)

    return dict(counter)


@celery.task(track_started=True)
def run_csv(source_file_path, timeline_name, index_name):
    """Create a Celery task for processing a CSV file.

    Args:
        source_file_path: Path to CSV file.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.

    Returns:
        Dictionary with count of processed events.
    """
    flush_interval = 1000  # events to queue before bulk index
    event_type = u'generic_event'  # Document type for Elasticsearch

    # Log information to Celery
    logging.info(u'Index name: {0:s}'.format(index_name))
    logging.info(u'Timeline name: {0:s}'.format(timeline_name))
    logging.info(u'Flush interval: {0:d}'.format(flush_interval))
    logging.info(u'Document type: {0:s}'.format(event_type))

    es = ElasticSearchDataStore(
        host=current_app.config[u'ELASTIC_HOST'],
        port=current_app.config[u'ELASTIC_PORT'])

    es.create_index(index_name=index_name, doc_type=event_type)
    for event in read_csv(source_file_path):
        es.import_event(
            flush_interval, index_name, event_type, event)

    # Import the remaining events
    total_events = es.import_event(flush_interval, index_name, event_type)

    # We are done so let's remove the processing status flag
    search_index = SearchIndex.query.filter_by(index_name=index_name).first()
    search_index.status.remove(search_index.status[0])
    db_session.add(search_index)
    db_session.commit()

    return {u'Events processed': total_events}
