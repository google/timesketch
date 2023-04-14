# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for SSHBruteForcePlugin"""

from datetime import datetime, timezone

import json
import logging
import textwrap

import mock

from timesketch.lib.analyzers.sequence_sessionizer_test import _create_eventObj
from timesketch.lib.analyzers.ssh_bruteforce import SSHBruteForcePlugin
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

log = logging.getLogger("timesketch")
log.setLevel(logging.DEBUG)

EXPECTED_MESSAGE = textwrap.dedent(
    """
    #### Brute Force Analyzer

    ##### Brute Force Summary for 192.168.40.25
    - Successful brute force on 2023-01-10 16:43:34 as admin

    ###### 192.168.40.25 Summary
    - IP first seen on 2023-01-10 16:40:14
    - IP last seen on 2023-01-10 16:43:39
    - First successful auth on 2023-01-10 16:43:34
    - First successful source IP: 192.168.40.25
    - First successful username: admin

    ###### Top Usernames
    - admin: 202"""
)


class TestSSHBruteForcePlugin(BaseTest):
    """Tests SSHBruteForcePlugin class."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_run(self):
        """Test the run method."""
        index = "test_index"
        sketch_id = 1

        plugin = SSHBruteForcePlugin(index_name=index, sketch_id=sketch_id)
        plugin.datastore.client = mock.Mock()
        datastore = plugin.datastore

        _create_mock_event(datastore)

        message = plugin.run()
        json_message = json.loads(message)

        _expected_message = "1 brute force from 192.168.40.25"
        self.assertEqual(_expected_message, json_message["result_summary"])
        self.assertEqual(EXPECTED_MESSAGE, json_message["result_markdown"])


def _create_mock_event(datastore):
    """Create mock failed SSH events"""

    event_timestamp = 1673368814000000
    event_id = 0
    pid = 6254
    port = 58320

    ssh_event = {
        "reporter": "sshd",
        "hostname": "linux-ssh-server",
    }

    # Failed SSH authentication event
    for _ in range(200):
        dt = datetime.utcfromtimestamp(event_timestamp / 1000000)
        _datetime = dt.astimezone(timezone.utc).isoformat()

        ssh_event["datetime"] = _datetime
        ssh_event["pid"] = pid
        ssh_event[
            "body"
        ] = f"Failed password for admin from 192.168.40.25 port {port} ssh2"

        _create_eventObj(datastore, event_id, event_timestamp, ssh_event)

        event_timestamp += 1000000
        event_id += 1
        pid += 1
        port += 1

    # Successful SSH authentication event
    dt = datetime.utcfromtimestamp(event_timestamp / 1000000)
    _datetime = dt.astimezone(timezone.utc).isoformat()

    ssh_event["datetime"] = _datetime
    ssh_event[
        "body"
    ] = f"Accepted password for admin from 192.168.40.25 port {port} ssh2"
    _create_eventObj(datastore, event_id, event_timestamp, ssh_event)

    # Disconnected SSH authentication event
    event_id += 1
    event_timestamp += 5000000
    dt = datetime.utcfromtimestamp(event_timestamp / 1000000)
    _datetime = dt.astimezone(timezone.utc).isoformat()

    ssh_event["datetime"] = _datetime
    ssh_event["body"] = f"Disconnected from user admin 192.168.40.25 port {port}"
    _create_eventObj(datastore, event_id, event_timestamp, ssh_event)
