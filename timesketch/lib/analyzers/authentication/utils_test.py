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
"""This file con1672097149tains unit tests for interface"""

import hashlib
import logging
import sys
import textwrap

from typing import List

import pandas as pd


from timesketch.lib.analyzers.interface import AnalyzerOutput
from timesketch.lib.analyzers.authentication.utils import AuthSummary
from timesketch.lib.analyzers.authentication.utils import LoginRecord
from timesketch.lib.analyzers.authentication.utils import BaseAuthenticationUtils
from timesketch.lib.analyzers.authentication.utils import BruteForceUtils
from timesketch.lib.testlib import BaseTest

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler(sys.stdout))


def load_test_dataframe() -> pd.DataFrame:
    """Loads SSH log file and returns dataframe.

    Returns:
        pd.DataFrame: A dataframe containing mock events.
    """

    return pd.DataFrame(mock_authentication_events())


EXPECTED_IP_SUMMARY = {
    "summary_type": "source_ip",
    "source_ip": "192.168.140.67",
    "domain": "",
    "username": "",
    "first_seen": 1672097149,
    "last_seen": 1672097360,
    "first_auth": {
        "timestamp": 1672097359,
        "session_id": "6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d0"
        "2a1991db",
        "session_duration": 1,
        "source_ip": "192.168.140.67",
        "source_hostname": "",
        "source_port": 58300,
        "domain": "",
        "username": "admin",
    },
    "summary": {},
    "successful_logins": [
        {
            "timestamp": 1672097359,
            "session_id": "6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d0"
            "2a1991db",
            "session_duration": 1,
            "source_ip": "192.168.140.67",
            "source_hostname": "",
            "source_port": 58300,
            "domain": "",
            "username": "admin",
        }
    ],
    "success_source_ips": ["192.168.140.67"],
    "success_usernames": ["admin"],
    "total_success_events": 1,
    "total_failed_events": 200,
    "distinct_source_ip_count": 1,
    "distinct_username_count": 1,
    "top_source_ips": {"192.168.140.67": 202},
    "top_usernames": {"admin": 202},
}

EXPECTED_USER_SUMMARY = {
    "summary_type": "username",
    "source_ip": "",
    "domain": "",
    "username": "admin",
    "first_seen": 1672097149,
    "last_seen": 1672097360,
    "first_auth": {
        "timestamp": 1672097359,
        "session_id": "6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d0"
        "2a1991db",
        "session_duration": 1,
        "source_ip": "192.168.140.67",
        "source_hostname": "",
        "source_port": 58300,
        "domain": "",
        "username": "admin",
    },
    "summary": {},
    "successful_logins": [
        {
            "timestamp": 1672097359,
            "session_id": "6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d0"
            "2a1991db",
            "session_duration": 1,
            "source_ip": "192.168.140.67",
            "source_hostname": "",
            "source_port": 58300,
            "domain": "",
            "username": "admin",
        },
    ],
    "success_source_ips": ["192.168.140.67"],
    "success_usernames": ["admin"],
    "total_success_events": 1,
    "total_failed_events": 210,
    "distinct_source_ip_count": 2,
    "distinct_username_count": 1,
    "top_source_ips": {
        "172.16.151.91": 10,
        "192.168.140.67": 202,
    },
    "top_usernames": {"admin": 212},
}

EXPECTED_AUTH_SUMMARY_3 = {
    "summary_type": "source_ip",
    "source_ip": "192.168.140.67",
    "domain": "",
    "username": "",
    "first_seen": 1672097149,
    "last_seen": 1672097360,
    "first_auth": {
        "timestamp": 1672097359,
        "session_id": "6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d0"
        "2a1991db",
        "session_duration": 1,
        "source_ip": "192.168.140.67",
        "source_hostname": "",
        "source_port": 58300,
        "domain": "",
        "username": "admin",
    },
    "summary": {},
    "successful_logins": [
        {
            "timestamp": 1672097359,
            "session_id": "6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d0"
            "2a1991db",
            "session_duration": 1,
            "source_ip": "192.168.140.67",
            "source_hostname": "",
            "source_port": 58300,
            "domain": "",
            "username": "admin",
        }
    ],
    "success_source_ips": ["192.168.140.67"],
    "success_usernames": ["admin"],
    "total_success_events": 1,
    "total_failed_events": 200,
    "distinct_source_ip_count": 1,
    "distinct_username_count": 1,
    "top_source_ips": {"192.168.140.67": 202},
    "top_usernames": {"admin": 202},
}

