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
"""Timesketch API crypto storage library for OAUTH client."""
from __future__ import unicode_literals

import base64
import os
import getpass
import json
import logging
import stat

from cryptography import fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from google.oauth2 import credentials


logger = logging.getLogger('crypto_client_api')


class TimesketchCredentials:
    """Class to store and retrieve credentials for Timesketch."""

    # The type of credential object.
    TYPE = ''

    def __init__(self):
        """Initialize the credential object."""
        self._credential = None

    @property
    def credential(self):
        """Returns the credentials back."""
        return self._credential

    @credential.setter
    def credential(self, credential_obj):
        """Sets the credential object."""
        self._credential = credential_obj

    def serialize(self):
        """Return serialized bytes object."""
        data = self.to_bytes()
        type_string = bytes(self.TYPE, 'utf-8').rjust(10)[:10]

        return type_string + data

    def deserialize(self, data):
        """Deserialize a credential object from bytes.

        Args:
            data (bytes): serialized credential object.
        """
        type_data = data[:10]
        type_string = type_data.decode('utf-8').strip()
        if not self.TYPE.startswith(type_string):
            raise TypeError('Not the correct serializer.')

        self.from_bytes(data[10:])

    def to_bytes(self):
        """Convert the credential object into bytes for storage."""
        raise NotImplementedError

    def from_bytes(self, data):
        """Deserialize a credential object from bytes.

        Args:
            data (bytes): serialized credential object.
        """
        raise NotImplementedError


class TimesketchPwdCredentials(TimesketchCredentials):
    """Username and password credentials for Timesketch authentication."""

    TYPE = 'timesketch'

    def from_bytes(self, data):
        """Deserialize a credential object from bytes.

        Args:
            data (bytes): serialized credential object.

        Raises:
            TypeError: if the data is not in bytes.
        """
        if not isinstance(data, bytes):
            raise TypeError('Data needs to be bytes.')

        try:
            data_dict = json.loads(data.decode('utf-8'))
        except ValueError:
            raise TypeError('Unable to parse the byte string.')

        if not 'username' in data_dict:
            raise TypeError('Username is not set.')
        if not 'password' in data_dict:
            raise TypeError('Password is not set.')
        self._credential = data_dict

    def to_bytes(self):
        """Convert the credential object into bytes for storage."""
        if not self._credential:
            return b''

        data_string = json.dumps(self._credential)
        return bytes(data_string, 'utf-8')


class TimesketchOAuthCredentials(TimesketchCredentials):
    """OAUTH credentials for Timesketch authentication."""

    TYPE = 'oauth'

    def from_bytes(self, data):
        """Deserialize a credential object from bytes.

        Args:
            data (bytes): serialized credential object.

        Raises:
            TypeError: if the data is not in bytes.
        """
        if not isinstance(data, bytes):
            raise TypeError('Data needs to be bytes.')

        try:
            token_dict = json.loads(data.decode('utf-8'))
        except ValueError:
            raise TypeError('Unable to parse the byte string.')

        self._credential = credentials.Credentials(
            token=token_dict.get('token'),
            refresh_token=token_dict.get('_refresh_token'),
            id_token=token_dict.get('_id_token'),
            token_uri=token_dict.get('_token_uri'),
            client_id=token_dict.get('_client_id'),
            client_secret=token_dict.get('_client_secret')
        )

    def to_bytes(self):
        """Convert the credential object into bytes for storage."""
        if not self._credential:
            return b''

        cred_obj = self._credential
        data = {
            'token': cred_obj.token,
            '_scopes': getattr(cred_obj, '_scopes', []),
            '_refresh_token': getattr(cred_obj, '_refresh_token', ''),
            '_id_token': getattr(cred_obj, '_id_token', ''),
            '_token_uri': getattr(cred_obj, '_token_uri', ''),
            '_client_id': getattr(cred_obj, '_client_id', ''),
            '_client_secret': getattr(cred_obj, '_client_secret', ''),
        }
        if cred_obj.expiry:
            data['expiry'] = cred_obj.expiry.isoformat()
        data_string = json.dumps(data)

        return bytes(data_string, 'utf-8')


