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

import logging
import subprocess

from flask import current_app

from timesketch import create_app
from timesketch import create_celery_app
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.lib.utils import read_and_validate_csv
from timesketch.lib.utils import read_and_validate_jsonl
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Timeline

celery = create_celery_app()
flask_app = create_app()


def _set_timeline_status(index_name, status, error_msg=None):
    """Helper function to set searchindex and all related timelines status.

    Args:
        index_name: Name of the datastore index.
        status: Status to set.
        error_msg: Error message.
    """
    # Run within Flask context so we can make database changes
    with flask_app.app_context():
        searchindex = SearchIndex.query.filter_by(index_name=index_name).first()
        timelines = Timeline.query.filter_by(searchindex=searchindex).all()

        es = ElasticsearchDataStore(
            host=current_app.config[u'ELASTIC_HOST'],
            port=current_app.config[u'ELASTIC_PORT'])

        # Set status
        searchindex.set_status(status)
        for timeline in timelines:
            timeline.set_status(status)
            db_session.add(timeline)

        # Update description if there was a failure in ingestion
        if error_msg and status == u'fail':
            # TODO: Don't overload the description field.
            searchindex.description = error_msg
            es.delete_index(index_name)

        # Commit changes to database
        db_session.add(searchindex)
        db_session.commit()


@celery.task(track_started=True)
def run_plaso(source_file_path, timeline_name, index_name, username=None):
    """Create a Celery task for processing Plaso storage file.

    Args:
        source_file_path: Path to plaso storage file.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.
        username: Username of the user who will own the timeline.

    Returns:
        String with summary of processed events.
    """
    cmd = [
        u'psort.py', u'-o', u'timesketch', source_file_path, u'--name',
        timeline_name, u'--status_view', u'none', u'--index', index_name
    ]
    if username:
        cmd.append(u'--username')
        cmd.append(username)

    # Run psort.py
    try:
        cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        # Mark the searchindex and timelines as failed and exit the task
        _set_timeline_status(index_name, status=u'fail', error_msg=e.output)
        return e.output

    # Mark the searchindex and timelines as ready
    _set_timeline_status(index_name, status=u'ready')

    return cmd_output


@celery.task(track_started=True)
def run_csv(source_file_path, timeline_name, index_name, username=None):
    """Create a Celery task for processing a CSV file.

    Args:
        source_file_path: Path to CSV file.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.
        username: Username of the user who will own the timeline.

    Returns:
        Dictionary with count of processed events.
    """
    event_type = u'generic_event'  # Document type for Elasticsearch

    # Log information to Celery
    logging.info(u'Index name: %s', index_name)
    logging.info(u'Timeline name: %s', timeline_name)
    logging.info(u'Document type: %s', event_type)
    logging.info(u'Owner: %s', username)

    es = ElasticsearchDataStore(
        host=current_app.config[u'ELASTIC_HOST'],
        port=current_app.config[u'ELASTIC_PORT'])

    es.create_index(index_name=index_name, doc_type=event_type)
    for event in read_and_validate_csv(source_file_path):
        es.import_event(index_name, event_type, event)

    # Import the remaining events
    total_events = es.import_event(index_name, event_type)

    # Set status to ready when done
    _set_timeline_status(index_name, status=u'ready')

    return {u'Events processed': total_events}


@celery.task(track_started=True)
def run_jsonl(source_file_path, timeline_name, index_name, username=None):
    """Create a Celery task for processing a JSONL file.

    Args:
        source_file_path: Path to JSONL file.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.
        username: Username of the user who will own the timeline.

    Returns:
        Dictionary with count of processed events.
    """
    event_type = u'generic_event'  # Document type for Elasticsearch

    # Log information to Celery
    logging.info(u'Index name: %s', index_name)
    logging.info(u'Timeline name: %s', timeline_name)
    logging.info(u'Document type: %s', event_type)
    logging.info(u'Owner: %s', username)

    es = ElasticsearchDataStore(
        host=current_app.config[u'ELASTIC_HOST'],
        port=current_app.config[u'ELASTIC_PORT'])

    es.create_index(index_name=index_name, doc_type=event_type)
    for event in read_and_validate_jsonl(source_file_path):
        es.import_event(index_name, event_type, event)

    # Import the remaining events
    total_events = es.import_event(index_name, event_type)

    # Set status to ready when done
    _set_timeline_status(index_name, status=u'ready')

    return {u'Events processed': total_events}
