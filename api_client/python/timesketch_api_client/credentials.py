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
"""Timesketch API credential library.

This library contains classes that define how to serialize the different
credential objects Timesketch supports.
"""
from __future__ import unicode_literals

import json

from google.oauth2 import credentials


class TimesketchCredentials:
    """Class to store and retrieve credentials for Timesketch."""

    # The type of credential object.
    TYPE = ""

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
        type_string = bytes(self.TYPE, "utf-8").rjust(10)[:10]

        return type_string + data

    def deserialize(self, data):
        """Deserialize a credential object from bytes.

        Args:
            data (bytes): serialized credential object.
        """
        type_data = data[:10]
        type_string = type_data.decode("utf-8").strip()
        if not self.TYPE.startswith(type_string):
            raise TypeError("Not the correct serializer.")

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

    TYPE = "timesketch"

    def from_bytes(self, data):
        """Deserialize a credential object from bytes.

        Args:
            data (bytes): serialized credential object.

        Raises:
            TypeError: if the data is not in bytes.
        """
        if not isinstance(data, bytes):
            raise TypeError("Data needs to be bytes.")

        try:
            data_dict = json.loads(data.decode("utf-8"))
        except ValueError as exc:
            raise TypeError("Unable to parse the byte string.") from exc

        if not "username" in data_dict:
            raise TypeError("Username is not set.")
        if not "password" in data_dict:
            raise TypeError("Password is not set.")
        self._credential = data_dict

    def to_bytes(self):
        """Convert the credential object into bytes for storage."""
        if not self._credential:
            return b""

        data_string = json.dumps(self._credential)
        return bytes(data_string, "utf-8")


class TimesketchOAuthCredentials(TimesketchCredentials):
    """OAUTH credentials for Timesketch authentication."""

    TYPE = "oauth"

    def from_bytes(self, data):
        """Deserialize a credential object from bytes.

        Args:
            data (bytes): serialized credential object.

        Raises:
            TypeError: if the data is not in bytes.
        """
        if not isinstance(data, bytes):
            raise TypeError("Data needs to be bytes.")

        try:
            token_dict = json.loads(data.decode("utf-8"))
        except ValueError as exc:
            raise TypeError("Unable to parse the byte string.") from exc

        self._credential = credentials.Credentials(
            token=token_dict.get("token"),
            refresh_token=token_dict.get("_refresh_token"),
            id_token=token_dict.get("_id_token"),
            token_uri=token_dict.get("_token_uri"),
            client_id=token_dict.get("_client_id"),
            client_secret=token_dict.get("_client_secret"),
        )

    def to_bytes(self):
        """Convert the credential object into bytes for storage."""
        if not self._credential:
            return b""

        cred_obj = self._credential
        data = {
            "token": cred_obj.token,
            "_scopes": getattr(cred_obj, "_scopes", []),
            "_refresh_token": getattr(cred_obj, "_refresh_token", ""),
            "_id_token": getattr(cred_obj, "_id_token", ""),
            "_token_uri": getattr(cred_obj, "_token_uri", ""),
            "_client_id": getattr(cred_obj, "_client_id", ""),
            "_client_secret": getattr(cred_obj, "_client_secret", ""),
        }
        if cred_obj.expiry:
            data["expiry"] = cred_obj.expiry.isoformat()
        data_string = json.dumps(data)

        return bytes(data_string, "utf-8")