EXPECTED_AUTH_SUMMARY_4 = {
    "summary_type": "username",
    "source_ip": "",
    "domain": "",
    "username": "admin",
    "first_seen": 1672097149,
    "last_seen": 1672097360,
    "first_auth": {
        "timestamp": 1672097359,
        "session_id": "6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d0"
        "2a1991db",
        "session_duration": 1,
        "source_ip": "192.168.140.67",
        "source_hostname": "",
        "source_port": 58300,
        "domain": "",
        "username": "admin",
    },
    "summary": {},
    "successful_logins": [
        {
            "timestamp": 1672097359,
            "session_id": "6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d0"
            "2a1991db",
            "session_duration": 1,
            "source_ip": "192.168.140.67",
            "source_hostname": "",
            "source_port": 58300,
            "domain": "",
            "username": "admin",
        },
    ],
    "success_source_ips": ["192.168.140.67"],
    "success_usernames": ["admin"],
    "total_success_events": 1,
    "total_failed_events": 210,
    "distinct_source_ip_count": 2,
    "distinct_username_count": 1,
    "top_source_ips": {
        "172.16.151.91": 10,
        "192.168.140.67": 202,
    },
    "top_usernames": {"admin": 212},
}

EMPTY_LOGIN_SESSION = {
    "source_ip": "",
    "domain": "",
    "username": "",
    "session_id": "",
    "login_timestamp": 0,
    "logout_timestamp": 0,
    "session_duration": 0,
}

EXPECTED_LOGIN_SESSION = {
    "timestamp": 1672097359,
    "session_id": "6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d02a1991db",
    "source_hostname": "",
    "session_duration": 7,
    "source_ip": "192.168.140.67",
    "source_port": 58300,
    "domain": "",
    "username": "admin",
}


