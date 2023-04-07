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
"""AuthAnalyzer test class"""

import logging
import os
import textwrap
import unittest

import pandas as pd

from timesketch.lib.analyzers.analyzer_output import AnalyzerOutput
from timesketch.lib.analyzers.auth import AuthAnalyzer
from timesketch.lib.analyzers.auth import AuthSummaryData
from timesketch.lib.analyzers.auth import BruteForceAnalyzer
from timesketch.lib.analyzers.auth import LoginRecord

log = logging.getLogger("timesketch")
log.setLevel(logging.DEBUG)


def load_test_dataframe() -> pd.DataFrame:
    """Loads SSH log file and returns dataframe."""
    log_file = os.path.join("test_data", "secure.csv")
    if not os.path.exists(log_file):
        raise Exception(f"Log file {log_file} does not exist.")

    return pd.read_csv(log_file)


class TestAuthAnalyzer(unittest.TestCase):
    """Test class for AuthAnalyzer"""

    EXPECTED_IP_SUMMARY = {
        "summary_type": "source_ip",
        "source_ip": "192.168.140.67",
        "domain": "",
        "username": "",
        "first_seen": 1664739900,
        "last_seen": 1665252640,
        "first_auth": {
            "timestamp": 1665252633,
            "session_id": "7b45adc5a3d14261800c1782719f647b81b3b8013836f30893f"
            "23202b592e"
            "000",
            "session_duration": 7,
            "source_ip": "192.168.140.67",
            "source_hostname": "",
            "source_port": 49206,
            "domain": "",
            "username": "admin",
        },
        "brute_forces": [],
        "successful_logins": [
            {
                "timestamp": 1665252633,
                "session_id": "7b45adc5a3d14261800c1782719f647b81b3b8013836f30"
                "893f23202b592e"
                "000",
                "session_duration": 7,
                "source_ip": "192.168.140.67",
                "source_hostname": "",
                "source_port": 49206,
                "domain": "",
                "username": "admin",
            }
        ],
        "success_source_ip_list": ["192.168.140.67"],
        "success_username_list": ["admin"],
        "total_success_events": 1,
        "total_failed_events": 27594,
        "distinct_source_ip_count": 1,
        "distinct_username_count": 2,
        "top_source_ips": {"192.168.140.67": 5204},
        "top_usernames": {"root": 5173, "admin": 31},
    }

    EXPECTED_USER_SUMMARY = {
        "summary_type": "username",
        "source_ip": "",
        "domain": "",
        "username": "kadmin",
        "first_seen": 1664739446,
        "last_seen": 1665252676,
        "first_auth": {
            "timestamp": 1664739446,
            "session_id": "271a92c99d59549e5b74212dda7a770fa80e219474764897c47"
            "5f1320b419"
            "20a",
            "session_duration": -1,
            "source_ip": "172.30.151.71",
            "source_hostname": "",
            "source_port": 58419,
            "domain": "",
            "username": "kadmin",
        },
        "brute_forces": [],
        "successful_logins": [
            {
                "timestamp": 1664739446,
                "session_id": "271a92c99d59549e5b74212dda7a770fa80e21947476489"
                "7c475f1320b419"
                "20a",
                "session_duration": -1,
                "source_ip": "172.30.151.71",
                "source_hostname": "",
                "source_port": 58419,
                "domain": "",
                "username": "kadmin",
            },
            {
                "timestamp": 1665252676,
                "session_id": "1b45c307539bff6a44b039d99dc11bbe5e9ea9473f316b9"
                "64aa26ec176064"
                "ea0",
                "session_duration": -1,
                "source_ip": "172.30.151.91",
                "source_hostname": "",
                "source_port": 50188,
                "domain": "",
                "username": "kadmin",
            },
        ],
        "success_source_ip_list": ["172.30.151.71", "172.30.151.91"],
        "success_username_list": ["kadmin"],
        "total_success_events": 2,
        "total_failed_events": 0,
        "distinct_source_ip_count": 2,
        "distinct_username_count": 1,
        "top_source_ips": {"172.30.151.71": 1, "172.30.151.91": 1},
        "top_usernames": {"kadmin": 2},
    }

    EXPECTED_AUTH_SUMMARY_3 = {
        "summary_type": "source_ip",
        "source_ip": "192.168.140.67",
        "domain": "",
        "username": "",
        "first_seen": 1664739900,
        "last_seen": 1665252640,
        "first_auth": {
            "timestamp": 1665252633,
            "session_id": "7b45adc5a3d14261800c1782719f647b81b3b8013836f30893f"
            "23202b592e"
            "000",
            "session_duration": 7,
            "source_ip": "192.168.140.67",
            "source_hostname": "",
            "source_port": 49206,
            "domain": "",
            "username": "admin",
        },
        "brute_forces": [],
        "successful_logins": [
            {
                "timestamp": 1665252633,
                "session_id": "7b45adc5a3d14261800c1782719f647b81b3b8013836f30"
                "893f23202b592e"
                "000",
                "session_duration": 7,
                "source_ip": "192.168.140.67",
                "source_hostname": "",
                "source_port": 49206,
                "domain": "",
                "username": "admin",
            }
        ],
        "success_source_ip_list": ["192.168.140.67"],
        "success_username_list": ["admin"],
        "total_success_events": 1,
        "total_failed_events": 27594,
        "distinct_source_ip_count": 1,
        "distinct_username_count": 2,
        "top_source_ips": {"192.168.140.67": 5204},
        "top_usernames": {"root": 5173, "admin": 31},
    }

    EXPECTED_AUTH_SUMMARY_4 = {
        "summary_type": "username",
        "source_ip": "",
        "domain": "",
        "username": "kadmin",
        "first_seen": 1664739446,
        "last_seen": 1665252676,
        "first_auth": {
            "timestamp": 1664739446,
            "session_id": "271a92c99d59549e5b74212dda7a770fa80e219474764897c47"
            "5f1320b419"
            "20a",
            "session_duration": -1,
            "source_ip": "172.30.151.71",
            "source_hostname": "",
            "source_port": 58419,
            "domain": "",
            "username": "kadmin",
        },
        "brute_forces": [],
        "successful_logins": [
            {
                "timestamp": 1664739446,
                "session_id": "271a92c99d59549e5b74212dda7a770fa80e21947476489"
                "7c475f1320b419"
                "20a",
                "session_duration": -1,
                "source_ip": "172.30.151.71",
                "source_hostname": "",
                "source_port": 58419,
                "domain": "",
                "username": "kadmin",
            },
            {
                "timestamp": 1665252676,
                "session_id": "1b45c307539bff6a44b039d99dc11bbe5e9ea9473f316b9"
                "64aa26ec176064"
                "ea0",
                "session_duration": -1,
                "source_ip": "172.30.151.91",
                "source_hostname": "",
                "source_port": 50188,
                "domain": "",
                "username": "kadmin",
            },
        ],
        "success_source_ip_list": ["172.30.151.91", "172.30.151.71"],
        "success_username_list": ["kadmin"],
        "total_success_events": 2,
        "total_failed_events": 0,
        "distinct_source_ip_count": 2,
        "distinct_username_count": 1,
        "top_source_ips": {"172.30.151.71": 1, "172.30.151.91": 1},
        "top_usernames": {"kadmin": 2},
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
        "timestamp": 1665252633,
        "session_id": "7b45adc5a3d14261800c1782719f647b81b3b8013836f30893f232"
        "02b592e000",
        "source_hostname": "",
        "session_duration": 7,
        "source_ip": "192.168.140.67",
        "source_port": 49206,
        "domain": "",
        "username": "admin",
    }

    def setUp(self):
        self.analyzer = AuthAnalyzer(
            name="analyzer.auth",
            display_name="Auth Analyzer",
            description="Authentication analyzer",
        )

    def test_check_required_fields(self):
        """Test check_required_fields method."""
        # Test 1: Does not meet required fields.
        print("[+] Testing missing required fields")
        missing_fields = [
            "timestamp",
            "event_type",
            "auth_method",
            "auth_result",
            "hostname",
            "source_ip",
            "source_port",
            "source_hostname",
            "domain",
            "username",
        ]
        self.assertFalse(self.analyzer.check_required_fields(missing_fields))

        # Test 2: Meets required fields
        print("[+] Testing valid fields")
        valid_fields = [
            "timestamp",
            "event_type",
            "auth_method",
            "auth_result",
            "hostname",
            "source_ip",
            "source_port",
            "source_hostname",
            "domain",
            "username",
            "session_id",
        ]
        self.assertTrue(self.analyzer.check_required_fields(valid_fields))

    def test_session_duration(self):
        """Test session_duration method."""
        # Common dataframe for the rest of the unit tests
        df = load_test_dataframe()
        self.analyzer.set_dataframe(df)

        print("[+] Testing empty session_id")
        session_duration = self.analyzer.session_duration(
            session_id="", timestamp=12345678
        )
        self.assertEqual(session_duration, -1)

        print("[+] Testing invalid session_id")
        session_duration = self.analyzer.session_duration(
            session_id="invalid", timestamp=123456789
        )
        self.assertEqual(session_duration, -1)

        print("[+] Testing valid session_id and invalid timestamp")
        session_duration = self.analyzer.session_duration(
            session_id="7b45adc5a3d14261800c1782719f647b81b3b8013836f30893f232"
            "02b592e000",
            timestamp=None,
        )
        self.assertEqual(session_duration, -1)

        print("[+] Testing valid session_id and timestamp")
        session_duration = self.analyzer.session_duration(
            session_id="7b45adc5a3d14261800c1782719f647b81b3b8013836f30893f232"
            "02b592e000",
            timestamp=1665252633,
        )
        self.assertEqual(session_duration, 7)

    def test_get_ip_summary(self):
        """Test get_ip_summary method."""

        # Test 1: Empty dataframe.
        print("[+] Testing empty dataframe")
        df = pd.DataFrame()
        self.analyzer.set_dataframe(df)
        summary = self.analyzer.get_ip_summary("100.100.100.100")
        self.assertIsNone(summary)

        # Common dataframe for the rest of the unit tests
        df = load_test_dataframe()
        self.analyzer.set_dataframe(df)

        # Test 2: Checking for non-existent source_ip
        print("[+] Testing non-existent IP address 100.100.100.100")
        summary = self.analyzer.get_ip_summary("100.100.100.100")
        self.assertIsNone(summary)

        # Test 3: Checking a valid source_ip
        print("[+] Testing valid IP 192.168.140.67 summary")
        summary = self.analyzer.get_ip_summary("192.168.140.67")
        self.assertDictEqual(summary.to_dict(), self.EXPECTED_IP_SUMMARY)

    def test_get_user_summary(self):
        """Test get_user_summary method."""

        # Test 1: Empty dataframe
        print("[+] Testing empty dataframe")
        df = pd.DataFrame()
        self.analyzer.set_dataframe(df)
        summary = self.analyzer.get_user_summary(domain="", username="gametogenesis")
        self.assertIsNone(summary)

        # Dataframe for the rest of the tests
        df = load_test_dataframe()
        self.analyzer.set_dataframe(df)

        # Test 2: Non-existent username
        print("[+] Testing non-existent username supermario")
        summary = self.analyzer.get_user_summary(domain="", username="supermario")
        self.assertIsNone(summary)

        # Test 3: Valid username
        print("[+] Testing valid username kadmin")
        summary = self.analyzer.get_user_summary(domain="", username="kadmin")
        self.assertIsNotNone(summary)
        user_summary = summary.to_dict()
        self.assertEqual(
            user_summary["first_auth"], self.EXPECTED_USER_SUMMARY["first_auth"]
        )

    def test_get_auth_summary(self):
        """Test get_auth_summary method."""

        # Test 1: Empty dataframe
        print("[+] Testing empty dataframe")
        df = pd.DataFrame()
        result = self.analyzer.set_dataframe(df)
        self.assertFalse(result)
        summary = self.analyzer.get_auth_summary(df, "source_ip", "100.100.100.100")
        self.assertIsNone(summary)

        # Dataframe for the rest of the tests
        df = load_test_dataframe()
        self.analyzer.set_dataframe(df)

        # Test 2: Invalid summary_type
        print("[+] Testing invalid summary_type value")
        summary = self.analyzer.get_auth_summary(df, "source_port", 54321)
        self.assertIsNone(summary)

        # Test 3: Valid summary_type source_ip
        print("[+] Testing valid summary_type source_ip")
        summary = self.analyzer.get_auth_summary(df, "source_ip", "192.168.140.67")
        self.assertDictEqual(summary.to_dict(), self.EXPECTED_AUTH_SUMMARY_3)

        # Test 4: Valid summary_type username
        print("[+] Testing valid source_type username")
        summary = self.analyzer.get_auth_summary(df, "username", "kadmin")
        self.assertDictEqual(
            summary.to_dict()["first_auth"], self.EXPECTED_AUTH_SUMMARY_4["first_auth"]
        )

    def test_to_useraccount(self):
        """Test to_useraccount method."""

        # Test 1: Empty domain and username
        print("[+] Testing empty domain and username")
        useraccount = self.analyzer.to_useraccount(domain="", username="")
        self.assertEqual(useraccount, "")

        # Test 2: Non-empty domain and username
        print("[+] Testing username and domain")
        useraccount = self.analyzer.to_useraccount(domain="example", username="admin")
        self.assertEqual(useraccount, "example\\admin")

    def test_from_useraccount(self):
        """Test from_useraccount method."""

        # Test 1: Empty useraccount
        print("[+] Testing empty useraccount")
        domain, username = self.analyzer.from_useraccount("")
        self.assertEqual(domain, "")
        self.assertEqual(username, "")

        # Test 2: Empty domain
        print("[+] Testing empty domain and username")
        domain, username = self.analyzer.from_useraccount("admin")
        self.assertEqual(domain, "")
        self.assertEqual(username, "admin")

        # Test 3: Domain and username
        domain, username = self.analyzer.from_useraccount("example\\admin")
        self.assertEqual(domain, "example")
        self.assertEqual(username, "admin")

    def test_human_timestamp(self):
        """Test human_timestamp method."""
        dtstring = self.analyzer.human_timestamp(0)
        self.assertEqual(dtstring, "1970-01-01 00:00:00")

        dtstring = self.analyzer.human_timestamp(1675915532)
        self.assertEqual(dtstring, "2023-02-09 04:05:32")

    def test_get_login_session(self):
        """Test get_login_session method."""
        # Test 1: Empty dataframe
        print("[+] Testing empty dataframe and empty parameters")
        df = pd.DataFrame()
        self.analyzer.set_dataframe(df)
        login_session = self.analyzer.get_login_session("", "", "", "")
        self.assertIsNone(login_session)

        # Dataframe for the rest of the tests
        df = load_test_dataframe()
        self.analyzer.set_dataframe(df)

        # Test 2: Checking for non-existent parameter values
        print("[+] Testing non-existent value of the parameters")
        login_session = self.analyzer.get_login_session(
            source_ip="100.100.100.100",
            domain="",
            username="gametogenesis",
            session_id="kurbtwhfwq",
        )
        self.assertIsNone(login_session)

        # Test 3: Checking a valid session
        print("[+] Testing valid login session")
        login_session = self.analyzer.get_login_session(
            source_ip="192.168.140.67",
            domain="",
            username="admin",
            session_id="7b45adc5a3d14261800c1782719f647b81b3b8013836f30893f232"
            "02b592e000",
        )
        self.assertDictEqual(login_session.__dict__, self.EXPECTED_LOGIN_SESSION)


