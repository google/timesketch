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

import os
import logging
import subprocess
import traceback

import codecs
import io
import json
import six
import yaml

from elasticsearch.exceptions import NotFoundError
from elasticsearch.exceptions import RequestError
from flask import current_app

from celery import chain
from celery import group
from celery import signals
from sqlalchemy import create_engine

# To be able to determine plaso's version.
try:
    import plaso
except ImportError:
    plaso = None

from timesketch.app import configure_logger
from timesketch.app import create_celery_app
from timesketch.lib import datafinder
from timesketch.lib import errors
from timesketch.lib.analyzers import manager
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.lib.utils import read_and_validate_csv
from timesketch.lib.utils import read_and_validate_jsonl
from timesketch.lib.utils import send_email
from timesketch.models import db_session
from timesketch.models.sketch import Analysis
from timesketch.models.sketch import AnalysisSession
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline
from timesketch.models.user import User


logger = logging.getLogger('timesketch.tasks')
celery = create_celery_app()


PLASO_MINIMUM_VERSION = 20201228


# pylint: disable=unused-argument
@signals.after_setup_logger.connect
def setup_loggers(*args, **kwargs):
    """Configure the logger."""
    configure_logger()


def get_import_errors(error_container, index_name, total_count):
    """Returns a string with error message or an empty string if no errors.

    Args:
      error_container: dict with error messages for each index.
      index_name: string with the search index name.
      total_count: integer with the total amount of events indexed.
    """
    if index_name not in error_container:
        return ''

    index_dict = error_container[index_name]
    error_list = index_dict.get('errors', [])

    if not error_list:
        return ''

    error_count = len(error_list)

    error_types = index_dict.get('types')
    error_details = index_dict.get('details')

    if error_types:
        top_type = error_types.most_common()[0][0]
    else:
        top_type = 'Unknown Reasons'

    if error_details:
        top_details = error_details.most_common()[0][0]
    else:
        top_details = 'Unknown Reasons'

    if total_count is None:
        total_count = 0

    if not top_type:
        top_type = 'Unknown Reasons'
    if not top_details:
        top_details = 'Unknown Reasons'

    return (
        '{0:d} out of {1:d} events imported. Most common error type '
        'is "{2:s}" with the detail of "{3:s}"').format(
            total_count - error_count, total_count,
            top_type, top_details)


class SqlAlchemyTask(celery.Task):
    """An abstract task that runs on task completion."""
    abstract = True

    def after_return(self, *args, **kwargs):
        """Close the database session on task completion."""
        db_session.remove()
        super().after_return(*args, **kwargs)


# pylint: disable=unused-argument
@signals.worker_process_init.connect
def init_worker(**kwargs):
    """Create new database engine per worker process."""
    url = celery.conf.get('SQLALCHEMY_DATABASE_URI')
    engine = create_engine(url)
    db_session.configure(bind=engine)


def _close_index(index_name, data_store, timeline_id):
    """Helper function to close an index if it is not used somewhere else.

    Args:
        index_name: String with the Elastic index name.
        data_store: Instance of elastic.ElasticsearchDataStore.
        timeline_id: ID of the timeline the index belongs to.
    """
    indices = SearchIndex.query.filter_by(index_name=index_name).all()
    for index in indices:
        for timeline in index.timelines:
            if timeline.get_status.status in ('closed', 'deleted', 'archived'):
                continue

            if timeline.id != timeline_id:
                return

    try:
        data_store.client.indices.close(index=index_name)
    except NotFoundError:
        logger.error(
            'Unable to close index: {0:s} - index not '
            'found'.format(index_name))


def _set_timeline_status(timeline_id, status, error_msg=None):
    """Helper function to set status for searchindex and all related timelines.

    Args:
        timeline_id: Timeline ID.
        status: Status to set.
        error_msg: Error message.
    """
    timeline = Timeline.query.get(timeline_id)

    if not timeline:
        logger.warning('Cannot set status: No such timeline')
        return

    # Check if there is at least one data source that hasn't failed.
    multiple_sources = any(not x.error_message for x in timeline.datasources)

    if multiple_sources:
        timeline_status = timeline.get_status.status.lower()
        if timeline_status != 'process' and status != 'fail':
            timeline.set_status(status)
            timeline.searchindex.set_status(status)
    else:
        timeline.set_status(status)
        timeline.searchindex.set_status(status)

    # Update description if there was a failure in ingestion.
    if error_msg:
        if timeline.datasources:
            data_source = timeline.datasources[-1]
            data_source.error_message = error_msg

    # Commit changes to database
    db_session.add(timeline)
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