class CredentialStorage:
    """Class to store and retrieve stored credentials."""

    # The default filename of the token file.
    DEFAULT_CREDENTIAL_FILENAME = '.timesketch.token'

    # Length of the salt.
    SALT_LENGTH = 16

    def __init__(self):
        """Initialize the class."""
        self._user = getpass.getuser()
        home_path = os.path.expanduser('~')
        self._filepath = os.path.join(
            home_path, self.DEFAULT_CREDENTIAL_FILENAME)

    def _get_key(self, salt, password):
        """Returns an encryption key.

        Args:
            salt (bytes): a salt used during the encryption.
            password (bytes): the password used to decrypt/encrypt
                the message.

        Returns:
            Bytes with the encryption key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(
            kdf.derive(password))

    def set_filepath(self, file_path):
        """Set the filepath to the credential file."""
        if os.path.isfile(file_path):
            self._filepath = file_path

    def save_credentials(
            self, cred_obj, file_path='', password='', config_assistant=None):
        """Save credential data to a token file.

        This function will create an encrypted file
        in the user's home directory (~/.timesketch.token by default)
        that contains a stored copy of the credential object.

        Args:
            cred_obj (TimesketchCredentials): the credential
                object that is to be stored on disk.
            file_path (str): full path to the file storing the saved
                credentials.
            password (str): optional password to encrypt the
                credential file with. If not supplied a password
                will be generated.
            config_assistant (ConfigAssistant): optional configuration
                assistant object. Can be used to store the password to the
                credential file.
        """
        if not file_path:
            file_path = self._filepath

        if password:
            password = bytes(password, 'utf-8')
        else:
            password = fernet.Fernet.generate_key()
            if config_assistant:
                config_assistant.set_config('cred_key', password)
                config_assistant.save_config()

        if not os.path.isfile(file_path):
            logger.info('File does not exist, creating it.')

        salt = os.urandom(self.SALT_LENGTH)
        key = self._get_key(salt, password)
        crypto = fernet.Fernet(key)

        data = cred_obj.serialize()

        with open(file_path, 'wb') as fw:
            fw.write(salt)
            fw.write(crypto.encrypt(data))

        file_permission = stat.S_IREAD | stat.S_IWRITE
        os.chmod(file_path, file_permission)
        logger.info('Credentials saved to: %s', file_path)

    def load_credentials(
            self, file_path='', password='', config_assistant=None):
        """Load credentials from a file and return a credential object.

        Args:
            file_path (str): Full path to the file storing the saved
                credentials.
            password (str): optional password to encrypt the
                credential file with. If not supplied a password
                will be generated.
            config_assistant (ConfigAssistant): optional configuration
                assistant object. Can be used to store the password to the
                credential file.

        Raises:
            IOError: If not able to decrypt the data.

        Returns:
            Credential object (oauth2.credentials.Credentials) read from
            the file.
        """
        if not file_path:
            file_path = self._filepath

        if not os.path.isfile(file_path):
            return None

        if password:
            password = bytes(password, 'utf-8')
        elif config_assistant:
            try:
                password = config_assistant.get_config('cred_key')
                if not isinstance(password, bytes):
                    password = bytes(password, 'utf-8')
            except KeyError:
                raise IOError(
                    'Not able to determine encryption key from config.')
        else:
            raise IOError(
                'Neither password nor a configuration assistant passed to '
                'tool, unable to determine password.')

        with open(file_path, 'rb') as fh:
            salt = fh.read(self.SALT_LENGTH)
            key = self._get_key(salt, password)
            data = fh.read()
            crypto = fernet.Fernet(key)
            try:
                data_string = crypto.decrypt(data)
            except fernet.InvalidSignature as e:
                raise IOError(
                    'Unable to decrypt data, signature is not correct: '
                    '{0!s}'.format(e))
            except fernet.InvalidToken as e:
                raise IOError(
                    'Unable to decrypt data, password wrong? (error '
                    '{0!s})'.format(e))

            # TODO: Implement a manager.
            cred_obj = TimesketchPwdCredentials()
            try:
                cred_obj.deserialize(data_string)

                return cred_obj
            except TypeError:
                logger.debug('Credential object is not "timesketch" auth.')

            cred_obj = TimesketchOAuthCredentials()
            cred_obj.deserialize(data_string)
            return cred_obj
