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

from timesketch_api_client import cli_input
from timesketch_api_client import credentials as ts_credentials
from timesketch_api_client import crypto
from timesketch_api_client import config
from timesketch_api_client import sketch
from timesketch_api_client import version as api_version
from timesketch_import_client import helper
from timesketch_import_client import importer
from timesketch_import_client import version as importer_version


logger = logging.getLogger('timesketch_importer.importer_frontend')


def configure_logger_debug():
    """Configure the logger to log debug logs."""
    logger.setLevel(logging.DEBUG)
    logger_formatter = logging.Formatter(
        '[%(asctime)s] %(name)s/%(levelname)s %(message)s '
        '<%(module)s/%(funcName)s>')
    for handler in logger.parent.handlers:
        handler.setFormatter(logger_formatter)


def configure_logger_default():
    """Configure the logger to only log information and above logs."""
    logger.setLevel(logging.INFO)
    logger_formatter = logging.Formatter(
        '[%(asctime)s] %(name)s/%(levelname)s %(message)s')
    for handler in logger.parent.handlers:
        handler.setFormatter(logger_formatter)


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
            '.plaso, .csv, '
            '.jsonl (not {0:s})').format(file_extension.lower())

    import_helper = helper.ImportHelper()
    import_helper.add_config_dict(config_dict)

    log_config_file = config_dict.get('log_config_file', '')
    if log_config_file:
        import_helper.add_config(log_config_file)

    with importer.ImportStreamer() as streamer:
        streamer.set_sketch(my_sketch)
        streamer.set_config_helper(import_helper)

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


def main(args=None):
    """The main function of the tool."""
    if args is None:
        args = sys.argv[1:]

    argument_parser = argparse.ArgumentParser(
        description='A tool to upload data to Timesketch, using the API.')

    argument_parser.add_argument(
        '--version', action='store_true', dest='show_version',
        help='Print version information')

    argument_parser.add_argument(
        '--debug', '--verbose', '-d', action='store_true', dest='show_debug',
        help='Make the logging more verbose to include debug logs.')

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
        '--cred-prompt', '--cred_prompt', '--token-password',
        '--token_password', '--token', action='store_true', default=False,
        dest='cred_prompt',
        help='Prompt for password to decrypt and encrypt credential file.')
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
        '--log-config-file', '--log_config_file', '--lc', action='store',
        type=str, default='', metavar='FILEPATH', dest='log_config_file',
        help=(
            'Path to a YAML config file that defines the config for parsing '
            'and setting up file parsing. By default formatter.yaml that '
            'comes with the importer will be used.'))
    config_group.add_argument(
        '--host', '--hostname', '--host-uri', '--host_uri', dest='host_uri',
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
        '--config_section', '--config-section', action='store', type=str,
        dest='config_section', default='', help=(
            'The config section in the RC file that will be used to '
            'define server information.'))
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
        'path', action='store', nargs='?', type=str, help=(
            'Path to the file that is to be imported.'))

    options = argument_parser.parse_args(args)

    if options.show_version:
        print('API Client Version: {0:s}'.format(api_version.get_version()))
        print('Importer Client Version: {0:s}'.format(
            importer_version.get_version()))
        sys.exit(0)

    if options.show_debug:
        configure_logger_debug()
    else:
        configure_logger_default()

    if not options.path:
        logger.error(
            'A valid file path needs to be provided, unable to continue.')
        sys.exit(1)

    if not os.path.isfile(options.path):
        logger.error('Path {0:s} is not valid, unable to continue.'.format(
            options.path))
        sys.exit(1)

    config_section = options.config_section
    assistant = config.ConfigAssistant()
    assistant.load_config_file(section=config_section)
    assistant.load_config_dict(vars(options))

    try:
        file_path = assistant.get_config('token_file_path')
    except KeyError:
        file_path = ''

    cred_storage = crypto.CredentialStorage(file_path=file_path)
    token_password = ''
    if options.cred_prompt:
        token_password = cli_input.ask_question(
            'Enter password to encrypt/decrypt credential file',
            input_type=str, hide_input=True)

    try:
        credentials = cred_storage.load_credentials(
            config_assistant=assistant, password=token_password)
    except IOError:
        logger.error(
            'Unable to decrypt the credential file')
        logger.debug(
            'Error details:', exc_info=True)
        logger.error(
            'If you\'ve forgotten the password you can delete '
            'the ~/.timesketch.token file and run the tool again.')
        sys.exit(1)

    conf_password = ''

    if credentials:
        if credentials.TYPE.lower() == 'oauth':
            assistant.set_config('auth_mode', 'oauth')
        elif credentials.TYPE.lower() == 'timesketch':
            assistant.set_config('auth_mode', 'timesketch')

    else:
        # Check whether we'll need to read password for timesketch
        # auth from the command line.
        if options.pwd_prompt:
            conf_password = getpass.getpass('Type in the password: ')
        else:
            conf_password = options.password

        if options.run_local:
            assistant.set_config('auth_mode', 'oauth_local')

        if options.client_secret:
            assistant.set_config('auth_mode', 'oauth')

        if conf_password:
            assistant.set_config('auth_mode', 'timesketch')

    if conf_password:
        credentials = ts_credentials.TimesketchPwdCredentials()
        credentials.credential = {
            'username': assistant.get_config('username'),
            'password': conf_password
        }
        logger.info('Saving Credentials.')
        cred_storage.save_credentials(
            credentials, password=token_password,
            file_path=file_path,
            config_assistant=assistant)

    # Gather all questions that are missing.
    config.configure_missing_parameters(
        config_assistant=assistant, token_password=token_password)

    logger.info('Creating a client.')
    ts_client = assistant.get_client(token_password=token_password)
    if not ts_client:
        logger.error('Unable to create a Timesketch API client, exiting.')
        sys.exit(1)

    logger.info('Client created.')
    logger.info('Saving TS config.')
    assistant.save_config(
        section=config_section, token_file_path=file_path)

    if ts_client.credentials:
        logger.info('Saving Credentials.')
        cred_storage.save_credentials(
            ts_client.credentials, password=token_password,
            file_path=file_path,
            config_assistant=assistant)

    sketch_id = options.sketch_id
    if sketch_id:
        my_sketch = ts_client.get_sketch(sketch_id)
    else:
        my_sketch = ts_client.create_sketch('New Sketch From Importer CLI')

    if not my_sketch:
        logger.error('Unable to get sketch ID: {0:d}'.format(sketch_id))
        sys.exit(1)

    filename = os.path.basename(options.path)
    default_timeline_name, _, _ = filename.rpartition('.')

    if options.timeline_name:
        conf_timeline_name = options.timeline_name
    else:
        conf_timeline_name = cli_input.ask_question(
            'What is the timeline name', input_type=str,
            default=default_timeline_name)

    config_dict = {
        'message_format_string': options.format_string,
        'timeline_name': conf_timeline_name,
        'index_name': options.index_name,
        'timestamp_description': options.time_desc,
        'entry_threshold': options.entry_threshold,
        'size_threshold': options.size_threshold,
        'log_config_file': options.log_config_file,
    }

    logger.info('Uploading file.')
    result = upload_file(
        my_sketch=my_sketch, config_dict=config_dict, file_path=options.path)
    logger.info(result)


if __name__ == '__main__':
    main()
