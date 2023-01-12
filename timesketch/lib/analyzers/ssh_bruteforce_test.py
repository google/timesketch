"""Tests for SSHBruteForcePlugin"""

from __future__ import unicode_literals

from datetime import datetime, timezone
import logging
import mock

from timesketch.lib.analyzers.ssh_bruteforce import SSHBruteForcePlugin
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

from timesketch.lib.analyzers.sequence_sessionizer_test import _create_eventObj

log = logging.getLogger("timesketch.analyzers.ssh.bruteforce")
log.setLevel(logging.DEBUG)

EXPECTED_MESSAGE = """## Brute Force Analysis

### Brute Force from 192.168.40.25

- Successful brute force from 192.168.40.25 as admin at 2023-01-10 16:43:34 (duration=5)

#### IP Summaries

- Source IP: 192.168.40.25
- Brute forcing IP first seen: 2023-01-10 16:40:14
- Brute forcing IP last seen: 2023-01-10 16:43:39
- First successful login for brute forcing IP
    - IP: 192.168.40.25
    - Login timestamp: 2023-01-10 16:43:34
    - Username: admin
- Total successful login from IP: 1
- Total failed login attempts: 200
- IP addresses that successfully logged in: 192.168.40.25
- Usernames that successfully logged in: admin
- Total number of unique username attempted: 1
- Top 10 username attempted
    - admin: 202
"""


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
        self.assertEqual(message, EXPECTED_MESSAGE)


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
