"""Tests for LoginPlugin."""

from __future__ import unicode_literals

from timesketch.lib.analyzers import login
from timesketch.lib.testlib import BaseTest


class TestLoginPlugin(BaseTest):
    """Tests the functionality of the analyzer."""

    def test_parse_evtx_logon(self):
        """Test EVTX logon parsing."""
        string_list = []
        string_parsed = {}

        attributes = login.parse_evtx_logon_event(string_list, string_parsed)
        self.assertEqual(len(attributes), 0)

        string_list = [
            "S-1-5",
            "1",
            "2",
            "0x0034",
            "S-1-5-5-4-54",
            "secret_santa",
            "6",
            "7",
            "2",
            "9",
            "10",
            "11",
            "12",
            "13",
            "14",
            "15",
            "16",
            "17",
            "18",
            "19",
            "20",
            "21",
            "22",
        ]
        string_parsed = {
            "target_user_id": "S-1-5-5-4-54",
            "target_user_name": "secret_santa",
            "target_machine_name": "rudolph",
        }

        attributes = login.parse_evtx_logon_event(string_list, string_parsed)
        self.assertEqual(len(attributes), 9)

        hostname = attributes.get("hostname", "N/A")
        self.assertEqual(hostname, "rudolph")

        session = attributes.get("session_id", "N/A")
        self.assertEqual(session, string_list[3])

        logoff_type = attributes.get("logon_type", "N/A")
        self.assertEqual(logoff_type, "Interactive")

    def test_parse_evtx_logoff(self):
        """Test EVTX logoff parsing."""
        string_list = ["0", "giljagaur", "esja", "0x000342", "2"]

        attributes = login.parse_evtx_logoff_event(string_list)

        self.assertEqual(len(attributes), 4)
        username = attributes.get("username", "N/A")
        self.assertEqual(username, string_list[1])

        session = attributes.get("session_id", "N/A")
        self.assertEqual(session, string_list[3])

        logoff_type = attributes.get("logon_type", "N/A")
        self.assertEqual(logoff_type, "Interactive")