class TestBaseAuthenticationAnalyzer(BaseTest):
    """Class for testing BasicAuthenticationAnalyzer."""

    def setUp(self) -> None:
        df = load_test_dataframe()
        self.analyzer = BaseAuthenticationUtils()
        self.analyzer.set_dataframe(df)

    def test_check_required_fields(self) -> None:
        """Tests check_required_fields method."""

        # Testing missing fields
        fields = [
            "timestamp",
            "source_ip",
            "source_port",
            "username",
            "domain",
            "authentication_method",
            "authentication_result",
        ]
        self.assertFalse(self.analyzer.check_required_fields(fields))

        # Testing valid fields
        fields = [
            "timestamp",
            "source_ip",
            "source_port",
            "username",
            "domain",
            "authentication_method",
            "authentication_result",
            "session_id",
        ]
        self.assertTrue(self.analyzer.check_required_fields(fields))

    def test_calculate_session_duration(self) -> None:
        """Tests calculate_session_duration."""

        # Testing empty session ID
        session_duration = self.analyzer.calculate_session_duration(
            session_id="", timestamp=1672097359
        )
        self.assertEqual(-1, session_duration)

        # Testing invalid session ID value
        session_duration = self.analyzer.calculate_session_duration(
            session_id="abcdef01234567890", timestamp=1672097359
        )
        self.assertEqual(-1, session_duration)

        # Testing valid session ID and invalid timestamp
        session_duration = self.analyzer.calculate_session_duration(
            session_id="6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d0"
            "2a1991db",
            timestamp=None,
        )
        self.assertEqual(-1, session_duration)

        # Testing valid session_id and timestamp
        session_duration = self.analyzer.calculate_session_duration(
            session_id="6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d0"
            "2a1991db",
            timestamp=1672097359,
        )
        self.assertEqual(1, session_duration)

    def test_get_ip_summary(self) -> None:
        """Test get_ip_summary method."""

        # Testing empty dataframe
        authsummary = self.analyzer.get_ip_summary("100.100.100.100")
        self.assertIsNone(authsummary)

        # Testing non-existent IP address 100.100.100.100
        authsummary = self.analyzer.get_ip_summary("100.100.100.100")
        self.assertIsNone(authsummary)

        # Testing valid IP 192.168.140.67 summary
        authsummary = self.analyzer.get_ip_summary("192.168.140.67")
        self.assertDictEqual(EXPECTED_IP_SUMMARY, authsummary.to_dict())

    def test_get_user_summary(self) -> None:
        """Test get_user_summary method."""

        # Testing empty dataframe
        authsummary = self.analyzer.get_user_summary(
            username="gametogenesis", domain=""
        )
        self.assertIsNone(authsummary)

        # Testing non-existent username supermario
        authsummary = self.analyzer.get_user_summary(username="supermario", domain="")
        self.assertIsNone(authsummary)

        # Testing valid username kadmin
        authsummary = self.analyzer.get_user_summary(username="admin", domain="")
        self.assertIsNotNone(authsummary)
        self.assertDictEqual(EXPECTED_USER_SUMMARY, authsummary.to_dict())

    def test_get_authsummary(self) -> None:
        """Test get_authsummary method."""

        # Testing empty dataframe
        df = pd.DataFrame()
        authsummary = self.analyzer.get_authsummary(df, "source_ip", "100.100.100.100")
        self.assertIsNone(authsummary)

        # Testing invalid summary_type value
        df = self.analyzer.df
        authsummary = self.analyzer.get_authsummary(df, "source_port", 54321)
        self.assertIsNone(authsummary)

        # Testing valid summary_type source_ip
        authsummary = self.analyzer.get_authsummary(df, "source_ip", "192.168.140.67")
        self.assertDictEqual(EXPECTED_AUTH_SUMMARY_3, authsummary.to_dict())

        # Testing valid source_type username
        authsummary = self.analyzer.get_authsummary(df, "username", "admin")
        self.assertDictEqual(EXPECTED_AUTH_SUMMARY_4, authsummary.to_dict())

    def test_to_useraccount(self) -> None:
        """Test to_useraccount method."""

        # Testing empty domain and username
        useraccount = self.analyzer.to_useraccount(username="", domain="")
        self.assertEqual(useraccount, "")

        # Testing username and domain
        useraccount = self.analyzer.to_useraccount(username="admin", domain="example")
        self.assertEqual("example/admin", useraccount)

    def test_from_useraccount(self) -> None:
        """Test from_useraccount method."""

        # Testing empty useraccount
        username, domain = self.analyzer.from_useraccount("")
        self.assertEqual("", username)
        self.assertEqual("", domain)

        # Testing empty domain and username
        username, domain = self.analyzer.from_useraccount("admin")
        self.assertEqual("admin", username)
        self.assertEqual("", domain)

        username, domain = self.analyzer.from_useraccount("example/admin")
        self.assertEqual("admin", username)
        self.assertEqual("example", domain)


