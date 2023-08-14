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
"""Analyzers for SSH authentication events."""

import hashlib
import logging
import textwrap
import pandas as pd


from timesketch.lib.analyzers.interface import BaseAnalyzer, AnalyzerOutput
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.authentication.utils import BruteForceUtils

log = logging.getLogger("timesketch")


class SSHEventData:
    """Class for storing SSH authentication data.

    Attributes:
        event_id (str): OpenSearch event ID of an authentication event.
        timestamp (int): Authentication event timestamp in Unix seconds.
        hostname (str): Hostname of the system.
        pid (int): Process ID of the SSHD process.
        event_type (str): Type of authentication event. Valid values are
            "authentication" or "disconnection".
        authentication_method (str): SSH authentication method - password or key.
        authentication_result (str): "success" or "failure"
        source_ip (str): IP address in the authentication event.
        source_port (str): Source port in the authentication event.
        username (str): Username in the authentication event.
        session_id (str): Pseudo session ID calculated from log line.
    """

    def __init__(self) -> None:
        """Initialize class."""

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
        self.session_id = ""

    def calculate_session_id(self) -> None:
        """Calculates pseudo session ID for SSH authentication event."""

        session_id_data = (
            f"{self.hostname}|{self.username}|{self.source_ip}|{self.source_port}"
        )

        hasher = hashlib.new("sha256")
        hasher.update(str.encode(session_id_data))

        self.session_id = hasher.hexdigest()