class TestBruteForceAnalyzer(unittest.TestCase):
    """Test class for BruteForceAnalyzer"""

    def _authsummarydata(self) -> AuthSummaryData:
        """Returns the expected AuthSummaryData object.

        Returns:
                AuthSummaryData: Expected AuthSummaryData object.
        """
        authdatasummary = AuthSummaryData()
        authdatasummary.summary_type = "source_ip"
        authdatasummary.source_ip = "192.168.140.67"
        authdatasummary.domain = ""
        authdatasummary.username = ""
        authdatasummary.first_seen = 1664739900
        authdatasummary.last_seen = 1665252640
        authdatasummary.success_source_ip_list = ["192.168.140.67"]
        authdatasummary.success_username_list = ["admin"]
        authdatasummary.total_success_events = 1
        authdatasummary.total_failed_events = 27594
        authdatasummary.distinct_source_ip_count = 1
        authdatasummary.distinct_username_count = 2
        authdatasummary.top_source_ips["192.168.140.67"] = 5204
        authdatasummary.top_usernames["root"] = 5173
        authdatasummary.top_usernames["admin"] = 31

        login = LoginRecord(
            source_ip="192.168.140.67",
            domain="",
            username="admin",
            session_id="7b45adc5a3d14261800c1782719f647b81b3b8013836f30893f232"
            "02b592e000",
        )
        login.timestamp = 1665252633
        login.session_duration = 7
        login.source_port = 49206

        authdatasummary.brute_forces.append(login)
        authdatasummary.successful_logins.append(login)
        authdatasummary.first_auth = login

        return authdatasummary

    def _analyzer_output(self) -> AnalyzerOutput:
        """Return expected analyzer output object.

        Returns:
                AnalyzerOutput: Expected AnalyzerOutput object.
        """
        output = AnalyzerOutput(
            analyzer_id="bruteforce.auth.analyzer", analyzer_name="Brute Force Analyzer"
        )
        output.result_summary = "1 brute force from 192.168.140.67"
        output.result_markdown = textwrap.dedent(
            """
                #### Brute Force Analyzer

                ##### Brute Force Summary for 192.168.140.67
                - Successful brute force on 2022-10-08 18:10:33 as admin

                ###### 192.168.140.67 Summary
                - IP first seen on 2022-10-02 19:45:00
                - IP last seen on 2022-10-08 18:10:40
                - First successful auth on 2022-10-08 18:10:33
                - First successful source IP: 192.168.140.67
                - First successful username: admin

                ###### Top Usernames
                - root: 5173
                - admin: 31"""
        )
        output.attributes = self._authsummarydata()
        return output

    def setUp(self):
        self.analyzer = BruteForceAnalyzer()

    def test_login_analysis_exceptions(self):
        """Test login_analysis method."""
        # Test 1: Empty dataframe
        print("[+] Testing empty dataframe")
        df = pd.DataFrame()
        self.analyzer.set_dataframe(df)
        output = self.analyzer.login_analysis("100.100.100.100")
        self.assertIsNone(output)

        # Common data frame used for unit tests
        df = load_test_dataframe()
        self.analyzer.set_dataframe(df)

        # Test 2: Login analysis with empty source_ip
        print("[+] Testing empty source_ip in login_analysis")
        output = self.analyzer.login_analysis(source_ip="")
        self.assertIsNone(output)

        # Test 3: Log analysis for non-existent IP address
        print("[+] Testing log analysis for non-existent IP address")
        output = self.analyzer.login_analysis(source_ip="100.100.100.100")
        self.assertIsNone(output)

        # Test 4: Login analysis for unsuccessful IP address
        print("[+] Testing login analysis for unsuccessful IP address")
        output = self.analyzer.login_analysis(source_ip="172.30.151.91")
        self.assertIsNone(output)

    def test_login_analysis(self):
        """Test login_analysis method."""
        # Common data frame used for unit tests
        df = load_test_dataframe()
        self.analyzer.set_dataframe(df)

        print("[+] Testing login analysis for successful IP address")
        output = self.analyzer.login_analysis(source_ip="192.168.140.67")
        expected_output = self._authsummarydata()
        self.assertDictEqual(output.to_dict(), expected_output.to_dict())

    def test_generate_report(self):
        """Test generate_report method."""
        authsummarydata = self._authsummarydata()

        summaries = []
        summaries.append(authsummarydata)
        output = self.analyzer.generate_analyzer_output(summaries, True)
        expected_output = self._analyzer_output()
        self.assertEqual(output.result_markdown, expected_output.result_markdown)

    def test_run(self):
        """Test run method."""
        df = load_test_dataframe()
        output = self.analyzer.run(df)
        expected_output = self._analyzer_output()
        self.assertEqual(output.result_markdown, expected_output.result_markdown)


if __name__ == "__main__":
    unittest.main()
