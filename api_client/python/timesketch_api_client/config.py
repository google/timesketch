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
"""Timesketch API library for reading/parsing configs."""
from __future__ import unicode_literals

import configparser
import logging
import os

from google.auth.transport import requests as auth_requests

from . import client
from . import crypto


logger = logging.getLogger('config_assistance_api')


def get_client(config_dict=None, config_path=''):
    """Returns a Timesketch API client using the configuration assistant.

    Args:
        config_dict (dict): optional dict that will be used to configure
            the client.
        config_path (str): optional path to the configuration file, if
            not supplied a default path will be used.
    """
    assistant = ConfigAssistant()
    assistant.load_config_file(config_path)
    if config_dict:
        assistant.load_config_dict(config_dict)
    return assistant.get_client()


class ConfigAssistant:
    """A simple assistant that helps with setting up a Timesketch API client.

    This assistant can read and save configs to a file. It also maintains
    a state about what config has been passed to it, to assist possible
    UIs to understand what is missing in order to setup a Timesketch API
    client.
    """

    # The name of the default config file.
    RC_FILENAME = '.timesketchrc'

    # The needed items to configure a client.
    CLIENT_NEEDED = frozenset([
        'host_uri',
        'username',
        'auth_mode',
    ])
    OAUTH_CLIENT_NEEDED = frozenset([
        'client_id',
        'client_secret',
    ])

    def __init__(self):
        """Initialize the configuration assistant."""
        self._config = {}

    @property
    def parameters(self):
        """Return a list of configured parameters."""
        return self._config.keys()

    @property
    def missing(self):
        """Return a list of missing parameters."""
        return self.get_missing_config()

    def get_config(self, name):
        """Returns a value for a given config.

        Args:
            name (str): the name of the config value to retrieve.

        Raises:
            KeyError: if the config does not exist.
        """
        return self._config[name]

    def get_client(self, token_password=''):
        """Returns a Timesketch API client if possible.

        Args:
            token_password (str): an optional password to decrypt
                the credential token file.
        """
        if self.missing:
            return None

        auth_mode = self._config.get('auth_mode', 'timesketch')
        credential_storage = crypto.CredentialStorage()
        credentials = credential_storage.load_credentials(
            config_assistant=self, password=password)

        if auth_mode.startswith('oauth'):
            if not credentials:
                return client.TimesketchApi(
                    host_uri=self._config.get('host_uri'),
                    username=self._config.get('username'),
                    password=self._config.get('password', ''),
                    verify=self._config.get('verify', True),
                    client_id=self._config.get('client_id', ''),
                    client_secret=self._config.get('client_secret', ''),
                    auth_mode=auth_mode,
                )

            ts = client.TimesketchApi(
                host_uri=self._config.get('host_uri'),
                username=self._config.get('username'),
                auth_mode=auth_mode,
                create_session=False)
            ts.set_credentials(credentials)
            session = auth_requests.AuthorizedSession(credentials.credential)
            try:
                ts.refresh_oauth_token()
            except auth_requests.RefreshError as e:
                logger.error(
                    'Unable to refresh credentials, with error: %s', e)
                return None
            session = ts.authenticate_oauth_session(session)
            ts.set_session(session)
            return ts

        if credentials:
            username = credentials.credential.get(
                'username', self._config.get('username', ''))
            password = credentials.credential.get(
                'password', self._config.get('password', ''))
        else:
            username = self._config.get('username', '')
            password = self._config.get('password', '')

        return client.TimesketchApi(
            host_uri=self._config.get('host_uri'),
            username=username,
            password=password,
            verify=self._config.get('verify', True),
            client_id=self._config.get('client_id', ''),
            client_secret=self._config.get('client_secret', ''),
            auth_mode=auth_mode,
        )

    def get_missing_config(self):
        """Returns a list of configuration parameters that are missing.

        Returns:
            A list of parameters that are missing from the config object.
        """
        needed_set = self.CLIENT_NEEDED
        auth_mode = self._config.get('auth_mode', '')
        if auth_mode.startswith('oauth'):
            needed_set = needed_set.union(self.OAUTH_CLIENT_NEEDED)

        configured_set = set(self._config.keys())
        return list(needed_set.difference(configured_set))

    def has_config(self, name):
        """Returns a boolean indicating whether a config parameter is set.

        Args:
            name (str): the name of the configuration.

        Returns:
            bool: whether the object has been set or not.
        """
        return name.lower() in self._config

    def load_config_file(self, config_file_path=''):
        """Load the config from file.

        Args:
            config_file_path (str): Full path to the configuration file,
                if not supplied the default path will be used, which is
                the file RC_FILENAME inside the user's home directory.

        Raises:
          IOError if the file does not exist or config does not load.
        """
        if config_file_path:
            if not os.path.isfile(config_file_path):
                error_msg = (
                    'Unable to load config file, file {0:s} does not '
                    'exist.').format(config_file_path)
                logger.error(error_msg)
                raise IOError(error_msg)
        else:
            home_path = os.path.expanduser('~')
            config_file_path = os.path.join(home_path, self.RC_FILENAME)

        if not os.path.isfile(config_file_path):
            fw = open(config_file_path, 'a')
            fw.close()

        config = configparser.ConfigParser()
        try:
            files_read = config.read([config_file_path])
        except configparser.MissingSectionHeaderError as e:
            raise IOError(
                'Unable to parse config file, with error: {0!s}'.format(e))

        if not files_read:
            logger.warning('No config read')
            return

        if 'timesketch' not in config.sections():
            logger.warning('No timesketch section in the config')
            return

        timesketch_config = config['timesketch']
        for name, value in timesketch_config.items():
            self.set_config(name, value)

    def load_config_dict(self, config_dict):
        """Loads configuration from a dictionary.

        Only loads the config items that are needed for the client,
        other keys are ignored in the dict object.

        Args:
            config_dict (dict): dict object with configuration.
        """
        fields = list(self.CLIENT_NEEDED)
        fields.extend(list(self.OAUTH_CLIENT_NEEDED))

        for key, value in config_dict.items():
            key = key.lower()
            if key not in fields:
                continue

            if not value:
                continue
            self.set_config(key, value)

    def save_config(self, file_path=''):
        """Save the current config to a file.

        Args:
            file_path (str): A full path to the location where the
                configuration file is to be stored. If not provided the
                default location will be used.
        """
        if not file_path:
            home_path = os.path.expanduser('~')
            file_path = os.path.join(home_path, self.RC_FILENAME)

        config = configparser.ConfigParser()
        config['timesketch'] = {
            'host_uri': self._config.get('host_uri'),
            'username': self._config.get('username'),
            'verify': self._config.get('verify', True),
            'client_id': self._config.get('client_id', ''),
            'client_secret': self._config.get('client_secret', ''),
            'auth_mode': self._config.get('auth_mode', 'timesketch')
        }

        if 'cred_key' in self._config:
            cred_key = self._config.get('cred_key')
            if isinstance(cred_key, bytes):
                cred_key = cred_key.decode('utf-8')
            config['timesketch']['cred_key'] = cred_key

        with open(file_path, 'w') as fw:
            config.write(fw)

    def set_config(self, name, value):
        """Sets a given config item with a value.

        Args:
          name (str): the name of the configuration value to be set.
          value (object): the value of the configuration object.
        """
        self._config[name.lower()] = value
