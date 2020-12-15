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
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Text

import configparser
import logging
import os
import requests

from google.auth.transport import requests as auth_requests

from . import client
from . import cli_input
from . import credentials as ts_credentials
from . import crypto


logger = logging.getLogger('timesketch_api.config_assistance')


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

    CONFIG_ORDERING = {
        'host_uri': 1,
        'auth_mode': 2,
        'username': 3,
        'client_id': 4,
        'client_secret': 5,
        'password': 6,
    }

    CONFIG_HINTS = {
        'host_uri': 'URL of the Timesketch server',
        'username': 'The username of the Timesketch user',
        'password': 'Password of the chosen user.',
        'auth_mode': (
            'Authentication mode, valid choices are: "userpass" '
            '(user/pass) or "oauth"'),
        'client_id': 'OAUTH Client identification.',
        'client_secret': 'The OAUTH client secret',
    }

    def __init__(self):
        """Initialize the configuration assistant."""
        self._config = {}

    @property
    def parameters(self) -> List[Text]:
        """Return a list of configured parameters."""
        return self._config.keys()

    @property
    def missing(self) -> List[Text]:
        """Return a list of missing parameters."""
        return self.get_missing_config()

    def get_config(self, name: Text) -> Any:
        """Returns a value for a given config.

        Args:
            name (str): the name of the config value to retrieve.

        Raises:
            KeyError: if the config does not exist.
        """
        return self._config[name]

    def get_client(
            self, token_password: Optional[Text] = '') -> Optional[
                client.TimesketchApi]:
        """Returns a Timesketch API client if possible.

        Args:
            token_password (str): an optional password to decrypt
                the credential token file.
        """
        if self.missing:
            return None

        auth_mode = self._config.get('auth_mode', 'userpass')
        # TODO: Remove shortly, temporary due to change of
        # 'timesketch' to 'userpass'
        if auth_mode == 'timesketch':
            auth_mode = 'userpass'

        file_path = self._config.get('token_file_path', '')
        credential_storage = crypto.CredentialStorage(file_path=file_path)
        credentials = credential_storage.load_credentials(
            config_assistant=self, password=token_password)

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

    def get_missing_config(self) -> List[Text]:
        """Returns a list of configuration parameters that are missing.

        Returns:
            A list of parameters that are missing from the config object.
        """
        needed_set = self.CLIENT_NEEDED
        auth_mode = self._config.get('auth_mode', '')
        if auth_mode.startswith('oauth'):
            needed_set = needed_set.union(self.OAUTH_CLIENT_NEEDED)
        configured_set = set(self._config.keys())
        return sorted(
            list(needed_set.difference(configured_set)),
            key=lambda x: self.CONFIG_ORDERING.get(x, 100))

    def has_config(self, name: Text) -> bool:
        """Returns a boolean indicating whether a config parameter is set.

        Args:
            name (str): the name of the configuration.

        Returns:
            bool: whether the object has been set or not.
        """
        return name.lower() in self._config

    def load_config_file(
            self, config_file_path: Optional[Text] = '',
            section: Optional[Text] = 'timesketch'):
        """Load the config from file.

        Args:
            config_file_path (str): Full path to the configuration file,
                if not supplied the default path will be used, which is
                the file RC_FILENAME inside the user's home directory.
            section (str): The configuration section to read from. This
                is optional and defaults to timesketch. This can be
                useful if you have mutiple Timesketch servers to connect to,
                with each one of them having a separate section in the config
                file.

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
        except configparser.MissingSectionHeaderError as exc:
            raise IOError(
                'Unable to parse config file') from exc

        if not files_read:
            logger.warning('No config read')
            return

        if not section:
            section = 'timesketch'

        if section not in config.sections():
            logger.warning('No %s section in the config', section)
            return

        timesketch_config = config[section]
        for name, value in timesketch_config.items():
            self.set_config(name, value)

    def load_config_dict(self, config_dict: Dict[Text, Text]):
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

    def save_config(
            self, file_path: Optional[Text] = '',
            section: Optional[Text] = 'timesketch',
            token_file_path: Optional[Text] = ''):
        """Save the current config to a file.

        Args:
            file_path (str): A full path to the location where the
                configuration file is to be stored. If not provided the
                default location will be used.
            section (str): The configuration section to write to. This
                is optional and defaults to timesketch. This can be
                useful if you have mutiple Timesketch servers to connect to,
                with each one of them having a separate section in the config
                file.
            token_file_path (str): Optional path to the location of the token
                file.
        """
        if not file_path:
            home_path = os.path.expanduser('~')
            file_path = os.path.join(home_path, self.RC_FILENAME)

        config = configparser.ConfigParser()

        if not os.path.isfile(file_path):
            fw = open(file_path, 'a')
            fw.close()

        # Read in other sections in the config file as well.
        try:
            _ = config.read([file_path])
        except configparser.MissingSectionHeaderError:
            pass

        # TODO: Remove this, temporary here to transition from the use of
        # timesketch to the auth mode of userpass.
        auth_mode = self._config.get('auth_mode', 'userpass')
        if auth_mode == 'timesketch':
            auth_mode = 'userpass'

        config[section] = {
            'host_uri': self._config.get('host_uri'),
            'username': self._config.get('username'),
            'verify': self._config.get('verify', True),
            'client_id': self._config.get('client_id', ''),
            'client_secret': self._config.get('client_secret', ''),
            'auth_mode': auth_mode,
        }
        if token_file_path:
            config[section]['token_file_path'] = token_file_path

        if 'cred_key' in self._config:
            cred_key = self._config.get('cred_key')
            if isinstance(cred_key, bytes):
                cred_key = cred_key.decode('utf-8')
            config[section]['cred_key'] = cred_key

        with open(file_path, 'w') as fw:
            config.write(fw)

    def set_config(self, name: Text, value: Any):
        """Sets a given config item with a value.

        Args:
          name (str): the name of the configuration value to be set.
          value (object): the value of the configuration object.
        """
        self._config[name.lower()] = value


def get_client(
        config_dict: Optional[Dict[Text, Any]] = None,
        config_path: Optional[Text] = '',
        config_section: Optional[Text] = 'timesketch',
        token_password: Optional[Text] = '',
        confirm_choices: Optional[bool] = False
        ) -> Optional[client.TimesketchApi]:
    """Returns a Timesketch API client using the configuration assistant.

    Args:
        config_dict (dict): optional dict that will be used to configure
            the client.
        config_path (str): optional path to the configuration file, if
            not supplied a default path will be used.
        config_section (str): The configuration section to read from. This
            is optional and defaults to timesketch. This can be
            useful if you have mutiple Timesketch servers to connect to,
            with each one of them having a separate section in the config
            file.
        token_password (str): an optional password to decrypt
            the credential token file.
        confirm_choices (bool): an optional bool. if set to the user is given
            a choice to change the value for all already configured parameters.
            This defaults to False.

    Returns:
        A timesketch client (TimesketchApi) or None if not possible.
    """
    assistant = ConfigAssistant()
    try:
        assistant.load_config_file(config_path, section=config_section)
        if config_dict:
            assistant.load_config_dict(config_dict)
    except IOError as e:
        logger.error('Unable to load the config file, is it valid?')
        logger.error('Error: %s', e)

    try:
        configure_missing_parameters(
            config_assistant=assistant,
            token_password=token_password,
            confirm_choices=confirm_choices,
            config_section=config_section)
        return assistant.get_client(token_password=token_password)
    except (RuntimeError, requests.ConnectionError) as e:
        logger.error(
            'Unable to connect to the Timesketch server, are you '
            'connected to the network? Is the timesketch server '
            'running and accessible from your host? The error '
            'message is %s', e)
    except IOError as e:
        logger.error('Unable to get a client, with error: %s', e)
        logger.error(
            'If the issue is in the credentials then one solution '
            'is to remove the ~/.timesketch.token file and the '
            'credential section in ~/.timesketchrc or to remove '
            'both files. Or you could have supplied a wrong '
            'password to undecrypt the token file.')


def configure_missing_parameters(
        config_assistant: ConfigAssistant,
        token_password: Optional[Text] = '',
        confirm_choices: Optional[bool] = False,
        config_section: Optional[Text] = 'timesketch'):
    """Fill in missing configuration for a config assistant.

    This function will take in a configuration assistant object and check
    whether it is not fully configured. If it isn't it will ask the user
    to fill in the missing details.

    It will also check to see whether a password has been set if the auth
    is username/password and ask for a password to store credentials.

    Args:
        config_assistant (ConfigAssistant): a config assistant that might
            not be fully configured.
        token_password (str): an optional password to decrypt
            the credential token file.
        confirm_choices (bool): an optional bool. if set to the user is given
            a choice to change the value for all already configured parameters.
            This defaults to False.
        config_section (str): The configuration section to read from. This
            is optional and defaults to timesketch. This can be
            useful if you have mutiple Timesketch servers to connect to,
            with each one of them having a separate section in the config
            file.
    """
    just_configured = []

    for field in config_assistant.missing:
        hint = config_assistant.CONFIG_HINTS.get(field, '')
        value = cli_input.ask_question(
            f'What is the value for <{field}> ({hint})', input_type=str)
        if value:
            config_assistant.set_config(field, value)
            just_configured.append(field)

    if config_assistant.missing:
        # We still have unanswered questions.
        return configure_missing_parameters(config_assistant, token_password)

    if confirm_choices:
        # Go through prior answered parameters.
        for field in config_assistant.parameters:
            if field in ('cred_key', 'verify', 'username'):
                continue
            # We don't want to re-ask the user about the field they just
            # configured.
            if field in just_configured:
                continue

            answer = config_assistant.get_config(field)
            change = cli_input.confirm_choice(
                f'Want to change the value for "{field}" [{answer}]',
                default=False, abort=False)
            if not change:
                continue
            hint = config_assistant.CONFIG_HINTS.get(field, '')
            value = cli_input.ask_question(
                f'What is the value for <{field}> ({hint})', input_type=str)
            if value:
                config_assistant.set_config(field, value)

    try:
        file_path = config_assistant.get_config('token_file_path')
    except KeyError:
        file_path = ''
    config_assistant.save_config(
        section=config_section, token_file_path=file_path)
    credential_storage = crypto.CredentialStorage(file_path=file_path)
    credentials = credential_storage.load_credentials(
        config_assistant=config_assistant, password=token_password)

    # Check if we are using username/password and we don't have credentials
    # saved.
    auth_mode = config_assistant.get_config('auth_mode')
    if auth_mode != 'userpass':
        return None

    choice = False
    if credentials and confirm_choices:
        choice = cli_input.confirm_choice(
            'Want to change credentials?',
            default=False, abort=False)

    if not choice and credentials:
        return None

    username = config_assistant.get_config('username')
    if choice:
        value = cli_input.ask_question(
            'What is the username?',
            input_type=str, default=username)
        if value:
            username = value
            config_assistant.set_config('username', value)

    password = cli_input.ask_question(
        'Password for user {0:s}'.format(username), input_type=str,
        hide_input=True, default='***')
    credentials = ts_credentials.TimesketchPwdCredentials()
    credentials.credential = {
        'username': username,
        'password': password
    }
    cred_storage = crypto.CredentialStorage(file_path=file_path)
    cred_storage.save_credentials(
        credentials, password=token_password,
        config_assistant=config_assistant)
    config_assistant.save_config(
        section=config_section, token_file_path=file_path)
    return None
