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
"""Tests for the Plaso field name compatibility helpers."""

from timesketch.lib import plaso_compat
from timesketch.lib.testlib import BaseTest


class TestPlasoCompat(BaseTest):
    """Tests for the Plaso field name compatibility helpers."""

    def test_get_field_names(self):
        """Tests the get_field_names function."""
        self.assertEqual(
            plaso_compat.get_field_names("message_body"), ("message_body", "body")
        )
        self.assertEqual(
            plaso_compat.get_field_names("hostname"), ("hostname", "computer_name")
        )
        # Lookups are one-directional: legacy names do not resolve to current names.
        self.assertEqual(plaso_compat.get_field_names("body"), ("body",))
        self.assertEqual(
            plaso_compat.get_field_names("computer_name"), ("computer_name",)
        )
        # Fields without aliases.
        self.assertEqual(plaso_compat.get_field_names("username"), ("username",))

    def test_expand_field_names(self):
        """Tests the expand_field_names function."""
        self.assertEqual(
            plaso_compat.expand_field_names(
                ["timestamp", "message_body", "body", "hostname", "username"]
            ),
            [
                "timestamp",
                "message_body",
                "body",
                "hostname",
                "computer_name",
                "username",
            ],
        )
        self.assertEqual(plaso_compat.expand_field_names([]), [])

    def test_get_field_value(self):
        """Tests the get_field_value function."""
        get_field_value = plaso_compat.get_field_value

        # Plaso >= 20260720 and legacy events.
        self.assertEqual(get_field_value({"hostname": "new"}, "hostname"), "new")
        self.assertEqual(
            get_field_value({"computer_name": "legacy"}, "hostname"), "legacy"
        )
        self.assertEqual(get_field_value({"body": "legacy"}, "message_body"), "legacy")

        # Lookups are one-directional: asking for a legacy name does not return
        # the current field name.
        self.assertIsNone(get_field_value({"hostname": "example.com"}, "computer_name"))

        # The current field takes precedence over its legacy alias.
        source = {"hostname": "new", "computer_name": "legacy"}
        self.assertEqual(get_field_value(source, "hostname"), "new")

        # Empty values and "-" placeholders are considered not set.
        source = {"hostname": "", "computer_name": "legacy"}
        self.assertEqual(get_field_value(source, "hostname"), "legacy")
        source = {"hostname": None, "computer_name": "legacy"}
        self.assertEqual(get_field_value(source, "hostname"), "legacy")
        source = {"hostname": "-", "computer_name": "legacy"}
        self.assertEqual(get_field_value(source, "hostname"), "legacy")
        self.assertEqual(
            get_field_value({"hostname": "-"}, "hostname", "UNKNOWN"), "UNKNOWN"
        )

        # Falsy non-empty values, such as 0, are considered set.
        self.assertEqual(get_field_value({"pid": 0}, "pid", default=-1), 0)

        # Default values.
        self.assertIsNone(get_field_value({}, "hostname"))
        self.assertEqual(get_field_value({}, "hostname", "UNKNOWN"), "UNKNOWN")

    def test_build_field_query(self):
        """Tests the build_field_query function."""
        self.assertEqual(
            plaso_compat.build_field_query("message_body", "*Accepted*"),
            "(message_body:*Accepted* OR body:*Accepted*)",
        )
        self.assertEqual(
            plaso_compat.build_field_query("reporter", "sshd"), "reporter:sshd"
        )