class TestBruteForceAnalyzer(BaseTest):
    """Class for testing BruteForceAnalzyer."""

    def setUp(self) -> None:
        """Setups test class."""

        self.analyzer = BruteForceUtils()
        self.analyzer.analyzer_metadata = {
            "timesketch_instance": "http://localhost",
            "sketch_id": 1,
            "timeline_id": 1,
        }
        df = load_test_dataframe()
        self.analyzer.set_dataframe(df)

    def _create_analyzer_output(self) -> AnalyzerOutput:
        """Creates and returns analyzer output.

        Returns:
            AnalyzerOutput: Returns an empty analyzer output.
        """

        output = AnalyzerOutput(
            analyzer_identifier="BruteForceAnalyzer",
            analyzer_name="Brute Force Analyzer",
            timesketch_instance="http://localhost",
            sketch_id=1,
            timeline_id=1,
        )
        return output

    def _create_authsummary(self) -> AuthSummary:
        """Creates and returns authsummaries.

        Returns:
            AuthSummary: Returns an object of AuthSummary.
        """

        # Create successful login entry
        login = LoginRecord(
            source_ip="192.168.140.67",
            username="admin",
            domain="",
            session_id="6d652a46d9ddf7ebc4cade9b36a2ff1a0819180ea353c63438b5e5d0"
            "2a1991db",
        )
        login.timestamp = 1672097359
        login.source_port = 58300
        login.session_duration = 1

        authsummary = AuthSummary()
        authsummary.summary_type = "source_ip"
        authsummary.source_ip = "192.168.140.67"
        authsummary.username = ""
        authsummary.domain = ""
        authsummary.first_seen = 1672097149
        authsummary.last_seen = 1672097360
        authsummary.first_auth = login
        authsummary.successful_logins.append(login)
        authsummary.success_source_ips = ["192.168.140.67"]
        authsummary.success_usernames = ["admin"]
        authsummary.total_success_events = 1
        authsummary.total_failed_events = 200
        authsummary.distinct_source_ip_count = 1
        authsummary.distinct_username_count = 1
        authsummary.top_source_ips["192.168.140.67"] = 202
        authsummary.top_usernames["admin"] = 202

        authsummary.summary["bruteforce"] = []
        authsummary.summary["bruteforce"].append(login)

        return authsummary

    def _create_authsummaries(self) -> List[AuthSummary]:
        """Creates and returns a list of AuthSummary.

        Returns:
            List[AuthSummary]: A list of AuthSummary.
        """

        authsummaries = []
        authsummary = self._create_authsummary()
        authsummaries.append(authsummary)

        return authsummaries

    def _mock_empty_analyzer_output(self) -> AnalyzerOutput:
        """Mock an empty analyzer output.

        Returns:
            AnalyzerOutput: An object of class AnalyzerOutput.
        """

        output = self._create_analyzer_output()
        output.result_priority = "NOTE"
        output.result_status = "SUCCESS"
        output.result_summary = "No bruteforce activity"
        output.result_markdown = "\n### Brute Force Analyzer\nBrute force not detected"

        return output

    def _mock_analyzer_output(self) -> AnalyzerOutput:
        """Mocks a valid analyzer output.

        Returns:
            AnalyzerOutput: An object of class AnalyzerOutput.
        """

        output = self._create_analyzer_output()
        output.result_priority = "HIGH"
        output.result_status = "SUCCESS"
        output.result_summary = "1 brute force from 192.168.140.67"
        output.result_markdown = textwrap.dedent(
            """
                ### Brute Force Analyzer

                ### Brute Force Summary for 192.168.140.67
                - Successful brute force on 2022-12-26T23:29:19Z as admin

                #### 192.168.140.67 Summary
                - IP first seen on 2022-12-26T23:25:49Z
                - IP last seen on 2022-12-26T23:29:20Z
                - First successful authentication on 2022-12-26T23:29:19Z
                - First successful login from 192.168.140.67
                - First successful login as admin

                #### Top Usernames
                - admin: 202"""
        )

        return output

    def test_generate_analyzer_output(self) -> None:
        """Tests generate_analyzer_output method."""

        test_output = self._create_analyzer_output()

        # Testing unset authsummaries
        self.assertIsNone(
            self.analyzer.generate_analyzer_output(
                authsummaries=None, output=test_output
            )
        )

        # Testing empty authsummaries
        expected_output = self._mock_empty_analyzer_output()

        # Generate output and set result_attributes to empty dict
        # We don't want to compare it.
        output = self.analyzer.generate_analyzer_output(
            authsummaries=[], output=test_output
        )
        output.result_attributes = {}

        self.assertDictEqual(expected_output.__dict__, output.__dict__)

        # Testing valid authsummaries
        expected_output = self._mock_analyzer_output()
        authsummaries = self._create_authsummaries()
        expected_output.result_attributes = {"bruteforce": authsummaries}

        output = self.analyzer.generate_analyzer_output(
            authsummaries=authsummaries, output=test_output
        )

        self.assertDictEqual(expected_output.__dict__, output.__dict__)

    def test_ip_bruteforce_check(self) -> None:
        """Tests ip_bruteforce_check method."""

        # Testing non-existing IP
        authsummary = self.analyzer.ip_bruteforce_check("192.168.100.100")
        self.assertIsNone(authsummary)

        # Testing empty IP address
        authsummary = self.analyzer.ip_bruteforce_check("")
        self.assertIsNone(authsummary)

        # Testing non brutforcing IP address
        authsummary = self.analyzer.ip_bruteforce_check("172.30.151.91")
        self.assertIsNone(authsummary)

        # Testing brute forcing IP address
        authsummary = self.analyzer.ip_bruteforce_check("192.168.140.67")
        expected_authsummary = self._create_authsummary()

        self.assertDictEqual(expected_authsummary.to_dict(), authsummary.to_dict())

    def test_start_bruteforce_analysis(self) -> None:
        """Tests start_bruteforce_analysis method."""

        expected_output = self._mock_analyzer_output()

        # Generate analyzer output and set result_attributes to empty dict
        output = self.analyzer.start_bruteforce_analysis(self._create_analyzer_output())
        output.result_attributes = {}

        self.assertDictEqual(expected_output.to_json(), output.to_json())


