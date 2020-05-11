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

import cryptography
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

    def _get_default_key(self):
        """Returns the default encryption key."""
        letters = string.ascii_letters
        random_string = ''.join(
            random.choice(letters) for _ in range(self.RANDOM_KEY_LENGTH))

        key_string = b'{0:s}{1:s}{2:s}'.format(
            getpass.getuser(), random_string, self.SHARED_KEY)

        return random_string, base64.b64encode(key_string)

    def set_filepath(self, file_path):
        """Set the filepath to the credential file."""
        if os.path.isfile(file_path):
            self._filepath = file_path

    def save_credentials(self, cred_obj, file_path=''):
        """Save credential data to a token file.

        This function will create an EncryptedFile (go/encryptedfile)
        in the user's home directory (~/.timesketch.token by default)
        that contains a stored copy of the credential object.

        Args:
            cred_obj (google.oauth2.credentials.Credentials): the credential
                object that is to be stored on disk.
            file_path (str): Full path to the file storing the saved
                credentials.
        """
        if not file_path:
            file_path = self._filepath

        if not os.path.isfile(file_path):
            logger.error(
                'Unable to save file, path %s does not exist.', file_path)
            return

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

        random_string, key = self._get_default_key()
        fernet = cryptography.fernet.Fernet(key)

        with open(file_path, 'w') as fw:
            fw.write(random_string)
            fw.write(fernet.encrypt(data_string))

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

        with open(file_path, 'r') as fh:
            random_string = fh.read(self.RANDOM_KEY_LENGTH)
            data = fh.read()
            key_string = b'{0:s}{1:s}{2:s}'.format(
                getpass.getuser(), random_string, self.SHARED_KEY)
            key = base64.b64encode(key_string)
            fernet = cryptography.fernet.Fernet(key)
            data_string = fernet.decrypt(data)
            try:
                token_dict = json.loads(data_string)
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
