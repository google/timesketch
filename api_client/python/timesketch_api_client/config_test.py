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
"""Tests for the Timesketch config library for the API client."""

import unittest
import tempfile

from . import config
from . import credentials
from . import crypto


class TimesketchConfigAssistantTest(unittest.TestCase):
    """Test ConfigAssistant."""

    TEST_CONFIG = """
[timesketch]
host_uri = http://127.0.0.1
username = foobar
auth_mode = oauth
client_id = myidfoo
client_secret = sdfa@$FAsASDF132
verify = True

[cli]
sketch =
output_format = tabular
    """

    def test_get_missing_config(self):
        """Test the missing config parameter."""
        config_obj = config.ConfigAssistant()
        config_obj.set_config("host_uri", "http://127.0.0.1")

        missing = config_obj.get_missing_config()
        expected_missing = ["auth_mode", "username"]
        self.assertEqual(set(expected_missing), set(missing))

        config_obj.set_config("username", "foobar")
        missing = config_obj.get_missing_config()
        expected_missing = ["auth_mode"]
        self.assertEqual(set(expected_missing), set(missing))

        config_obj.set_config("auth_mode", "oauth")
        missing = config_obj.get_missing_config()
        expected_missing = ["client_id", "client_secret"]
        self.assertEqual(set(expected_missing), set(missing))

    def test_has_config(self):
        """Test the has_config function."""
        config_obj = config.ConfigAssistant()
        config_obj.set_config("host_uri", "http://127.0.0.1")
        self.assertTrue(config_obj.has_config("host_uri"))
        self.assertFalse(config_obj.has_config("foobar"))

    def test_load_config(self):
        """Test loading config."""
        config_obj = config.ConfigAssistant()
        with tempfile.NamedTemporaryFile(mode="w") as fw:
            fw.write(self.TEST_CONFIG)
            fw.seek(0)
            config_obj.load_config_file(fw.name)
        expected_fields = [
            "host_uri",
            "auth_mode",
            "verify",
            "client_id",
            "client_secret",
            "username",
        ]
        self.assertEqual(set(expected_fields), set(config_obj.parameters))

        self.assertEqual(config_obj.get_config("host_uri"), "http://127.0.0.1")

    def test_save_config(self):
        """Test saving the config."""
        config_obj = config.ConfigAssistant()
        config_obj.set_config("host_uri", "http://127.0.0.1")
        config_obj.set_config("username", "foobar")
        config_obj.set_config("auth_mode", "oauth")
        config_obj.set_config("client_id", "myidfoo")
        config_obj.set_config("client_secret", "sdfa@$FAsASDF132")

        data = ""
        with tempfile.NamedTemporaryFile(mode="w") as fw:
            config_obj.save_config(fw.name)

            fw.seek(0)
            with open(fw.name, "r", encoding="utf-8") as fh:
                data = fh.read()

        lines = [x.strip() for x in data.split("\n") if x]
        expected_lines = [x.strip() for x in self.TEST_CONFIG.split("\n") if x.strip()]
        self.assertEqual(set(lines), set(expected_lines))

    def test_set_config(self):
        """Test the set config."""
        config_obj = config.ConfigAssistant()
        config_obj.set_config("host_uri", "http://127.0.0.1")

        self.assertTrue(config_obj.has_config("host_uri"))

    def test_cred_key_roundtrip(self):
        """Test generated cred_key is stored as str and round-trips cleanly."""
        with (
            tempfile.NamedTemporaryFile(mode="w") as rc_file,
            tempfile.NamedTemporaryFile() as token_file,
        ):
            assistant = config.ConfigAssistant()
            assistant.config_file_path = rc_file.name
            assistant.set_config("host_uri", "http://127.0.0.1")
            assistant.set_config("username", "foobar")
            assistant.set_config("auth_mode", "userpass")

            cred = credentials.TimesketchPwdCredentials()
            cred.credential = {"username": "foobar", "password": "secret"}

            storage = crypto.CredentialStorage(file_path=token_file.name)
            storage.save_credentials(cred, config_assistant=assistant)

            saved_key = assistant.get_config("cred_key")
            self.assertIsInstance(saved_key, str)

            reloaded = config.ConfigAssistant()
            reloaded.load_config_file(rc_file.name)
            loaded_cred = storage.load_credentials(config_assistant=reloaded)
            self.assertIsNotNone(loaded_cred)
            assert loaded_cred is not None
            self.assertEqual(
                loaded_cred.credential,
                {"username": "foobar", "password": "secret"},
            )

            empty_key_assistant = config.ConfigAssistant()
            empty_key_assistant.set_config("cred_key", "")
            with self.assertRaises(IOError):
                storage.load_credentials(config_assistant=empty_key_assistant)


if __name__ == "__main__":
    unittest.main()
