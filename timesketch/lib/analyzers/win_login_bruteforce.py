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
"""Sketch analyzer plugin for RDP bruteforce."""

from __future__ import unicode_literals

import logging
import xml.etree.ElementTree as ET

import pandas as pd


from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.analyzer_output import AnalyzerOutput
from timesketch.lib.analyzers.analyzer_output import AnalyzerOutputException
from timesketch.lib.analyzers.auth import AuthAnalyzerException
from timesketch.lib.analyzers.auth import BruteForceAnalyzer

log = logging.getLogger("timesketch")


class WindowsLoginEventData:
    """Windows Login events 4624 and 2625.

    Attributes:
        event_id (str): OpenSearch internal document ID.
        timestamp (str): Event timestamp.
        event_key (str): Windows authentication event type i.e. authentication
            and disconnection.
        auth_method (str): Windows authentication methods. Valid values are
            password or publickey.
        domain (str): Domain of authenticating user.
        username (str): Username of authenticating user.
        source_ip (str): Source IP of the device authenticating.
        source_port (int): Source port of used in authentication event.
        source_hostname (str): Source hostname of the device authenticating.
        session_id (str): Windows authentication session ID.
    """

    def __init__(self):
        """Initializing WindowsLoginEventData."""
        self.event_id = ""
        self.timestamp = 0
        self.hostname = ""
        self.event_type = ""
        self.auth_method = ""
        self.auth_result = ""
        self.domain = ""
        self.username = ""
        self.source_ip = ""
        self.source_port = 0
        self.source_hostname = ""
        self.session_id = ""

        # Windows Logon/Logoff events.
        self.eid = None
        self.logon_type = None
        self.process_id = None
        self.process_name = None


