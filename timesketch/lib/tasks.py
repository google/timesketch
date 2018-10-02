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
import traceback

from flask import current_app

from timesketch import create_app
from timesketch import create_celery_app
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.lib.utils import read_and_validate_csv
from timesketch.lib.utils import read_and_validate_jsonl
from timesketch.lib.analyzers.similarity import SimilarityScorer
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Timeline

celery = create_celery_app()
flask_app = create_app()


class SqlAlchemyTask(celery.Task):
    """An abstract task that closes the database on task completion."""
    abstract = True

    def after_return(self, *args, **kwargs):
        db_session.remove()
        super(SqlAlchemyTask, self).after_return(*args, **kwargs)


def _set_timeline_status(index_name, status, error_msg=None):
    """Helper function to set status for searchindex and all related timelines.

    Args:
        index_name: Name of the datastore index.
        status: Status to set.
        error_msg: Error message.
    """
    # Run within Flask context so we can make database changes
    with flask_app.app_context():
        searchindex = SearchIndex.query.filter_by(index_name=index_name).first()
        timelines = Timeline.query.filter_by(searchindex=searchindex).all()

        # Set status
        searchindex.set_status(status)
        for timeline in timelines:
            timeline.set_status(status)
            db_session.add(timeline)

        # Update description if there was a failure in ingestion
        if error_msg and status == u'fail':
            # TODO: Don't overload the description field.
            searchindex.description = error_msg

        # Commit changes to database
        db_session.add(searchindex)
        db_session.commit()


@celery.task(track_started=True)
def run_similarity_scorer(index_name, data_type):
    """Create a Celery task for calculating similarity scores.

    Args:
      index_name: Name of the datastore index.
      data_type: Data type attribute to process.

    Returns:
      index_name as a string.
    """
    log_message = u'Similarity scorer for data_type {0:s} on index {1:s}'
    logging.info(log_message.format(data_type, index_name))
    scorer = SimilarityScorer(index=index_name, data_type=data_type)
    result = scorer.run()
    logging.info(u'Similarity scorer result: %s' % result)
    return index_name


@celery.task(track_started=True, base=SqlAlchemyTask)
def run_plaso(source_file_path, timeline_name, index_name, source_type):
    """Create a Celery task for processing Plaso storage file.

    Args:
        source_file_path: Path to plaso storage file.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.
        source_type: Type of file, csv or jsonl.

    Returns:
        String with summary of processed events.
    """
    # Log information to Celery
    message = u'Index timeline [{0:s}] to index [{1:s}] (source: {2:s})'
    logging.info(message.format(timeline_name, index_name, source_type))

    cmd = [
        u'psort.py', u'-o', u'timesketch', source_file_path, u'--name',
        timeline_name, u'--status_view', u'none', u'--index', index_name
    ]

    # Run psort.py
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        # Mark the searchindex and timelines as failed and exit the task
        _set_timeline_status(index_name, status=u'fail', error_msg=e.output)
        return e.output

    # Mark the searchindex and timelines as ready
    _set_timeline_status(index_name, status=u'ready')

    return index_name


@celery.task(track_started=True, base=SqlAlchemyTask)
def run_csv_jsonl(source_file_path, timeline_name, index_name, source_type):
    """Create a Celery task for processing a CSV or JSONL file.

    Args:
        source_file_path: Path to CSV or JSONL file.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.
        source_type: Type of file, csv or jsonl.

    Returns:
        Dictionary with count of processed events.
    """
    event_type = u'generic_event'  # Document type for Elasticsearch
    validators = {
        u'csv': read_and_validate_csv,
        u'jsonl': read_and_validate_jsonl
    }
    read_and_validate = validators.get(source_type)

    # Log information to Celery
    logging.info(
        u'Index timeline [{0:s}] to index [{1:s}] (source: {2:s})'.format(
            timeline_name, index_name, source_type))

    es = ElasticsearchDataStore(
        host=current_app.config[u'ELASTIC_HOST'],
        port=current_app.config[u'ELASTIC_PORT'])

    # Reason for the broad exception catch is that we want to capture
    # all possible errors and exit the task.
    try:
        es.create_index(index_name=index_name, doc_type=event_type)
        for event in read_and_validate(source_file_path):
            es.import_event(index_name, event_type, event)
        # Import the remaining events
        es.import_event(index_name, event_type)
    except Exception as e:
        # Mark the searchindex and timelines as failed and exit the task
        error_msg = traceback.format_exc(e)
        _set_timeline_status(index_name, status=u'fail', error_msg=error_msg)
        logging.error(error_msg)
        return

    # Set status to ready when done
    _set_timeline_status(index_name, status=u'ready')

    return index_name
