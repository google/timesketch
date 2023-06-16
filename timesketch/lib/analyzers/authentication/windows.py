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
"""Analyzers for Windows authentication events."""

from typing import List

import logging
import textwrap

import pandas as pd

from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.authentication.utils import BruteForceUtils
from timesketch.lib.analyzers.interface import AnalyzerOutput, BaseAnalyzer

log = logging.getLogger("timesketch")


class WindowLoginEventData:
    """Class for storing Windows authentication data.

    Attributes:
        event_id (str): OpenSearch event ID of an authentication event.
        timestamp (int): Authentication event timestamp in Unix second.
        hostname (str): Hostname of the system.
        pid (int): Process ID of the authenticating process.
        event_type (str): Type of authentication event. Valid values are
            "authentication" or "disconnection".
        authentication_method (str): Windows authentication method. Default is password.
        authentication_result (str): "success" or "failure"
        source_ip (str): IP address of authentication event.
        source_port (str): Source port in authentication port.
        username (str): Username in authentication event.
        domain (str): Domain name of authenticating user. Unused as the information is
            not available for Event ID 4634 (logoff).
        session_id (str): Session ID for successful authentication event.
        source_hostname (str): Source hostname of authenticating hostname.
        eid (int): Windows event log event ID.
        logon_type (int): Windows authentication event logon type.
        login_id (int): Windows authentication logon ID.
        process_name (str): Process name of the authenticating process.
    """

    def __init__(self) -> None:
        """Initialize WindowsLoginEventData object."""

        self.event_id = ""
        self.timestamp = 0
        self.hostname = ""
        self.pid = 0
        self.event_type = ""
        self.authentication_method = ""
        self.authentication_result = ""
        self.source_ip = ""
        self.source_port = ""
        self.username = ""
        self.domain = ""
        self.session_id = ""
        self.source_hostname = ""
        self.eid = 0
        self.logon_type = 0
        self.logon_id = 0
        self.process_name = ""