class WindowsLoginBruteForcePlugin(interface.BaseAnalyzer):
    """ "Analyzer for Windows login bruteforce authentication."""

    NAME = "WindowsLoginBruteForcePlugin"
    DISPLAY_NAME = "Windows Login Brute Force Analyzer"
    DESCRIPTION = "Windows login brute force analyzer"

    # We are interested in the following successful logon types.
    BRUTEFORCE_LOGON_TYPE = [2, 3, 10]

    def _empty_analyzer_output(self, status: str = "Failed", message: str = "") -> str:
        """Returns empty analyzer output.

        Returns:
            AnalyzerOutput: AnalyzerOutput object with empty values.
        """
        output = AnalyzerOutput(
            analyzer_id="analyzer.bruteforce.windows",
            analyzer_name="Windows BruteForce Analyzer",
        )

        output.result_priority = "LOW"
        output.result_status = status
        output.result_summary = message

        return str(output)

    def parse_xml_string(self, xml_string: str) -> WindowsLoginEventData:
        """Parses Windows authentication event XML data.

        Args:
            xml_string (str): Windows authentication event's event data.

        Returns:
            WindowsLoginEventData: An object of WindowsLoginEventData.
        """
        root = ET.fromstring(xml_string)

        eventdata_root = None
        for child in root:
            if "EventData" in child.tag:
                eventdata_root = child
                break

        winlogineventdata = WindowsLoginEventData()

        for child in eventdata_root:
            try:
                key = child.attrib["Name"]
                if key == "TargetUserName":
                    winlogineventdata.username = child.text
                elif key == "TargetDomainName":
                    winlogineventdata.domain = child.text
                elif key == "TargetLogonId":
                    winlogineventdata.session_id = child.text
                elif key == "LogonType":
                    winlogineventdata.logon_type = int(child.text or 0)
                elif key == "WorkstationName":
                    winlogineventdata.source_hostname = child.text
                elif key == "ProcessId":
                    winlogineventdata.process_id = child.text
                elif key == "ProcessName":
                    winlogineventdata.process_name = child.text
                elif key == "IpAddress":
                    winlogineventdata.source_ip = child.text
                elif key == "IpPort":
                    try:
                        winlogineventdata.source_port = int(child.text)
                    except ValueError:
                        winlogineventdata.source_port = 0
            except KeyError as exception:
                log.error("[%s] Key name not found. %s", self.NAME, str(exception))
                continue

        log.info("event data %s", str(winlogineventdata.__dict__))
        return winlogineventdata

    def annotate_events(self, df: pd.DataFrame, output: AnalyzerOutput) -> None:
        """Annotate matching Windows events.

        Args:
            df (pd.DataFrame): Pandas dataframe of the events.
            output (AnalyzerOutput): Analyzer output for Windows login events.
        """
        event_ids = []

        if df.empty:
            log.info("[%s] Dataframe is empty", self.NAME)
            return

        if not output:
            log.info("[%s] Analyzer output is None", self.NAME)
            return

        if not output.attributes:
            log.info("[%s] No output attributes to annotate", self.NAME)
            return

        try:
            for authsummary in output.attributes:
                bruteforce_logins = authsummary.brute_forces
                if not bruteforce_logins:
                    continue

                for login in bruteforce_logins:
                    login_session_df = df[df["session_id"] == login.session_id]
                    if login_session_df.empty:
                        continue

                    for _, row in login_session_df.iterrows():
                        event_id = row.get("event_id" or None)
                        if event_id:
                            event_ids.append(event_id)
        except KeyError as exception:
            log.error("[%s] Missing expected key. %s", self.NAME, str(exception))
            return

        if not event_ids:
            log.info("[%s] No OpenSearch event IDs to annotate", self.NAME)
            return
        log.info("[%s] Annotating %d events", self.NAME, len(event_ids))

        # Only annotate matching events.
        query_string = ""
        for event_id in event_ids:
            if not query_string:
                query_string = f"_id:{event_id}"
            else:
                query_string += f" OR _id:{event_id}"
        log.debug("[%s] Annotation query string %s", self.NAME, query_string)

        return_fields = ["timestamp", "computer_name", "event_identifier"]

        if not query_string:
            log.info("[%s] No query string to run", self.NAME)
            return

        try:
            annotation_events = self.event_stream(
                query_string=query_string, return_fields=return_fields
            )
            if not annotation_events:
                log.info("[%s] No events for query.", self.NAME)
                return

            for event in annotation_events:
                event.add_label("windows_bruteforce")
                event.add_star()
                event.commit()
        except ValueError as exception:
            log.error(
                "[%s] Value error encountered getting events. %s",
                self.NAME,
                str(exception),
            )

    def run(self) -> str:
        """Entry point for the analyzer.

        Returns:
            str: Analyzer output as string.
        """
        query_string = (
            "source_name:Microsoft-Windows-Security-Auditing AND "
            "(event_identifier:4624 OR event_identifier:4625 "
            "OR event_identifier:4634)"
        )
        return_fields = ["timestamp", "computer_name", "event_identifier", "xml_string"]

        events = None
        try:
            events = self.event_stream(
                query_string=query_string, return_fields=return_fields
            )
        except KeyError as exception:
            log.error(
                "[%s] Error getting events from OpenSearch. %s",
                self.NAME,
                str(exception),
            )
            return self._empty_analyzer_output(
                status="Failed", message="Failed getting events from OpenSearch"
            )
        if not events:
            return self._empty_analyzer_output(
                status="Success", message="No events matching the query"
            )

        # windows_login_events is a list of WindowsLoginEventData dictionary
        windows_login_events = []

        for event in events:
            _event_identifier = int(event.source.get("event_identifier" or 0))
            # We only want to process events related to authentication.
            if _event_identifier not in [4624, 4625, 4634]:
                log.error("[%s] Error getting event ID.", self.NAME)
                continue

            # Extracted field validation before parsing xml_string
            # Using the timestamp extracted by Plaso
            _timestamp = int(event.source.get("timestamp" or 0))
            if not _timestamp:
                log.error(
                    "[%s] Error getting timestamp from OpenSearch event.", self.NAME
                )
                continue

            _hostname = event.source.get("computer_name" or "")
            if not _hostname:
                log.error(
                    "[%s] Error getting computer name from OpenSearch event.", self.NAME
                )
                continue

            _xml_string = event.source.get("xml_string" or "")
            if not _xml_string:
                log.error(
                    "[%s] Error getting xml_string from OpenSearch event.", self.NAME
                )
                continue

            # Note; _parse_xml_string always returns WindowsLoginEventData
            windows_login_event = self.parse_xml_string(_xml_string)
            if not windows_login_event:
                log.error("[%s] Error parsing xml_string.", self.NAME)
                continue
            windows_login_event.eid = _event_identifier

            # Updating the fields needed for brute force analysis
            windows_login_event.event_id = event.event_id
            windows_login_event.timestamp = int(_timestamp / 1000000)
            windows_login_event.hostname = _hostname

            # We are assuming authenticaiton to be password-based authenticaiton
            # TODO(rmaskey): Set appropriate authentication method.
            windows_login_event.auth_method = "password"

            if _event_identifier == 4624:
                windows_login_event.event_type = "authentication"
                windows_login_event.auth_result = "success"

                # We only want to analyze events relevant for brute force logons
                # LogonType 2 - Local interactive logon
                # LogonType 3 - Network logon
                # LogonType 10 - Remote interactive logon (RDP)
                if windows_login_event.logon_type not in self.BRUTEFORCE_LOGON_TYPE:
                    continue
            elif _event_identifier == 4625:
                windows_login_event.event_type = "authentication"
                windows_login_event.auth_result = "failure"

                # We only want to analyze events relevant for brute force logons
                # LogonType 2 - Local interactive logon
                # LogonType 3 - Network logon
                # LogonType 10 - Remote interactive logon (RDP)
                if windows_login_event.logon_type not in self.BRUTEFORCE_LOGON_TYPE:
                    continue
            elif _event_identifier == 4634:
                windows_login_event.event_type = "disconnection"

            windows_login_events.append(windows_login_event.__dict__)

        log.info(
            "[%s] Total number of Windows authentication events: %d",
            self.NAME,
            len(windows_login_events),
        )

        df = pd.DataFrame(windows_login_events)
        if df.empty:
            log.info("[%s] No dataframe for Windows authentication events.", self.NAME)
            return self._empty_analyzer_output(
                status="Success",
                message="No dataframe for Windows authentication events.",
            )

        # run brute force analyzer
        try:
            bfa = BruteForceAnalyzer()

            # NOTE: Setting threshold to 2 due to duplicate events.
            bfa.set_success_threshold(2)
            output = bfa.run(df)
            if not output:
                log.info("[%s] No analyzer output.", self.NAME)
                return self._empty_analyzer_output(
                    status="Failed",
                    message="No output from brute force analyzer",
                )

            output.analyzer_identifier = "analyzer.bruteforce.windows"
            output.analyzer_name = "Windows BruteForce Analyzer"

            self.annotate_events(df, output)

            return str(output)
        except (AuthAnalyzerException, AnalyzerOutputException) as exception:
            log.error(
                "[%s] Error analyzing Windows authentication events. %s",
                self.NAME,
                str(exception),
            )
            return self._empty_analyzer_output(
                status="Failed", message="Unable to run analyzer."
            )


manager.AnalysisManager.register_analyzer(WindowsLoginBruteForcePlugin)
