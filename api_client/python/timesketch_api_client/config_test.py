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
from __future__ import unicode_literals

import unittest
import tempfile

from . import config


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
            with open(fw.name, "r") as fh:
                data = fh.read()

        lines = [x.strip() for x in data.split("\n") if x]
        expected_lines = [x.strip() for x in self.TEST_CONFIG.split("\n") if x.strip()]
        self.assertEqual(set(lines), set(expected_lines))

    def test_set_config(self):
        """Test the set config."""
        config_obj = config.ConfigAssistant()
        config_obj.set_config("host_uri", "http://127.0.0.1")

        self.assertTrue(config_obj.has_config("host_uri"))