class WindowsLoginBruteForceAnalyzer(BaseAnalyzer):
    """Class for Windows authentication analysis."""

    # The maximum of the successful authentication events should exist during the
    # analysis window to qualify as a successful brute force activity.
    SUCCESS_THRESHOLD = 2

    # The authentication logon types we are interested in processing.
    BRUTE_FORCE_LOGON_TYPE = [2, 3, 10]

    # The time duration in seconds to evaluate brute force activity
    BRUTE_FORCE_WINDOW = 3600

    # The minimum number of failed logins that must occur in the brute force window.
    BRUTE_FORCE_MIN_FAILED_EVENT = 20

    # The minimum duration where an attacker accessed the host after a successful
    # brute force login would be considered as an interactive access.
    BRUTE_FORCE_MIN_ACCESS_WINDOW = 30

    NAME = "WindowsBruteForceAnalyser"
    DISPLAY_NAME = "Windows Login Brute Force Analyzer"
    DESCRIPTION = textwrap.dedent(
        f"""Windows login brute force analysis for logon types 2, 3, and 10. It checks
        for multiple failed login events followed by success a login event.

        The analyzer uses the following threshold values to determine a successful
        brute force activity.
            - {BRUTE_FORCE_WINDOW} seconds brute force windows before a successful
             login.
            - {BRUTE_FORCE_MIN_FAILED_EVENT} failed login events in the brute force
             window"""
    )

    DEPENDENCIES = frozenset(["feature_extraction"])

    SEARCH_QUERY = (
        "source_name:Microsoft-Windows-Security-Auditing AND"
        " (event_identifier:4624 OR event_identifier:4625 OR"
        " event_identifier:4634)"
    )

    EVENT_FIELDS = [
        "event_id",
        "timestamp",
        "event_identifier",
        "computer_name",
        "ip_address",
        "port",
        "process_id",
        "username",
        "domain",
        "logon_type",
        "logon_id",
        "workstation_name",
        "process_name",
    ]

    def __init__(
        self, index_name: str, sketch_id: int, timeline_id: int = None
    ) -> None:
        """Initialize Windows brute force analyzer.

        index_name (str): TimeSketch index name.
        sketch_id (int): TimeSketch sketch ID.
        timeline_id (ind): TimeSketch timeline ID.
        """

        super().__init__(index_name, sketch_id, timeline_id)
        self.brute_force_analyzer = BruteForceUtils(
            self.BRUTE_FORCE_WINDOW,
            self.BRUTE_FORCE_MIN_FAILED_EVENT,
            self.BRUTE_FORCE_MIN_ACCESS_WINDOW,
        )

    def run(self) -> str:
        """Entry point for the analyzer.

        Returns:
            str: Analyzer output as string.

        Raises:
            TypeError: If logon_type is None.
            ValueError: If logon_type is not numeric value.
        """

        # Store a list of WindowsLoginEventData
        records = []

        # Get the events from TimeSketch
        events = self.event_stream(
            query_string=self.SEARCH_QUERY, return_fields=self.EVENT_FIELDS
        )

        # Iterate over the events
        event_counter = 0
        for event in events:
            # Create a new WindowsLoginEventData object
            event_data = WindowLoginEventData()

            # Set the event data
            event_data.event_id = event.event_id
            event_data.timestamp = int(event.source.get("timestamp") / 1000000)
            event_data.hostname = event.source.get("computer_name")
            event_data.username = event.source.get("username")
            event_data.domain = event.source.get("domain")
            event_data.source_ip = event.source.get("ip_address")
            event_data.source_port = event.source.get("port")
            event_data.source_hostname = event.source.get("workstation_name")
            event_data.session_id = event.source.get("logon_id")
            event_data.eid = event.source.get("event_identifier")

            # Handle events without logon_type
            try:
                event_data.logon_type = int(event.source.get("logon_type"))
            except (ValueError, TypeError) as e:
                log.debug("[%s] Unknown value for logon_type. %s", self.NAME, str(e))
                event_data.logon_type = 0

            event_data.logon_id = event.source.get("logon_id")
            event_data.pid = event.source.get("process_id", 0)
            event_data.process_name = event.source.get("process_name")

            # Interpret the event data and extract required data
            if event_data.eid == 4624:
                if event_data.logon_type not in self.BRUTE_FORCE_LOGON_TYPE:
                    continue
                # NOTE: Windows does not capture the authentication method.
                # Setting the authentication method as password
                event_data.authentication_method = "password"
                event_data.authentication_result = "success"
                event_data.event_type = "authentication"
            elif event_data.eid == 4625:
                if event_data.logon_type not in self.BRUTE_FORCE_LOGON_TYPE:
                    continue
                # NOTE: Windows does not capture the authentication method.
                # Setting the authentication method as password
                event_data.authentication_method = "password"
                event_data.authentication_result = "failure"
                event_data.event_type = "authentication"
            elif event_data.eid == 4634:
                event_data.authentication_method = ""
                event_data.authentication_result = ""
                event_data.event_type = "disconnection"
            else:
                event_data.authentication_method = ""
                event_data.authentication_result = ""
                event_data.event_type = ""
                continue

            records.append(event_data.__dict__)
            event_counter += 1

        # Log the number of Windows authentication events process
        log.debug(
            "[%s] %d of %d  Windows authentication events processed",
            self.NAME,
            len(records),
            event_counter,
        )

        # Create a Pandas DataFrame from the list of records
        df = pd.DataFrame(records)
        if df.empty:
            log.debug("[%s] No Windows authentication events", self.NAME)
            self.output.result_summary = "No Windows authentication events"
            self.output.result_priority = "NOTE"
            self.output.result_status = "SUCCESS"
            return str(self.output)

        # Add required dataframe columns
        # Windows domain is removed from the analysis as domain is not capture in
        # the event IDs used for the analysis.
        df["domain"] = ""

        try:
            self.brute_force_analyzer.set_dataframe(df)
        except (AttributeError, TypeError) as exception:
            raise exception

        # Set brute force threshold for Windows login
        # NOTE: We are setting successful login count to 2 as we noticed two successful
        # events in timesketch.
        log.debug(
            "[%s] Setting brute force success threshold to %d",
            self.NAME,
            self.SUCCESS_THRESHOLD,
        )
        self.brute_force_analyzer.set_success_threshold(
            threshold=self.SUCCESS_THRESHOLD
        )

        # Check if the output is empty
        result = self.brute_force_analyzer.start_bruteforce_analysis(self.output)
        if isinstance(result, AnalyzerOutput):
            self.output = result
        else:
            log.debug("[%s] No analyzer output", self.NAME)
            self.output.result_summary = (
                f"No verdict for {len(records)} Windows authentication events"
            )
            self.output.result_priority = "NOTE"
            self.output.result_status = "SUCCESS"
            return str(self.output)

        # Annotate the brute force events
        events = self.event_stream(
            query_string=self.SEARCH_QUERY, return_fields=self.EVENT_FIELDS
        )

        try:
            self.annotate_events(events=events)
        except (ValueError, TypeError) as e:
            log.debug("[%s] Unable to annotate. %s", self.NAME, str(e))

        # TODO(rmaskey): Have a better way to handle result_attributes
        # result_attributes is a dict containing list of objects and not required for
        # user readable output.
        self.output.result_attributes = {}
        return str(self.output)

    def annotate_events(self, events: List) -> None:
        """Annotates the matching events.

        Args:
            events (List): OpenSearch events.

        Raises:
            ValueError: If events and analyzer output is empty.
            TypeError: If output is not of type AnalyzerOutput.
        """

        if not events:
            raise ValueError("events is empty")

        if not self.output:
            raise ValueError("AnalyzerOutput is none")

        if not isinstance(self.output, AnalyzerOutput):
            raise TypeError("Param output is not of type AnalyzerOutput")

        # We want to check result_attributes is set and have "bruteforce" attribute
        if not self.output.result_attributes:
            log.debug("[%s] No result_attributes to annotate", self.NAME)
            return

        if (
            not isinstance(self.output.result_attributes, dict)
            or "bruteforce" not in self.output.result_attributes
        ):
            log.debug("[%s] No bruteforce attributes in result_attributes", self.NAME)
            return

        # Generate the event IDs for tagging
        event_ids = []

        for authsummary in self.output.result_attributes["bruteforce"]:
            log.debug(
                "[%s] Checking annotation for %s", self.NAME, authsummary.source_ip
            )
            if (
                not isinstance(authsummary.summary, dict)
                or "bruteforce" not in authsummary.summary
            ):
                log.debug(
                    "[%s] No summary data or missing bruteforce attribute", self.NAME
                )
                continue

            for login in authsummary.summary["bruteforce"]:
                session_df = self.brute_force_analyzer.df[
                    self.brute_force_analyzer.df["session_id"] == login.session_id
                ]
                if session_df.empty:
                    log.debug(
                        "[%s] No session ID %s in dataframe",
                        self.NAME,
                        login.session_id,
                    )
                    continue

                # We only want to tag brute force login and logout events.
                # We don't want to tag failed authentication events before the
                # successful login event.
                for _, row in session_df.iterrows():
                    event_id = row.get("event_id", "")
                    event_identifier = row.get("eid")
                    if event_id and (event_identifier in [4624, 4634]):
                        event_ids.append(event_id)

        if not event_ids:
            log.debug("[%s] No events to annotate", self.NAME)
            return

        log.debug("[%s] Annotating %d events", self.NAME, len(event_ids))
        for event in events:
            if event.event_id in event_ids:
                log.debug("[%s] Annotating event ID %s", self.NAME, event.event_id)
                event.add_tags(["windows_bruteforce"])
                event.add_star()
                event.commit()


manager.AnalysisManager.register_analyzer(WindowsLoginBruteForceAnalyzer)