def build_index_pipeline(
        file_path='', events='', timeline_name='', index_name='',
        file_extension='', sketch_id=None, only_index=False, timeline_id=None):
    """Build a pipeline for index and analysis.

    Args:
        file_path: The full path to a file to upload, either a file_path or
            or events need to be defined.
        events: String with the event data, either file_path or events
            needs to be defined.
        timeline_name: Name of the timeline to create.
        index_name: Name of the index to index to.
        file_extension: The file extension of the file.
        sketch_id: The ID of the sketch to analyze.
        only_index: If set to true then only indexing tasks are run, not
            analyzers. This is to be used when uploading data in chunks,
            we don't want to run the analyzers until all chunks have been
            uploaded.
        timeline_id: Optional ID of the timeline object this data belongs to.

    Returns:
        Celery chain with indexing task (or single indexing task) and analyzer
        task group.
    """
    if not (file_path or events):
        raise RuntimeError(
            'Unable to upload data, missing either a file or events.')
    index_task_class = _get_index_task_class(file_extension)
    sketch_analyzer_chain = None
    searchindex = SearchIndex.query.filter_by(index_name=index_name).first()

    index_task = index_task_class.s(
        file_path, events, timeline_name, index_name, file_extension,
        timeline_id)

    # TODO: Check if a scenario is set or an investigative question
    # is in the sketch, and then enable data finder on the newly
    # indexed data.
    if only_index:
        return index_task

    if sketch_id:
        sketch_analyzer_chain, _ = build_sketch_analysis_pipeline(
            sketch_id, searchindex.id, user_id=None)

    # If there are no analyzers just run the indexer.
    if not sketch_analyzer_chain:
        return index_task

    if sketch_analyzer_chain:
        return chain(
            index_task, run_sketch_init.s(), sketch_analyzer_chain)

    if current_app.config.get('ENABLE_EMAIL_NOTIFICATIONS'):
        return chain(
            index_task,
            run_email_result_task.s()
        )

    return chain(index_task)


