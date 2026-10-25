# Copyright 2026 Google Inc. All rights reserved.
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
"""Tests for the Timesketch importer CLI tool."""

import unittest

from tools import timesketch_importer


class GetSanitizedCommandLineTest(unittest.TestCase):
    """Tests for the get_sanitized_command_line function."""

    COMMON = ["--host", "https://ts.example", "--sketch_id", "1", "data.jsonl"]

    def _sanitize(self, args, password=None, client_secret=None):
        """Returns the sanitized command line for the given arguments."""
        argv = ["timesketch_importer"] + args + self.COMMON
        return timesketch_importer.get_sanitized_command_line(
            argv, secrets=[password, client_secret]
        )

    def test_without_secrets(self):
        """Test that a command line without secrets is not changed."""
        context = self._sanitize(["-u", "user"])
        self.assertEqual(
            context,
            "timesketch_importer -u user --host https://ts.example "
            "--sketch_id 1 data.jsonl",
        )

    def test_password(self):
        """Test the different ways to provide a password."""
        for args in (
            ["-p", "s3cr3t"],
            ["--password", "s3cr3t"],
            ["--pwd", "s3cr3t"],
            ["--password=s3cr3t"],
            ["--pwd=s3cr3t"],
            ["-ps3cr3t"],
            ["-dps3cr3t"],
            ["--passw", "s3cr3t"],
            ["--passw=s3cr3t"],
        ):
            context = self._sanitize(["-u", "user"] + args, password="s3cr3t")
            self.assertNotIn("s3cr3t", context, args)
            self.assertIn("-u user", context)
            self.assertIn("--sketch_id 1 data.jsonl", context)

    def test_client_secret(self):
        """Test the different ways to provide a client secret."""
        for args in (
            ["--client-secret", "s3cr3t"],
            ["--client_secret", "s3cr3t"],
            ["--client-secret=s3cr3t"],
            ["--client_secret=s3cr3t"],
            ["--client-sec", "s3cr3t"],
        ):
            context = self._sanitize(
                ["--client-id", "my-id"] + args, client_secret="s3cr3t"
            )
            self.assertNotIn("s3cr3t", context, args)
            self.assertIn("--client-id my-id", context)

    def test_empty_secrets(self):
        """Test that empty secrets do not remove other arguments."""
        context = self._sanitize(["-u", "user"], password="", client_secret="")
        self.assertIn("-u user", context)
        self.assertIn("--sketch_id 1 data.jsonl", context)


if __name__ == "__main__":
    unittest.main()
