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

from __future__ import unicode_literals

import logging
import subprocess
import traceback

from celery import group
from celery import chain
from flask import current_app

from timesketch import create_app
from timesketch import create_celery_app
from timesketch.lib.analyzers import manager
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.lib.utils import read_and_validate_csv
from timesketch.lib.utils import read_and_validate_jsonl
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Timeline

celery = create_celery_app()
flask_app = create_app()


class SqlAlchemyTask(celery.Task):
    """An abstract task that runs on task completion."""
    abstract = True

    def after_return(self, *args, **kwargs):
        """Close the database session on task completion."""
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
        if error_msg and status == 'fail':
            # TODO: Don't overload the description field.
            searchindex.description = error_msg

        # Commit changes to database
        db_session.add(searchindex)
        db_session.commit()


def _get_index_task_class(file_extension):
    """Get correct index task function for the supplied file type.

    Args:
        file_extension (str): File type based on filename extension.

    Returns:
        A task function.

    Raises:
        KeyError if no task class can be found.
    """
    if file_extension == 'plaso':
        index_class = run_plaso
    elif file_extension in ['csv', 'jsonl']:
        index_class = run_csv_jsonl
    else:
        raise KeyError('No task that supports {0:s}'.format(file_extension))
    return index_class


def _get_index_analyzers():
    """Get list of index analysis tasks to run.

    Returns:
        Group of index analysis tasks as Celery subtask signatures or None if
        index analyzers are disabled in config.
    """
    tasks = []

    # Exit early if index analyzers are disabled.
    if not current_app.config.get(u'ENABLE_INDEX_ANALYZERS', False):
        return None

    for analyzer_name, analyzer_cls in manager.AnalysisManager.get_analyzers():
        kwarg_list = analyzer_cls.get_kwargs()

        if not analyzer_cls.IS_SKETCH_ANALYZER:
            if kwarg_list:
                for kwargs in kwarg_list:
                    tasks.append(
                        run_index_analyzer.s(analyzer_name, **kwargs))
            else:
                tasks.append(run_index_analyzer.s(analyzer_name))

    return group(tasks)


def build_index_pipeline(file_path, timeline_name, index_name, file_extension,
                         sketch_id=None):
    """Build a pipeline for index and analysis.

    Args:
        file_path: Path to the file to index.
        timeline_name: Name of the timeline to create.
        index_name: Name of the index to index to.
        file_extension: The file extension of the file.
        sketch_id: The ID of the sketch to analyze.

    Returns:
        Celery chain with indexing task (or single indexing task) and analyzer
        task group.
    """
    index_task_class = _get_index_task_class(file_extension)
    index_analyzer_group = _get_index_analyzers()
    sketch_analyzer_group = None

    if sketch_id:
        sketch_analyzer_group = build_sketch_analysis_pipeline(sketch_id)

    index_task = index_task_class.s(
        file_path, timeline_name, index_name, file_extension)

    # If there are no analyzers just run the indexer.
    if not index_analyzer_group and not sketch_analyzer_group:
        return index_task

    if sketch_analyzer_group:
        if not index_analyzer_group:
            return chain(
                index_task, run_sketch_init.s(), sketch_analyzer_group)
        return chain(
            index_task, index_analyzer_group, run_sketch_init.s(),
            sketch_analyzer_group)

    return chain(index_task, index_analyzer_group)


def build_sketch_analysis_pipeline(sketch_id):
    """Build a pipeline for sketch analysis.

    Args:
        sketch_id: The ID of the sketch to analyze.

    Returns:
        Celery group with analysis tasks or None if no analyzers are enabled.
    """
    tasks = []

    # Exit early if sketch analyzers are disabled.
    if not current_app.config.get(u'ENABLE_SKETCH_ANALYZERS', False):
        return None

    for analyzer_name, analyzer_cls in manager.AnalysisManager.get_analyzers():
        kwarg_list = analyzer_cls.get_kwargs()

        if not analyzer_cls.IS_SKETCH_ANALYZER:
            continue

        if kwarg_list:
            for kwargs in kwarg_list:
                tasks.append(run_sketch_analyzer.s(
                    sketch_id, analyzer_name, **kwargs))
        else:
            tasks.append(run_sketch_analyzer.s(sketch_id, analyzer_name))

    return group(tasks)


