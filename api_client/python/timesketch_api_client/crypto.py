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

from __future__ import annotations

import base64
import os
import getpass
import logging
import stat
from typing import Any, Optional, Union

from cryptography import fernet
from cryptography.hazmat import backends
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from . import credentials

logger = logging.getLogger("timesketch_api.crypto_client")


class CredentialStorage:
    """Class to store and retrieve stored credentials."""

    # The default filename of the token file.
    DEFAULT_CREDENTIAL_FILENAME = ".timesketch.token"

    # Length of the salt.
    SALT_LENGTH = 16

    def __init__(self, file_path: str = "") -> None:
        """Initialize the class.

        Args:
            file_path: Path to the credential file.
        """
        self._user = getpass.getuser()
        if file_path:
            self._filepath = file_path
        else:
            home_path = os.path.expanduser("~")
            self._filepath = os.path.join(home_path, self.DEFAULT_CREDENTIAL_FILENAME)

    def _get_key(self, salt: bytes, password: bytes) -> bytes:
        """Returns an encryption key.

        Args:
            salt: a salt used during the encryption.
            password: the password used to decrypt/encrypt
                the message.

        Returns:
            Bytes with the encryption key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=backends.default_backend(),
        )
        return bytes(base64.urlsafe_b64encode(kdf.derive(password)))

    def set_filepath(self, file_path: str) -> None:
        """Set the filepath to the credential file.

        Args:
            file_path: Path to the credential file.
        """
        if os.path.isfile(file_path):
            self._filepath = file_path

    def save_credentials(
        self,
        cred_obj: credentials.TimesketchCredentials,
        file_path: str = "",
        password: Union[str, bytes] = "",
        config_assistant: Any = None,
    ) -> None:
        """Save credential data to a token file.

        This function will create an encrypted file
        in the user's home directory (~/.timesketch.token by default)
        that contains a stored copy of the credential object.

        Args:
            cred_obj: the credential
                object that is to be stored on disk.
            file_path: full path to the file storing the saved
                credentials.
            password: optional password to encrypt the
                credential file with. If not supplied a password
                will be generated.
            config_assistant: optional configuration
                assistant object. Can be used to store the password to the
                credential file.
        """
        if not file_path:
            file_path = self._filepath

        if password:
            if isinstance(password, str):
                password_bytes = bytes(password, "utf-8")
            else:
                password_bytes = password
        else:
            password_bytes = fernet.Fernet.generate_key()
            if config_assistant:
                config_assistant.set_config("cred_key", password_bytes)
                config_assistant.save_config()

        if not os.path.isfile(file_path):
            logger.info("File does not exist, creating it.")

        salt = os.urandom(self.SALT_LENGTH)
        key = self._get_key(salt, password_bytes)
        crypto = fernet.Fernet(key)

        data = cred_obj.serialize()

        with open(file_path, "wb") as fw:
            fw.write(salt)
            fw.write(crypto.encrypt(data))

        file_permission = stat.S_IREAD | stat.S_IWRITE
        os.chmod(file_path, file_permission)
        logger.info("Credentials saved to: %s", file_path)

    def load_credentials(
        self,
        file_path: str = "",
        password: Union[str, bytes] = "",
        config_assistant: Any = None,
    ) -> Optional[credentials.TimesketchCredentials]:
        """Load credentials from a file and return a credential object.

        Args:
            file_path: Full path to the file storing the saved
                credentials.
            password: optional password to encrypt the
                credential file with. If not supplied a password
                will be generated.
            config_assistant: optional configuration
                assistant object. Can be used to store the password to the
                credential file.

        Raises:
            IOError: If not able to decrypt the data.
            OSError: If the file does not exist.

        Returns:
            Credential object (oauth2.credentials.Credentials) read from
            the file.
        """
        if not file_path:
            file_path = self._filepath

        if not os.path.isfile(file_path):
            return None

        password_bytes: bytes
        if password:
            if isinstance(password, str):
                password_bytes = bytes(password, "utf-8")
            else:
                password_bytes = password
        elif config_assistant:
            try:
                password_raw = config_assistant.get_config("cred_key")
                if not isinstance(password_raw, bytes):
                    password_bytes = bytes(password_raw, "utf-8")
                else:
                    password_bytes = password_raw
            except KeyError as exc:
                raise IOError(
                    "Not able to determine encryption key from config."
                ) from exc
        else:
            raise IOError(
                "Neither password nor a configuration assistant passed to "
                "tool, unable to determine password."
            )

        with open(file_path, "rb") as fh:
            salt = fh.read(self.SALT_LENGTH)
            key = self._get_key(salt, password_bytes)
            data = fh.read()
            crypto = fernet.Fernet(key)
            try:
                data_string = crypto.decrypt(data)
            except fernet.InvalidSignature as e:
                raise IOError(
                    "Unable to decrypt data, signature is not correct: "
                    "{0!s}".format(e)
                ) from e
            except fernet.InvalidToken as e:
                raise IOError(
                    "Unable to decrypt data, password wrong? (error " "{0!s})".format(e)
                ) from e

            # TODO: Implement a manager.
            pwd_cred_obj = credentials.TimesketchPwdCredentials()
            try:
                pwd_cred_obj.deserialize(data_string)

                return pwd_cred_obj
            except TypeError:
                logger.debug('Credential object is not "timesketch" auth.')

            oauth_cred_obj = credentials.TimesketchOAuthCredentials()
            oauth_cred_obj.deserialize(data_string)
            return oauth_cred_obj
