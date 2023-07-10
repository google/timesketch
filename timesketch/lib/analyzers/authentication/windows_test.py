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
"""Unit tests for Windows authentication analyzer."""

from typing import List

import json
import logging
import textwrap

import mock

from timesketch.lib.analyzers.authentication import windows
from timesketch.lib.analyzers.interface import AnalyzerOutput
from timesketch.lib.analyzers.sequence_sessionizer_test import _create_eventObj
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

log = logging.getLogger("timesketch")
log.setLevel(logging.DEBUG)


class TestWindowsLoginBruteForceAnalyzer(BaseTest):
    """Class for testing WindowsLoginBruteForceAnalyzer."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_bruteforce_run(self) -> None:
        """Tests run method with brute force events."""

        analyzer = windows.WindowsLoginBruteForceAnalyzer(
            index_name="test_index", sketch_id=1, timeline_id=1
        )

        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        self._create_mock_events(datastore)

        expected_output = self._create_mock_run_output()
        output = analyzer.run()

        self.assertDictEqual(json.loads(expected_output), json.loads(output))

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    def test_benign_run(self) -> None:
        """Tests run method."""

        analyzer = windows.WindowsLoginBruteForceAnalyzer(
            index_name="test_index", sketch_id=1, timeline_id=1
        )

        analyzer.datastore.client = mock.Mock()
        datastore = analyzer.datastore

        self._create_mock_benign_events(datastore)

        expected_output = self._create_mock_benign_run_output()
        output = analyzer.run()

        self.assertDictEqual(json.loads(expected_output), json.loads(output))

    def _create_mock_events(self, datastore) -> None:
        """Creates mock Windows authentication events."""

        config = {
            "computer_name": "WIN-EFPSBTQIU5K",
            "username": "Administrator",
            "domain": "WIN-EFPSBTQIU5K",
            "ip_address": "192.168.40.25",
            "port": 46658,
            "workstation_name": "kali",
            "logon_type": 3,
            "logon_id": 0x00000000005C338A,
        }

        events = []

        events.extend(self._create_failed_events(config=config, count=200))
        events.extend(self._create_success_events(config=config, count=1))
        events.extend(self._create_logout_events(config=config, count=1))

        config["ip_address"] = "192.168.100.112"
        config["logon_id"] = 0x00000000006C339A
        events.extend(self._create_failed_events(config=config, count=200))
        events.extend(self._create_success_events(config=config, count=1))
        events.extend(self._create_logout_events(config=config, count=1))

        log.debug("Total number of mock events %d", len(events))

        event_id = 0
        timestamp = 1672097149681987

        for event in events:
            _create_eventObj(datastore, event_id, timestamp, event)
            event_id += 1
            timestamp += 1000000

    def _create_mock_benign_events(self, datastore) -> None:
        """Creates mock Windows authentication events."""

        config = {
            "computer_name": "WIN-EFPSBTQIU5K",
            "username": "Administrator",
            "domain": "WIN-EFPSBTQIU5K",
            "ip_address": "192.168.40.25",
            "port": 46658,
            "workstation_name": "kali",
            "logon_type": 3,
            "logon_id": 0x00000000005C338A,
        }

        events = []

        events.extend(self._create_success_events(config=config, count=5))
        events.extend(self._create_failed_events(config=config, count=20))
        events.extend(self._create_success_events(config=config, count=1))
        events.extend(self._create_logout_events(config=config, count=1))

        log.debug("Total number of mock events %d", len(events))

        event_id = 0
        timestamp = 1672097149681987

        for event in events:
            _create_eventObj(datastore, event_id, timestamp, event)
            event_id += 1
            timestamp += 1000000

    def _create_failed_events(self, config: dict, count=200) -> List[dict]:
        """Creates mock Windows failed login TimeSketch events.

        Returns:
            List[dict]: A list of dictionary containing failed login events.
        """

        return [
            {
                "source_name": "Microsoft-Windows-Security-Auditing",
                "event_identifier": 4625,
                "computer_name": config.get("computer_name"),
                "username": config.get("username"),
                "domain": config.get("domain"),
                "ip_address": config.get("ip_address"),
                "port": config.get("port") + i,
                "logon_type": config.get("logon_type"),
                "workstation_name": f"\\\\{config.get('workstation_name')}",
            }
            for i in range(0, count)
        ]

    def _create_success_events(self, config: dict, count=1) -> List[dict]:
        """Creates mock Windows successful login TimeSketch events.

        Returns:
            List[dict]: A list of dictionary containing successful login events.
        """

        return [
            {
                "source_name": "Microsoft-Windows-Security-Auditing",
                "event_identifier": 4624,
                "computer_name": config.get("computer_name"),
                "username": config.get("username"),
                "domain": config.get("domain"),
                "ip_address": config.get("ip_address"),
                "port": 0,
                "logon_id": f"{(config.get('logon_id') + i):016x}",
                "logon_type": config.get("logon_type"),
                "workstation_name": config.get("workstation_name"),
            }
            for i in range(0, count)
        ]

    def _create_logout_events(self, config: dict, count=1) -> List[dict]:
        """Creates mock Windows logout TimeSketch events.

        Returns:
            List[dict]: A list of dictionary containing logoff events.
        """

        return [
            {
                "source_name": "Microsoft-Windows-Security-Auditing",
                "event_identifier": 4634,
                "computer_name": config.get("computer_name"),
                "username": config.get("username"),
                "logon_id": f"{(config.get('logon_id') + i):016x}",
                "logon_type": config.get("logon_type"),
            }
            for i in range(0, count)
        ]

    def _create_mock_run_output(self) -> str:
        """Creates mock WindowsLoginBruteForceAnalyzer.run output

        Returns:
            str: Returns an analyzer output as a string.
        """

        output = AnalyzerOutput(
            analyzer_identifier="WindowsBruteForceAnalyser",
            analyzer_name="Windows Login Brute Force Analyzer",
            timesketch_instance="https://localhost",
            sketch_id=1,
            timeline_id=1,
        )

        output.result_priority = "HIGH"
        output.result_status = "SUCCESS"
        output.result_summary = (
            "1 brute force from 192.168.40.25, 1 brute force from 192.168.100.112"
        )
        output.result_markdown = textwrap.dedent(
            """
            ### Brute Force Analyzer

            ### Brute Force Summary for 192.168.40.25
            - Successful brute force on 2022-12-26T23:29:09Z as Administrator

            #### 192.168.40.25 Summary
            - IP first seen on 2022-12-26T23:25:49Z
            - IP last seen on 2022-12-26T23:29:09Z
            - First successful authentication on 2022-12-26T23:29:09Z
            - First successful login from 192.168.40.25
            - First successful login as Administrator

            #### Top Usernames
            - Administrator: 201

            ### Brute Force Summary for 192.168.100.112
            - Successful brute force on 2022-12-26T23:32:31Z as Administrator

            #### 192.168.100.112 Summary
            - IP first seen on 2022-12-26T23:29:11Z
            - IP last seen on 2022-12-26T23:32:31Z
            - First successful authentication on 2022-12-26T23:32:31Z
            - First successful login from 192.168.100.112
            - First successful login as Administrator

            #### Top Usernames
            - Administrator: 201"""
        )
        output.platform_meta_data["created_tags"] = ["windows_bruteforce"]

        return str(output)

    def _create_mock_benign_run_output(self) -> str:
        """Creates mock WindowsLoginBruteForceAnalyzer.run output.

        Returns:
            str: Returns an analyzer output as a string.
        """

        output = AnalyzerOutput(
            analyzer_identifier="WindowsBruteForceAnalyser",
            analyzer_name="Windows Login Brute Force Analyzer",
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
