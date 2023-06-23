# Copyright 2023 Google Inc. All rights reserved.
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
"""Unit tests for SSH analyzers"""

import json
import logging
import textwrap

import mock

from timesketch.lib.analyzers.authentication.ssh import SSHBruteForceAnalyzer
from timesketch.lib.analyzers.interface import AnalyzerOutput
from timesketch.lib.analyzers.sequence_sessionizer_test import _create_eventObj
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

log = logging.getLogger("timesketch")
log.setLevel(logging.DEBUG)


class TestSSHBruteForceAnalyzer(BaseTest):
    """Class for testing SSHBruteForceAnalyzer."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def setUp(self) -> None:
        super().setUp()
        self.analyzer = SSHBruteForceAnalyzer(
            index_name="test_index", sketch_id=1, timeline_id=1
        )

    def test_run(self) -> None:
        """Tests run method."""

        self.analyzer.datastore.client = mock.Mock()
        datastore = self.analyzer.datastore

        _create_mock_events(datastore)
        expected_output = _create_analyzer_output_json()

        output = self.analyzer.run()
        self.assertDictEqual(json.loads(expected_output), json.loads(output))

    def test_run_no_bruteforce(self) -> None:
        """Tests run method."""

        self.analyzer.datastore.client = mock.Mock()
        datastore = self.analyzer.datastore

        _create_mock_events(datastore, count=10)
        expected_output = _create_no_bruteforce_analyzer_output_json()

        output = self.analyzer.run()
        self.assertDictEqual(json.loads(expected_output), json.loads(output))


def _create_mock_events(datastore, count: int = 200) -> None:
    """Creates mock TimeSketch events.

    Args:
        count (int): Number of events to generate.
    """

    start = 58320
    end = int(start + count)

    events = [
        {
            "reporter": "sshd",
            "hostname": "ssh-server",
            "pid": port - 58000,
            "ip_address": "192.168.40.25",
            "port": port,
            "username": "admin",
            "authentication_method": "password",
            "body": f"Failed password for admin from 192.168.40.25 port {port} ssh2",
        }
        for port in range(start, end)
    ]
    events.extend(
        [
            {
                "reporter": "sshd",
                "hostname": "ssh-server",
                "pid": 625,
                "ip_address": "192.168.40.25",
                "port": 58600,
                "username": "admin",
                "authentication_method": "password",
                "body": "Accepted password for admin from 192.168.40.25 port 58600"
                " ssh2",
            },
            {
                "reporter": "sshd",
                "hostname": "ssh-server",
                "pid": 626,
                "ip_address": "192.168.40.25",
                "port": 58600,
                "username": "admin",
                "authentication_method": "password",
                "body": "Disconnected from user admin 192.168.40.25 port 58600",
            },
        ]
    )

    event_id = 0
    timestamp = 1673368814000000

    for event in events:
        _create_eventObj(datastore, event_id, timestamp, event)
        event_id += 1
        timestamp += 1000000
    print("events registered ", event_id)


def _create_analyzer_output_json() -> str:
    """Creates expected analyzer output

    Returns:
        str: AnalyzerOutput as a string.
    """

    output = AnalyzerOutput(
        analyzer_identifier="SSHBruteForceAnalyzer",
        analyzer_name="SSH Brute Force Analyzer",
        timesketch_instance="https://localhost",
        sketch_id=1,
        timeline_id=1,
    )

    output.result_priority = "HIGH"
    output.result_status = "SUCCESS"
    output.result_summary = "1 brute force from 192.168.40.25"
    output.result_markdown = textwrap.dedent(
        """
        ### Brute Force Analyzer

        ### Brute Force Summary for 192.168.40.25
        - Successful brute force on 2023-01-10T16:43:34Z as admin

        #### 192.168.40.25 Summary
        - IP first seen on 2023-01-10T16:40:14Z
        - IP last seen on 2023-01-10T16:43:35Z
        - First successful authentication on 2023-01-10T16:43:34Z
        - First successful login from 192.168.40.25
        - First successful login as admin

        #### Top Usernames
        - admin: 202"""
    )
    output.platform_meta_data["created_tags"] = ["ssh_bruteforce"]

    return str(output)


def _create_no_bruteforce_analyzer_output_json() -> str:
    """Creates expected analyzer output

    Returns:
        str: AnalyzerOutput as a string.
    """

    output = AnalyzerOutput(
        analyzer_identifier="SSHBruteForceAnalyzer",
        analyzer_name="SSH Brute Force Analyzer",
        timesketch_instance="https://localhost",
        sketch_id=1,
        timeline_id=1,
    )

    output.result_priority = "NOTE"
    output.result_status = "SUCCESS"
    output.result_summary = "No bruteforce activity"
    output.result_markdown = textwrap.dedent(
        """
        ### Brute Force Analyzer
        Brute force not detected"""
    )

    return str(output)