def build_sketch_analysis_pipeline(
        sketch_id, searchindex_id, user_id, analyzer_names=None,
        analyzer_kwargs=None, timeline_id=None):
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
        timeline_id (int): Optional int of the timeline to run the analyzer on.

    Returns:
        A tuple with a Celery group with analysis tasks or None if no analyzers
        are enabled and an analyzer session ID.
    """
    tasks = []

    if not analyzer_names:
        analyzer_names = current_app.config.get('AUTO_SKETCH_ANALYZERS', [])
        if not analyzer_kwargs:
            analyzer_kwargs = current_app.config.get(
                'AUTO_SKETCH_ANALYZERS_KWARGS', {})

    # Exit early if no sketch analyzers are configured to run.
    if not analyzer_names:
        return None, None

    if not analyzer_kwargs:
        analyzer_kwargs = current_app.config.get('ANALYZERS_DEFAULT_KWARGS', {})

    if user_id:
        user = User.query.get(user_id)
    else:
        user = None

    sketch = Sketch.query.get(sketch_id)
    analysis_session = AnalysisSession(user, sketch)

    analyzers = manager.AnalysisManager.get_analyzers(analyzer_names)
    for analyzer_name, _ in analyzers:
        kwargs = analyzer_kwargs.get(analyzer_name, {})
        searchindex = SearchIndex.query.get(searchindex_id)

        timeline = None
        if timeline_id:
            timeline = Timeline.query.get(timeline_id)

        if not timeline:
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
            sketch_id, analysis.id, analyzer_name,
            timeline_id=timeline_id, **kwargs))

    # Commit the analysis session to the database.
    db_session.add(analysis_session)
    db_session.commit()

    if current_app.config.get('ENABLE_EMAIL_NOTIFICATIONS'):
        tasks.append(run_email_result_task.s(sketch_id))

    if not tasks:
        return None, None

    return chain(tasks), analysis_session


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
            logger.warning('No user to send email to.')
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
def run_sketch_analyzer(
        index_name, sketch_id, analysis_id, analyzer_name,
        timeline_id=None, **kwargs):
    """Create a Celery task for a sketch analyzer.

    Args:
        index_name: Name of the datastore index.
        sketch_id: ID of the sketch to analyze.
        analysis_id: ID of the analysis.
        analyzer_name: Name of the analyzer.
        timeline_id: Int of the timeline this analyzer belongs to.

    Returns:
      Name (str) of the index.
    """
    analyzer_class = manager.AnalysisManager.get_analyzer(analyzer_name)
    analyzer = analyzer_class(
        sketch_id=sketch_id, index_name=index_name,
        timeline_id=timeline_id, **kwargs)

    result = analyzer.run_wrapper(analysis_id)
    logger.info('[{0:s}] result: {1:s}'.format(analyzer_name, result))
    return index_name


@celery.task(track_started=True, base=SqlAlchemyTask)
def run_plaso(
        file_path, events, timeline_name, index_name, source_type, timeline_id):
    """Create a Celery task for processing Plaso storage file.

    Args:
        file_path: Path to the plaso file on disk.
        events: String with event data, invalid for plaso files.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.
        source_type: Type of file, csv or jsonl.
        timeline_id: ID of the timeline object this data belongs to.

    Raises:
        RuntimeError: If the function is called using events, plaso
            is not installed or is of unsupported version.
    Returns:
        Name (str) of the index.
    """
    if not plaso:
        raise RuntimeError(
            'Plaso isn\'t installed, unable to continue processing plaso '
            'files.')

    plaso_version = int(plaso.__version__)
    if plaso_version <= PLASO_MINIMUM_VERSION:
        raise RuntimeError(
            'Plaso version is out of date (version {0:d}, please upgrade to a '
            'version that is later than {1:d}'.format(
                plaso_version, PLASO_MINIMUM_VERSION))

    if events:
        raise RuntimeError('Plaso uploads needs a file, not events.')

    event_type = 'generic_event'  # Document type for Elasticsearch

    mappings = None
    mappings_file_path = current_app.config.get('PLASO_MAPPING_FILE', '')
    if os.path.isfile(mappings_file_path):
        try:
            with open(mappings_file_path, 'r') as mfh:
                mappings = json.load(mfh)

                if not isinstance(mappings, dict):
                    raise RuntimeError(
                        'Unable to create mappings, the mappings are not a '
                        'dict, please look at the file: {0:s}'.format(
                            mappings_file_path))
        except (json.JSONDecodeError, IOError):
            logger.error('Unable to read in mapping', exc_info=True)

    elastic_server = current_app.config.get('ELASTIC_HOST')
    if not elastic_server:
        raise RuntimeError(
            'Unable to connect to Elastic, no server set, unable to '
            'process plaso file.')
    elastic_port = current_app.config.get('ELASTIC_PORT')
    if not elastic_port:
        raise RuntimeError(
            'Unable to connect to Elastic, no port set, unable to '
            'process plaso file.')

    es = ElasticsearchDataStore(
        host=elastic_server, port=elastic_port)

    try:
        es.create_index(
            index_name=index_name, doc_type=event_type, mappings=mappings)
    except errors.DataIngestionError as e:
        _set_timeline_status(timeline_id, status='fail', error_msg=str(e))
        _close_index(
            index_name=index_name, data_store=es, timeline_id=timeline_id)
        raise

    except (RuntimeError, ImportError, NameError, UnboundLocalError,
            RequestError) as e:
        _set_timeline_status(timeline_id, status='fail', error_msg=str(e))
        _close_index(
            index_name=index_name, data_store=es, timeline_id=timeline_id)
        raise

    except Exception as e:  # pylint: disable=broad-except
        # Mark the searchindex and timelines as failed and exit the task
        error_msg = traceback.format_exc()
        _set_timeline_status(timeline_id, status='fail', error_msg=error_msg)
        logger.error('Error: {0!s}\n{1:s}'.format(e, error_msg))
        _close_index(
            index_name=index_name, data_store=es, timeline_id=timeline_id)
        return None

    message = 'Index timeline [{0:s}] to index [{1:s}] (source: {2:s})'
    logger.info(message.format(timeline_name, index_name, source_type))

    try:
        psort_path = current_app.config['PSORT_PATH']
    except KeyError:
        psort_path = 'psort.py'

    cmd = [
        psort_path, '-o', 'elastic_ts', file_path, '--server', elastic_server,
        '--port', str(elastic_port), '--status_view', 'none',
        '--index_name', index_name,
    ]

    if mappings_file_path:
        cmd.extend(['--elastic_mappings', mappings_file_path])

    if timeline_id:
        cmd.extend(['--timeline_identifier', str(timeline_id)])

    elastic_username = current_app.config.get('ELASTIC_USER', '')
    if elastic_username:
        cmd.extend(['--elastic_user', elastic_username])

    elastic_password = current_app.config.get('ELASTIC_PASSWORD', '')
    if elastic_password:
        cmd.extend(['--elastic_password', elastic_password])

    elastic_ssl = current_app.config.get('ELASTIC_SSL', False)
    if elastic_ssl:
        cmd.extend(['--use_ssl'])


    psort_memory = current_app.config.get('PLASO_UPPER_MEMORY_LIMIT', '')
    if psort_memory:
        cmd.extend(['--process_memory_limit', str(psort_memory)])

    # Run psort.py
    try:
        subprocess.check_output(
            cmd, stderr=subprocess.STDOUT, encoding='utf-8')
    except subprocess.CalledProcessError as e:
        # Mark the searchindex and timelines as failed and exit the task
        _set_timeline_status(timeline_id, status='fail', error_msg=e.output)
        _close_index(
            index_name=index_name, data_store=es, timeline_id=timeline_id)
        return e.output

    # Mark the searchindex and timelines as ready
    _set_timeline_status(timeline_id, status='ready')

    return index_name


@celery.task(track_started=True, base=SqlAlchemyTask)
def run_csv_jsonl(
        file_path, events, timeline_name, index_name, source_type, timeline_id):
    """Create a Celery task for processing a CSV or JSONL file.

    Args:
        file_path: Path to the JSON or CSV file.
        events: A string with the events.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.
        source_type: Type of file, csv or jsonl.
        timeline_id: ID of the timeline object this data belongs to.

    Returns:
        Name (str) of the index.
    """
    if events:
        file_handle = io.StringIO(events)
        source_type = 'jsonl'
    else:
        file_handle = codecs.open(
            file_path, 'r', encoding='utf-8', errors='replace')

    event_type = 'generic_event'  # Document type for Elasticsearch
    validators = {
        'csv': read_and_validate_csv,
        'jsonl': read_and_validate_jsonl,
    }
    read_and_validate = validators.get(source_type)

    # Log information to Celery
    logger.info(
        'Index timeline [{0:s}] to index [{1:s}] (source: {2:s})'.format(
            timeline_name, index_name, source_type))

    mappings = None
    mappings_file_path = current_app.config.get('GENERIC_MAPPING_FILE', '')
    if os.path.isfile(mappings_file_path):
        try:
            with open(mappings_file_path, 'r') as mfh:
                mappings = json.load(mfh)

                if not isinstance(mappings, dict):
                    raise RuntimeError(
                        'Unable to create mappings, the mappings are not a '
                        'dict, please look at the file: {0:s}'.format(
                            mappings_file_path))
        except (json.JSONDecodeError, IOError):
            logger.error('Unable to read in mapping', exc_info=True)

    es = ElasticsearchDataStore(
        host=current_app.config['ELASTIC_HOST'],
        port=current_app.config['ELASTIC_PORT'])

    # Reason for the broad exception catch is that we want to capture
    # all possible errors and exit the task.
    final_counter = 0
    error_msg = ''
    error_count = 0
    try:
        es.create_index(
            index_name=index_name, doc_type=event_type, mappings=mappings)
        for event in read_and_validate(file_handle):
            es.import_event(
                index_name, event_type, event, timeline_id=timeline_id)
            final_counter += 1

        # Import the remaining events
        results = es.flush_queued_events()

        error_container = results.get('error_container', {})
        error_msg = get_import_errors(
            error_container=error_container,
            index_name=index_name,
            total_count=results.get('total_events', 0))

    except errors.DataIngestionError as e:
        _set_timeline_status(timeline_id, status='fail', error_msg=str(e))
        _close_index(
            index_name=index_name, data_store=es, timeline_id=timeline_id)
        raise

    except (RuntimeError, ImportError, NameError, UnboundLocalError,
            RequestError) as e:
        _set_timeline_status(timeline_id, status='fail', error_msg=str(e))
        _close_index(
            index_name=index_name, data_store=es, timeline_id=timeline_id)
        raise

    except Exception as e:  # pylint: disable=broad-except
        # Mark the searchindex and timelines as failed and exit the task
        error_msg = traceback.format_exc()
        _set_timeline_status(timeline_id, status='fail', error_msg=error_msg)
        _close_index(
            index_name=index_name, data_store=es, timeline_id=timeline_id)
        logger.error('Error: {0!s}\n{1:s}'.format(e, error_msg))
        return None

    if error_count:
        logger.info(
            'Index timeline: [{0:s}] to index [{1:s}] - {2:d} out of {3:d} '
            'events imported (in total {4:d} errors were discovered) '.format(
                timeline_name, index_name, (final_counter - error_count),
                final_counter, error_count))
    else:
        logger.info(
            'Index timeline: [{0:s}] to index [{1:s}] - {2:d} '
            'events imported.'.format(timeline_name, index_name, final_counter))

    # Set status to ready when done
    _set_timeline_status(timeline_id, status='ready', error_msg=error_msg)

    return index_name


@celery.task(track_started=True)
def find_data_task(
        rule_name, sketch_id, start_date, end_date,
        timeline_ids=None, parameters=None):
    """Runs a task to find out if data exists in a dataset.

    Args:
        rule_name (str): A rule names to run.
        sketch_id (int): Sketch identifier.
        start_date (str): A string with an ISO formatted timestring for the
            start date of the data search.
        end_date (str): A string with an ISO formatted timestring for the
            end date of the data search.
        timeline_ids (list): An optional list of integers for the timelines
            within the the sketch to limit the data search to. If not provided
            all timelines are searched.
        parameters (dict): An optional dict with key/value pairs of parameters
            and their values, used for filling in regular expressions.

    Returns:
        A dict with the key value being the rule name used and the value
        as a tuple with two items, boolean whether data was found and a
        reason string.
    """
    results = {}
    data_finder_path = current_app.config.get('DATA_FINDER_PATH')
    if not data_finder_path:
        logger.error(
            'Unable to find data, missing data finder path in the '
            'configuration file.')
        return results

    if not os.path.isfile(data_finder_path):
        logger.error(
            'Unable to read data finder rules, the file does not exist, '
            'please verify that the path in DATA_FINDER_PATH variable is '
            'correct and points to a readable file.')
        return results

    data_finder_dict = {}
    with open(data_finder_path, 'r') as fh:
        try:
            data_finder_dict = yaml.safe_load(fh)
        except yaml.parser.ParserError:
            logger.error(
                'Unable to read in YAML config file', exc_info=True)
            return results

    if rule_name not in data_finder_dict:
        results[rule_name] = (False, 'Rule not defined')
        return results

    data_finder = datafinder.DataFinder()
    data_finder.set_start_date(start_date)
    data_finder.set_end_date(end_date)
    data_finder.set_parameters(parameters)
    data_finder.set_rule(data_finder_dict.get(rule_name))
    data_finder.set_timeline_ids(timeline_ids)

    sketch = Sketch.query.get(sketch_id)
    indices = set()
    for timeline in sketch.active_timelines:
        if timeline.id not in timeline_ids:
            continue
        indices.add(timeline.searchindex.index_name)

    data_finder.set_indices(list(indices))

    results[rule_name] = data_finder.find_data()
    return results


def run_data_finder(
        rule_names, sketch_id, start_date, end_date,
        timeline_ids=None, parameters=None):
    """Runs a task to find out if data exists in a dataset.

    Args:
        rule_names (list): A list of rule names to run.
        sketch_id (int): Sketch identifier.
        start_date (str): A string with an ISO formatted timestring for the
            start date of the data search.
        end_date (str): A string with an ISO formatted timestring for the
            end date of the data search.
        timeline_ids (list): An optional list of integers for the timelines
            within the the sketch to limit the data search to. If not provided
            all timelines are searched.
        parameters (dict): An optional dict with key/value pairs of parameters
            and their values, used for filling in regular expressions.

    Returns:
        Celery task object.
    """
    task_group = group(find_data_task.s(
        rule_name=x, sketch_id=sketch_id, start_date=start_date,
        end_date=end_date, timeline_ids=timeline_ids,
        parameters=parameters) for x in rule_names)
    return task_group
