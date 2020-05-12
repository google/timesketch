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
import random
import string
import stat

from cryptography import fernet
from google.oauth2 import credentials


logger = logging.getLogger('crypto_client_api')


class CredentialStorage:
    """Class to store and retrieve stored credentials."""

    # A default shared secret that will be used as part of the key.
    SHARED_KEY = 'thetta er mjog leynt'

    # The default filename of the token file.
    DEFAULT_CREDENTIAL_FILENAME = '.timesketch.token'

    # The number of characters in the random part of the default key.
    RANDOM_KEY_LENGTH = 20

    def __init__(self):
        """Initialize the class."""
        self._user = getpass.getuser()
        home_path = os.path.expanduser('~')
        self._filepath = os.path.join(
            home_path, self.DEFAULT_CREDENTIAL_FILENAME)

    def _get_key(self, seed_key):
        """Returns an encryption key.

        Args:
            seed_key (str): a seed used to generate an encryption key.

        Returns:
            Bytes with the encryption key.
        """

        key_string_half = '{0:s}{1:s}'.format(
            getpass.getuser(), seed_key)

        if len(key_string_half) >= 32:
            key_string = key_string_half[:32]
        else:
            key_string = '{0:s}{1:s}'.format(
                key_string_half, self.SHARED_KEY)
            key_string = key_string[:32]

        return base64.b64encode(bytes(key_string, 'utf-8'))

    def set_filepath(self, file_path):
        """Set the filepath to the credential file."""
        if os.path.isfile(file_path):
            self._filepath = file_path

    def save_credentials(self, cred_obj, file_path=''):
        """Save credential data to a token file.

        This function will create an encrypted file
        in the user's home directory (~/.timesketch.token by default)
        that contains a stored copy of the credential object.

        Args:
            cred_obj (google.oauth2.credentials.Credentials): the credential
                object that is to be stored on disk.
            file_path (str): Full path to the file storing the saved
                credentials.
        """
        # TODO (kiddi): Support user/pass credentials as well. Create
        # a separate credential object that wraps the OAUTH creds.
        if not file_path:
            file_path = self._filepath

        if not os.path.isfile(file_path):
            logger.info('File does not exist, creating it.')

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

        letters = string.ascii_letters
        random_string = ''.join(
            random.choice(letters) for _ in range(self.RANDOM_KEY_LENGTH))
        key = self._get_key(random_string)
        crypto = fernet.Fernet(key)

        with open(file_path, 'wb') as fw:
            fw.write(bytes(random_string, 'utf-8'))
            fw.write(
                crypto.encrypt(bytes(data_string, 'utf-8')))

        file_permission = stat.S_IREAD | stat.S_IWRITE
        os.chmod(file_path, file_permission)
        logger.info('Credentials saved to: %s', file_path)

    def load_credentials(self, file_path=''):
        """Load credentials from a file and return a credential object.

        Args:
            file_path (str): Full path to the file storing the saved
                credentials.

        Returns:
            Credential object (oauth2.credentials.Credentials) read from
            the file.
        """
        if not file_path:
            file_path = self._filepath

        if not os.path.isfile(file_path):
            return None

        with open(file_path, 'rb') as fh:
            random_string = fh.read(self.RANDOM_KEY_LENGTH)
            key = self._get_key(random_string.decode('utf-8'))
            data = fh.read()
            crypto = fernet.Fernet(key)
            try:
                data_string = crypto.decrypt(data)
            except fernet.InvalidSignature as e:
                logger.error(
                    'Unable to decrypt data, signature is not correct: %s', e)
                return None
            except fernet.InvalidToken as e:
                logger.error('Unable to decrypt data, error %s', e)
                return None
            try:
                token_dict = json.loads(data_string.decode('utf-8'))
            except ValueError:
                return None

            return credentials.Credentials(
                token=token_dict.get('token'),
                refresh_token=token_dict.get('_refresh_token'),
                id_token=token_dict.get('_id_token'),
                token_uri=token_dict.get('_token_uri'),
                client_id=token_dict.get('_client_id'),
                client_secret=token_dict.get('_client_secret')
            )
