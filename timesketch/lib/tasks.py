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

import json
import six

from celery import chain
from celery import signals
from flask import current_app
from sqlalchemy import create_engine

from timesketch import create_celery_app
from timesketch.lib.analyzers import manager
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.lib.utils import read_and_validate_csv
from timesketch.lib.utils import read_and_validate_jsonl
from timesketch.lib.utils import send_email
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline
from timesketch.models.sketch import Analysis
from timesketch.models.sketch import AnalysisSession
from timesketch.models.user import User

celery = create_celery_app()


class SqlAlchemyTask(celery.Task):
    """An abstract task that runs on task completion."""
    abstract = True

    def after_return(self, *args, **kwargs):
        """Close the database session on task completion."""
        db_session.remove()
        super(SqlAlchemyTask, self).after_return(*args, **kwargs)


# pylint: disable=unused-argument
@signals.worker_process_init.connect
def init_worker(**kwargs):
    """Create new database engine per worker process."""
    url = celery.conf.get('SQLALCHEMY_DATABASE_URI')
    engine = create_engine(url)
    db_session.configure(bind=engine)


def _set_timeline_status(index_name, status, error_msg=None):
    """Helper function to set status for searchindex and all related timelines.

    Args:
        index_name: Name of the datastore index.
        status: Status to set.
        error_msg: Error message.
    """
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
        Celery chain of index analysis tasks as Celery subtask signatures or
        None if index analyzers are disabled in config.
    """
    tasks = []
    index_analyzers = current_app.config.get('AUTO_INDEX_ANALYZERS')

    if not index_analyzers:
        return None

    for analyzer_name, _ in manager.AnalysisManager.get_analyzers(
            index_analyzers):
        tasks.append(run_index_analyzer.s(analyzer_name))

    return chain(tasks)


def build_index_pipeline(file_path, timeline_name, index_name, file_extension,
                         sketch_id=None, only_index=False):
    """Build a pipeline for index and analysis.

    Args:
        file_path: Path to the file to index.
        timeline_name: Name of the timeline to create.
        index_name: Name of the index to index to.
        file_extension: The file extension of the file.
        sketch_id: The ID of the sketch to analyze.
        only_index: If set to true then only indexing tasks are run, not
            analyzers. This is to be used when uploading data in chunks,
            we don't want to run the analyzers until all chunks have been
            uploaded.

    Returns:
        Celery chain with indexing task (or single indexing task) and analyzer
        task group.
    """
    print('INDEX PIPELINE')
    index_task_class = _get_index_task_class(file_extension)
    index_analyzer_chain = _get_index_analyzers()
    sketch_analyzer_chain = None
    searchindex = SearchIndex.query.filter_by(index_name=index_name).first()

    index_task = index_task_class.s(
        file_path, timeline_name, index_name, file_extension)

    if only_index:
        print('ONLY INDEXING, NO ANALYZERS')
        return index_task
    print('We are about to get to the analyzers...')
    print('INDEX: {} - ID {}'.format(index_name, searchindex.id))

    if sketch_id:
        sketch_analyzer_chain = build_sketch_analysis_pipeline(
            sketch_id, searchindex.id, user_id=None)

    # If there are no analyzers just run the indexer.
    if not index_analyzer_chain and not sketch_analyzer_chain:
        return index_task

    if sketch_analyzer_chain:
        if not index_analyzer_chain:
            return chain(
                index_task, run_sketch_init.s(), sketch_analyzer_chain)
        return chain(
            index_task, index_analyzer_chain, run_sketch_init.s(),
            sketch_analyzer_chain)

    if current_app.config.get('ENABLE_EMAIL_NOTIFICATIONS'):
        return chain(
            index_task,
            index_analyzer_chain,
            run_email_result_task.s()
        )

    return chain(index_task, index_analyzer_chain)


def build_sketch_analysis_pipeline(sketch_id, searchindex_id, user_id,
                                   analyzer_names=None, analyzer_kwargs=None):
    """Build a pipeline for sketch analysis.

    If no analyzer_names is passed in then we assume auto analyzers should be
    run and get this list from the configuration. Parameters to the analyzers
    can be passed in to this function, otherwise they will be taken from the
    configuration. Either default kwargs for auto analyzers or defaults for
    manually run analyzers.

    Args:
        sketch_id (int): The ID of the sketch to analyze.
        searchindex_id (int): The ID of the searchindex to analyze.
        user_id (int): The ID of the user who started the analyzer.
        analyzer_names (list): List of analyzers to run.
        analyzer_kwargs (dict): Arguments to the analyzers.

    Returns:
        Celery group with analysis tasks or None if no analyzers are enabled.
    """
    print('BUILDING SKETCH PIPELINE FROM INDEX: {}'.format(searchindex_id))
    tasks = []

    if not analyzer_names:
        analyzer_names = current_app.config.get('AUTO_SKETCH_ANALYZERS', [])
        if not analyzer_kwargs:
            analyzer_kwargs = current_app.config.get(
                'AUTO_SKETCH_ANALYZERS_KWARGS', {})

    # Exit early if no sketch analyzers are configured to run.
    if not analyzer_names:
        return None

    if not analyzer_kwargs:
        analyzer_kwargs = current_app.config.get('ANALYZERS_DEFAULT_KWARGS', {})

    if user_id:
        user = User.query.get(user_id)
    else:
        user = None

    sketch = Sketch.query.get(sketch_id)
    analysis_session = AnalysisSession(user, sketch)

    analyzers = manager.AnalysisManager.get_analyzers(analyzer_names)
    for analyzer_name, analyzer_cls in analyzers:
        if not analyzer_cls.IS_SKETCH_ANALYZER:
            continue

        kwargs = analyzer_kwargs.get(analyzer_name, {})
        searchindex = SearchIndex.query.get(searchindex_id)
        timeline = Timeline.query.filter_by(
            sketch=sketch, searchindex=searchindex).first()

        analysis = Analysis(
            name=analyzer_name,
            description=analyzer_name,
            analyzer_name=analyzer_name,
            parameters=json.dumps(kwargs),
            user=user,
            sketch=sketch,
            timeline=timeline)
        analysis.set_status('PENDING')
        analysis_session.analyses.append(analysis)
        db_session.add(analysis)
        db_session.commit()

        tasks.append(run_sketch_analyzer.s(
            sketch_id, analysis.id, analyzer_name, **kwargs))

    # Commit the analysis session to the database.
    db_session.add(analysis_session)
    db_session.commit()

    if current_app.config.get('ENABLE_EMAIL_NOTIFICATIONS'):
        tasks.append(run_email_result_task.s(sketch_id))

    if not tasks:
        return None

    return chain(tasks)


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
    if isinstance(index_name_list, six.string_types):
        index_name_list = [index_name_list]
    return index_name_list[:1][0]


@celery.task(track_started=True)
def run_email_result_task(index_name, sketch_id=None):
    """Create email Celery task.

    This task is run after all sketch analyzers are done and emails
    the result of all analyzers to the user who imported the data.

    Args:
        index_name: An index name.
        sketch_id: A sketch ID (optional).

    Returns:
        Email sent status.
    """
    # We need to get a fake request context so that url_for() will work.
    with current_app.test_request_context():
        searchindex = SearchIndex.query.filter_by(index_name=index_name).first()
        sketch = None

        try:
            to_username = searchindex.user.username
        except AttributeError:
            logging.warning('No user to send email to.')
            return ''

        if sketch_id:
            sketch = Sketch.query.get(sketch_id)

        subject = 'Timesketch: [{0:s}] is ready'.format(searchindex.name)

        # TODO: Use jinja templates.
        body = 'Your timeline [{0:s}] has been imported and is ready.'.format(
            searchindex.name)

        if sketch:
            view_urls = sketch.get_view_urls()
            view_links = []
            for view_url, view_name in iter(view_urls.items()):
                view_links.append('<a href="{0:s}">{1:s}</a>'.format(
                    view_url,
                    view_name))

            body = body + '<br><br><b>Sketch</b><br>{0:s}'.format(
                sketch.external_url)

            analysis_results = searchindex.description.replace('\n', '<br>')
            body = body + '<br><br><b>Analysis</b>{0:s}'.format(
                analysis_results)

            if view_links:
                body = body + '<br><br><b>Views</b><br>' + '<br>'.join(
                    view_links)

        try:
            send_email(subject, body, to_username, use_html=True)
        except RuntimeError as e:
            return repr(e)

    return 'Sent email to {0:s}'.format(to_username)


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
    if result:
        logging.info('[{0:s}] result: {1:s}'.format(analyzer_name, result))
    else:
        logging.info('[{0:s}] return with no results.'.format(analyzer_name))
    return index_name


@celery.task(track_started=True)
def run_sketch_analyzer(index_name, sketch_id, analysis_id, analyzer_name,
                        **kwargs):
    """Create a Celery task for a sketch analyzer.

    Args:
        index_name: Name of the datastore index.
        sketch_id: ID of the sketch to analyze.
        analysis_id: ID of the analysis.
        analyzer_name: Name of the analyzer.

    Returns:
      Name (str) of the index.
    """
    analyzer_class = manager.AnalysisManager.get_analyzer(analyzer_name)
    analyzer = analyzer_class(
        sketch_id=sketch_id, index_name=index_name, **kwargs)

    result = analyzer.run_wrapper(analysis_id)
    logging.info('[{0:s}] result: {1:s}'.format(analyzer_name, result))
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
        Name (str) of the index.
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
        if six.PY3:
            subprocess.check_output(
                cmd, stderr=subprocess.STDOUT, encoding='utf-8')
        else:
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
        Name (str) of the index.
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

    except (RuntimeError, ImportError, NameError, UnboundLocalError) as e:
        _set_timeline_status(index_name, status='fail', error_msg=str(e))
        raise

    except Exception as e:  # pylint: disable=broad-except
        # Mark the searchindex and timelines as failed and exit the task
        error_msg = traceback.format_exc(e)
        _set_timeline_status(index_name, status='fail', error_msg=error_msg)
        logging.error(error_msg)
        return None

    # Set status to ready when done
    _set_timeline_status(index_name, status='ready')

    return index_name