class SSHBruteForceAnalyzer(BaseAnalyzer):
    """Class for SSH authentication analysis."""

    # The time duration before a successful login to evaluate for brute force activity.
    BRUTE_FORCE_WINDOW = 3600

    # The minimum number of failed events that must occur to be considered for brute
    # force activity.
    BRUTE_FORCE_MIN_FAILED_EVENT = 20

    # The minimum duration where an attacker accessed the host after a successful
    # brute force login would be considered as an interactive access.
    BRUTE_FORCE_MIN_ACCESS_WINDOW = 300

    NAME = "SSHBruteForceAnalyzer"
    DISPLAY_NAME = "SSH Brute Force Analyzer"
    DESCRIPTION = textwrap.dedent(
        """SSH brute force authentication analysis. It checks for multiple failed
        authentication events before a successful authentication.

        The following thresholds are used in the analyzer:
            - Minimum number of failed events: {0}
            - Brute force window before successful login event: {1}
            seconds""".format(
            BRUTE_FORCE_MIN_FAILED_EVENT, BRUTE_FORCE_WINDOW
        )
    )

    DEPENDENCIES = frozenset(["feature_extraction"])

    SEARCH_QUERY = (
        "reporter:sshd AND (body:*Accepted* OR body:*Failed* OR "
        "(body:*Disconnected* AND NOT body:*preauth*))"
    )

    EVENT_FIELDS = [
        "event_id",
        "timestamp",
        "hostname",
        "pid",
        "authentication_method",
        "username",
        "ip_address",
        "port",
        "body",
    ]

    # Create a BruteForceAnalyzer instance to handle the auth data analysis
    brute_force_analyzer = BruteForceUtils(
        BRUTE_FORCE_WINDOW, BRUTE_FORCE_MIN_FAILED_EVENT, BRUTE_FORCE_MIN_ACCESS_WINDOW
    )

    def __init__(self, index_name, sketch_id, timeline_id=None) -> None:
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Opensearch index name
            sketch_id: Sketch ID
            timeline_id: Timeline ID
        """
        self.index_name = index_name
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)

    def run(self) -> str:
        """Entry point for the analyzer.

        Returns:
            str: Returns AnalyzerOutput as a string.
        """

        # Store a list of SSHEventData
        records = []

        # Get the events from Timesketch
        events = self.event_stream(
            query_string=self.SEARCH_QUERY, return_fields=self.EVENT_FIELDS
        )

        # Iterate over the events
        for event in events:
            # Create a new SSHEventData object
            event_data = SSHEventData()

            # Set the event data
            event_data.event_id = event.event_id
            event_data.timestamp = int(event.source.get("timestamp") / 1000000)
            event_data.hostname = event.source.get("hostname")
            event_data.pid = event.source.get("pid")
            event_data.authentication_method = event.source.get("authentication_method")
            event_data.username = event.source.get("username")
            event_data.source_ip = event.source.get("ip_address")
            event_data.source_port = event.source.get("port")

            # Extract event_type and authentication_result based on the body message
            body = event.source.get("body", "")
            if not body:
                raise ValueError("body is empty")

            if body.startswith("Accepted"):
                event_data.event_type = "authentication"
                event_data.authentication_result = "success"
            elif body.startswith("Failed"):
                event_data.event_type = "authentication"
                event_data.authentication_result = "failure"
            elif body.startswith("Disconnected"):
                event_data.event_type = "disconnection"
                event_data.authentication_result = ""
            else:
                event_data.event_type = "unknown"
                event_data.authentication_result = "unknown"

            # Calculate the session ID
            event_data.calculate_session_id()

            # Append the event data to the list
            records.append(event_data.__dict__)

        # Log the number of SSH authentication events processed
        log.debug(
            "[%s] %d SSH authentication events processed", self.NAME, len(records)
        )

        # Create a Pandas DataFrame from the list of records
        df = pd.DataFrame(records)

        # Check if the DataFrame is empty
        if df.empty:
            log.debug("[%s] No SSH authentication events", self.NAME)
            self.output.result_summary = "No SSH authentication events"
            self.output.result_priority = "NOTE"
            self.output.result_status = "SUCCESS"
            return str(self.output)

        # Add required columns to the dataframe and set the dataframe
        df["domain"] = ""
        df["source_hostname"] = ""

        try:
            self.brute_force_analyzer.set_dataframe(df)
        except (AttributeError, TypeError) as exception:
            raise exception

        # Set brute force threshold for SSH
        self.brute_force_analyzer.set_success_threshold(threshold=1)

        # Check if the output is empty
        result = self.brute_force_analyzer.start_bruteforce_analysis(self.output)
        if isinstance(result, AnalyzerOutput):
            self.output = result
        else:
            self.output.result_summary = (
                f"No verdict for {len(records)} SSH authentication events."
            )
            self.output.result_priority = "NOTE"
            self.output.result_status = "SUCCESS"
            return str(self.output)

        # Annotate the bruteforce events
        events = self.event_stream(
            query_string=self.SEARCH_QUERY, return_fields=self.EVENT_FIELDS
        )

        try:
            self.annotate_events(events=events)
        except (ValueError, TypeError) as e:
            log.error("[%s] Unable to annotate. %s", self.NAME, str(e))

        # TODO(rmaskey): Have a better way to handle result_attributes
        # result_attributes is a dict containing list of objects and not required for
        # user readable output.
        self.output.result_attributes = {}
        return str(self.output)

    def annotate_events(self, events) -> None:
        """Annotates the matching events.

        Args:
            events (Generator): OpenSearch events.

        Raises:
            ValueError: If required values are empty.
            TypeError: If the required type is not matched.
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

                for _, row in session_df.iterrows():
                    event_id = row.get("event_id", "")
                    if event_id:
                        event_ids.append(event_id)

        if not event_ids:
            log.debug("[%s] No events to annotate", self.NAME)
            return

        log.debug("[%s] Annotating %d events", self.NAME, len(event_ids))
        for event in events:
            if event.event_id in event_ids:
                log.debug("[%s] Annotating event ID %s", self.NAME, event.event_id)
                event.add_tags(["ssh_bruteforce"])
                event.add_star()
                event.commit()


manager.AnalysisManager.register_analyzer(SSHBruteForceAnalyzer)
