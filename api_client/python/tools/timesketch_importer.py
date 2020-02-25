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
"""A simple frontend to the Timesketch data importer."""
from __future__ import unicode_literals

import argparse
import getpass
import logging
import os
import sys

from typing import Dict

import yaml

from timesketch_api_client import client
from timesketch_api_client import importer
from timesketch_api_client import sketch


logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))


def get_api_client(
        host: str, username: str, password: str = '', client_id: str = '',
        client_secret: str = '', run_local: bool = False
        ) -> client.TimesketchApi:
    """Returns a Timesketch API client.

    Args:
        host (str): the Timesketch host.
        username (str): the username to authenticate with.
        password (str): optional used if OAUTH is not the authentication
                        mechanism.
        client_id (str): if OAUTH is used then a client ID needs to be set.
        client_secret (str): if OAUTH is used then a client secret needs to be
                             set.
        run_local (bool): if OAUTH is used to authenticate and set to True
                          then the authentication URL is printed on screen
                          instead of starting a web server, this suits well
                          if the connection is over a SSH connection for
                          instance.

    Raises:
        TypeError: If a non supported authentication mode is passed in.

    Returns:
        A Timesketch API client object.
    """
    if run_local and client_secret:
        auth_mode = 'oauth_local'
    elif client_secret:
        auth_mode = 'oauth'
    elif password:
        auth_mode = 'timesketch'
    else:
        raise TypeError(
            'Neither password nor client secret provided, unable '
            'to authenticate')

    if not host.startswith('http'):
        host = 'https://{0:s}'.format(host)

    api_client = client.TimesketchApi(
        host_uri=host, username=username, password=password,
        client_id=client_id, client_secret=client_secret, auth_mode=auth_mode)

    return api_client


def upload_file(
        my_sketch: sketch.Sketch, config_dict: Dict[str, any],
        file_path: str) -> str:
    """Uploads a file to Timesketch.

    Args:
        my_sketch (sketch.Sketch): a sketch object to point to the sketch the
            data will be imported to.
        config_dict (dict): dict with settings for the importer.
        file_path (str): the path to the file to upload.

    Returns:
        A string with results (whether successful or not).
    """
    if not my_sketch or not hasattr(my_sketch, 'id'):
        return 'Sketch needs to be set'

    _, _, file_extension = file_path.rpartition('.')
    if file_extension.lower() not in ('plaso', 'csv', 'jsonl'):
        return (
            'File needs to have one of the following extensions: '
            '.plaso, .csv, .jsonl (not {0:s})').format(file_extension.lower())

    with importer.ImportStreamer() as streamer:
        streamer.set_sketch(my_sketch)

        format_string = config_dict.get('message_format_string')
        if format_string:
            streamer.set_message_format_string(format_string)
        timeline_name = config_dict.get('timeline_name')
        if timeline_name:
            streamer.set_timeline_name(timeline_name)
        index_name = config_dict.get('index_name')
        if index_name:
            streamer.set_index_name(index_name)
        time_desc = config_dict.get('timestamp_description')
        if time_desc:
            streamer.set_timestamp_description(time_desc)

        entry_threshold = config_dict.get('entry_threshold')
        if entry_threshold:
            streamer.set_entry_threshold(entry_threshold)
        size_threshold = config_dict.get('size_threshold')
        if size_threshold:
            streamer.set_filesize_threshold(size_threshold)

        streamer.add_file(file_path)

    return 'File got successfully uploaded to sketch: {0:d}'.format(
        my_sketch.id)