@celery.task(track_started=True)
def run_sketch_init(index_name_list):
    """Create sketch init Celery task.

    This task is needed to enable chaining of index analyzers and sketch
    analyzer task groups. In order to run the sketch analyzers after indexing
    this task needs to execute before any sketch analyzers.

    Args:
        index_name_list: List of index names.

    Returns:
        List with first entry of index_name_list.
    """
    if isinstance(index_name_list, basestring):
        index_name_list = [index_name_list]
    return index_name_list[:1]


@celery.task(track_started=True)
def run_index_analyzer(index_name, analyzer_name, **kwargs):
    """Create a Celery task for an index analyzer.

    Args:
      index_name: Name of the datastore index.
      analyzer_name: Name of the analyzer.

    Returns:
      Name (str) of the index.
    """
    analyzer_class = manager.AnalysisManager.get_analyzer(analyzer_name)
    analyzer = analyzer_class(index_name=index_name, **kwargs)
    result = analyzer.run_wrapper()
    logging.info('[{0:s}] result: {1:s}'.format(analyzer_name, result))
    return index_name


@celery.task(track_started=True)
def run_sketch_analyzer(index_name, sketch_id, analyzer_name, **kwargs):
    """Create a Celery task for a sketch analyzer.

    Args:
      sketch_id: ID of the sketch to analyze.
      analyzer_name: Name of the analyzer.

    Returns:
      ID (str) of the sketch.
    """
    analyzer_class = manager.AnalysisManager.get_analyzer(analyzer_name)
    analyzer = analyzer_class(
        sketch_id=sketch_id, index_name=index_name, **kwargs)
    result = analyzer.run_wrapper()
    logging.info('[{0:s}] result: {1:s}'.format(analyzer_name, result))
    return sketch_id


@celery.task(track_started=True, base=SqlAlchemyTask)
def run_plaso(source_file_path, timeline_name, index_name, source_type):
    """Create a Celery task for processing Plaso storage file.

    Args:
        source_file_path: Path to plaso storage file.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.
        source_type: Type of file, csv or jsonl.

    Returns:
        Elasticsearch index name.
    """
    # Log information to Celery
    message = 'Index timeline [{0:s}] to index [{1:s}] (source: {2:s})'
    logging.info(message.format(timeline_name, index_name, source_type))

    try:
        psort_path = current_app.config['PSORT_PATH']
    except KeyError:
        psort_path = 'psort.py'

    cmd = [
        psort_path, '-o', 'timesketch', source_file_path, '--name',
        timeline_name, '--status_view', 'none', '--index', index_name
    ]

    # Run psort.py
    try:
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        # Mark the searchindex and timelines as failed and exit the task
        _set_timeline_status(index_name, status='fail', error_msg=e.output)
        return e.output

    # Mark the searchindex and timelines as ready
    _set_timeline_status(index_name, status='ready')

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
        Elasticsearch index name.
    """
    event_type = 'generic_event'  # Document type for Elasticsearch
    validators = {
        'csv': read_and_validate_csv,
        'jsonl': read_and_validate_jsonl
    }
    read_and_validate = validators.get(source_type)

    # Log information to Celery
    logging.info(
        'Index timeline [{0:s}] to index [{1:s}] (source: {2:s})'.format(
            timeline_name, index_name, source_type))

    es = ElasticsearchDataStore(
        host=current_app.config['ELASTIC_HOST'],
        port=current_app.config['ELASTIC_PORT'])

    # Reason for the broad exception catch is that we want to capture
    # all possible errors and exit the task.
    try:
        es.create_index(index_name=index_name, doc_type=event_type)
        for event in read_and_validate(source_file_path):
            es.import_event(index_name, event_type, event)
        # Import the remaining events
        es.flush_queued_events()
    except Exception as e:
        # Mark the searchindex and timelines as failed and exit the task
        error_msg = traceback.format_exc(e)
        _set_timeline_status(index_name, status='fail', error_msg=error_msg)
        logging.error(error_msg)
        return None

    # Set status to ready when done
    _set_timeline_status(index_name, status='ready')

    return index_name