def mock_authentication_events() -> List[dict]:
    """Mock authentication events.

    Returns:
        List[dict]: A list of dictionary containing mock authentication events.
    """

    events = []

    # Creating failed events 192.168.140.67
    config = {
        "hostname": "debian-server",
        "username": "admin",
        "source_ip": "192.168.140.67",
        "source_port": 58200,
        "event_type": "authentication",
        "authentication_method": "password",
        "authentication_result": "failure",
        "pid": 625,
    }
    events.extend(create_authentication_events(config, count=200))

    # Create failed authentication from 172.16.151.91
    config["source_ip"] = "172.16.151.91"
    config["source_port"] = 58250
    events.extend(create_authentication_events(config, count=10))

    # Create successful events
    config = {
        "hostname": "debian-server",
        "username": "admin",
        "source_ip": "192.168.140.67",
        "source_port": 58300,
        "event_type": "authentication",
        "authentication_method": "password",
        "authentication_result": "success",
        "pid": 700,
    }
    events.extend(create_authentication_events(config, count=1))

    # Create disconnection events
    config = {
        "hostname": "debian-server",
        "username": "admin",
        "source_ip": "192.168.140.67",
        "source_port": 58300,
        "event_type": "disconnection",
        "authentication_method": "",
        "authentication_result": "",
        "pid": 700,
    }
    events.extend(create_authentication_events(config, count=1))

    # Generate event ID and timestamp
    event_id = 0
    timestamp = 1672097149681987

    for i, _ in enumerate(events):
        events[i]["event_id"] = event_id
        events[i]["timestamp"] = int(timestamp / 1000000)

        event_id += 1
        timestamp += 1000000
    return events


def create_authentication_events(config: dict, count: int = 200) -> List[dict]:
    """Creates authentication events.

    Args:
        config (dict): A dictionary containing SSH event data.
        count (int): Indicates the number of authentication events to generate.

    Returns:
        List[dict]: A list of dictionary containing authentication events.
    """

    events = []

    for i in range(0, count):
        event = {
            "hostname": config.get("hostname", "default-ssh-server"),
            "username": config.get("username", "root"),
            "domain": "",
            "source_ip": config.get("source_ip", "192.168.1.1"),
            "source_port": int(config.get("source_port", 62000)) + i,
            "pid": int(config.get("pid", 500)) + i,
            "event_type": config.get("event_type", "disconnection"),
            "authentication_method": config.get("authentication_method", ""),
            "authentication_result": config.get("authentication_result", ""),
        }

        event["session_id"] = calculate_session_id(
            hostname=event["hostname"],
            username=event["username"],
            source_ip=event["source_ip"],
            source_port=event["source_port"],
        )
        events.append(event)

    return events


def calculate_session_id(
    hostname: str, username: str, source_ip: str, source_port: int
) -> str:
    """Creates pseudo session ID for SSH.

    Args:
        hostname (str): Hostname of the system.
        username (str): Username in authentication event.
        source_ip (str): IP address initiating authentication.
        source_port (int): The source port used in authentication.

    Returns:
        str: A string containing pseudo session ID.
    """

    session_id_data = f"{hostname}|{username}|{source_ip}|{source_port}"

    hasher = hashlib.new("sha256")
    hasher.update(str.encode(session_id_data))

    return hasher.hexdigest()