if __name__ == '__main__':
    logger = logging.getLogger('timesketch_importer')

    argument_parser = argparse.ArgumentParser(
        description='A tool to upload data to Timesketch, using the API.')

    auth_group = argument_parser.add_argument_group('Authentication Arguments')
    auth_group.add_argument(
        '-u', '--user', '--username', action='store', dest='username',
        type=str, help='The username of the Timesketch user.')
    auth_group.add_argument(
        '-p', '--password', '--pwd', action='store', type=str, dest='password',
        help=(
            'If authenticated with password, provide the password on the CLI. '
            'If neither password is provided nor a password prompt an OAUTH '
            'connection is assumed.'))
    auth_group.add_argument(
        '--pwd-prompt', '--pwd_prompt', action='store_true', default=False,
        dest='pwd_prompt', help='Prompt for password.')
    auth_group.add_argument(
        '--client-secret', '--client_secret', action='store', type=str,
        default='', dest='client_secret', help='OAUTH client secret.')
    auth_group.add_argument(
        '--client-id', '--client_id', action='store', type=str, default='',
        dest='client_id', help='OAUTH client ID.')
    auth_group.add_argument(
        '--run_local', '--run-local', action='store_true', dest='run_local',
        help=(
            'If OAUTH is used to authenticate and the connection is over '
            'SSH then it is recommended to set this option. When set an '
            'authentication URL is prompted on the screen, requiring a '
            'copy/paste into a browser to complete the OAUTH dance.'))

    config_group = argument_parser.add_argument_group(
        'Configuration Arguments')
    config_group.add_argument(
        '--config-file', '--config_file', action='store', type=str,
        default='', metavar='FILEPATH', dest='config_file', help=(
            'Path to a YAML config file that can be used to store '
            'all parameters to this tool (except this path)'))
    config_group.add_argument(
        '--host', '--hostname', '--host-uri', '--host_uri', dest='host',
        type=str, default='', action='store',
        help='The URI to the Timesketch instance')
    config_group.add_argument(
        '--format_string', '--format-string', type=str, action='store',
        dest='format_string', default='', help=(
            'Formatting string for the message field. If there is no message '
            'field in the input data a message string can be composed using '
            'a format string.'))
    config_group.add_argument(
        '--timeline_name', '--timeline-name', action='store', type=str,
        dest='timeline_name', default='', help=(
            'String that will be used as the timeline name.'))
    config_group.add_argument(
        '--index-name', '--index_name', action='store', type=str, default='',
        dest='index_name', help=(
            'If the data should be imported into a specific timeline the '
            'index name needs to be provided, otherwise a new index will '
            'be generated.'))
    config_group.add_argument(
        '--timestamp_description', '--timestamp-description', '--time-desc',
        '--time_desc', action='store', type=str, default='', dest='time_desc',
        help='Value for the timestamp_description field.')
    config_group.add_argument(
        '--threshold_entry', '--threshold-entry', '--entries', action='store',
        type=int, default=0, dest='entry_threshold',
        help=(
            'How many entries should be buffered up before being '
            'sent to server.'))
    config_group.add_argument(
        '--threshold_size', '--threshold-size', '--filesize', action='store',
        type=int, default=0, dest='size_threshold',
        help=(
            'For binary file transfer, how many bytes should be transferred '
            'per chunk.'))
    config_group.add_argument(
        '--sketch_id', '--sketch-id', type=int, default=0, dest='sketch_id',
        action='store', help=(
            'The sketch ID to store the timeline in, if no sketch ID is '
            'provided a new sketch will be created.'))

    argument_parser.add_argument(
        'path', action='store', type=str, help=(
            'Path to the file that is to be imported.'))

    options = argument_parser.parse_args()
    config_options = {}

    if options.config_file:
        if not os.path.isfile(options.config_file):
            logger.error('Config file does not exist ({0:s})'.format(
                options.config_file))
            sys.exit(1)
        with open(options.config_file, 'r') as fh:
            config_options = yaml.safe_load(fh)

    if not os.path.isfile(options.path):
        logger.error('Path {0:s} is not valid, unable to continue.')
        sys.exit(1)

    conf_host = options.host or config_options.get('host', '')
    if not conf_host:
        logger.error('Hostname for Timesketch server must be set.')
        sys.exit(1)

    conf_password = options.password or config_options.get('password', '')
    conf_pwd_prompt = options.pwd_prompt or config_options.get(
        'pwd_prompt', False)
    if not conf_password and conf_pwd_prompt:
        conf_password = getpass.getpass('Type in the password: ')

    conf_client_id = options.client_id or config_options.get('client_id', '')
    conf_client_secret = options.client_secret or config_options.get(
        'client_secret', '')
    conf_username = options.username or config_options.get('username', '')
    conf_run_local = options.run_local or config_options.get(
        'run_local', False)

    logger.info('Creating a client.')
    ts_client = get_api_client(
        host=conf_host, username=conf_username, password=conf_password,
        client_id=conf_client_id, client_secret=conf_client_secret,
        run_local=conf_run_local)

    if not ts_client:
        logger.error('Unable to create a Timesketch API client, exiting.')
        sys.exit(1)

    logger.info('Client created.')
    sketch_id = options.sketch_id or config_options.get('sketch_id', 0)
    if sketch_id:
        sketch = ts_client.get_sketch(sketch_id)
    else:
        sketch = ts_client.create_sketch('New Sketch From Importer CLI')

    if not sketch:
        logger.error('Unable to get sketch ID: {0:d}'.format(sketch_id))
        sys.exit(1)

    conf_timeline_name = options.timeline_name or config_options.get(
        'timeline_name', 'unnamed_timeline_imported_from_importer')

    config = {
        'message_format_string': options.format_string or config_options.get(
            'format_string', ''),
        'timeline_name': conf_timeline_name,
        'index_name': options.index_name or config_options.get(
            'index_name', ''),
        'timestamp_description': options.time_desc or config_options.get(
            'timestamp_description', ''),
        'entry_threshold': options.entry_threshold or config_options.get(
            'entry_threshold', 0),
        'size_threshold': options.size_threshold or config_options.get(
            'size_threshold', 0),
    }

    logger.info('Uploading file.')
    result = upload_file(
        my_sketch=sketch, config_dict=config, file_path=options.path)
    logger.info(result)
