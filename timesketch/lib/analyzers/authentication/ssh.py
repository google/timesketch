"""Analyzers for SSH authentication events."""

from typing import List

import hashlib
import logging
import pandas as pd

from flask import current_app

from timesketch.lib.analyzers.interface import BaseAnalyzer
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.interface import AnalyzerOutput
from timesketch.lib.analyzers.authentication.interface import BruteForceAnalyzer

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
    """

    def __init__(self):
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

    def calculate_session_id(self):
        """Calculates pseudo session ID for SSH authentication event."""

        session_id_data = (
            f"{self.hostname}|{self.username}|{self.source_ip}|{self.source_port}"
        )

        hasher = hashlib.new("sha256")
        hasher.update(str.encode(session_id_data))

        self.session_id = hasher.hexdigest()


class SSHBruteForceAnalyzer(BaseAnalyzer, BruteForceAnalyzer):
    """Class for SSH authentication analysis."""

    NAME = "SSHBruteForceAnalyzer"
    DISPLAY_NAME = "SSH Brute Force Analyzer"
    DESCRIPTION = (
        "SSH brute force analyzer that checks for login/logoff and session duration"
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

    def __init__(
        self, index_name: str, sketch_id: int, timeline_id: int = None
    ) -> None:
        super().__init__(index_name, sketch_id, timeline_id)
        self._timesketch_instance = current_app.config.get(
            "EXTERNAL_HOST_URL", "https://localhost"
        )
        self._index = index_name
        self._sketch_id = sketch_id or 0
        self._timeline_id = timeline_id or 0

    def run(self):
        """Entry point for the analyzer."""

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
        log.info("[%s] %d SSH authentication events processed", self.NAME, len(records))

        # Setting analyzer metadata
        self.set_analyzer_metadata(
            timesketch_instance=self._timesketch_instance,
            sketch_id=self._sketch_id,
            timeline_id=self._timeline_id,
        )

        # Create a Pandas DataFrame from the list of records
        df = pd.DataFrame(records)

        # Check if the DataFrame is empty
        if df.empty:
            log.info("[%s] No SSH authentication events", self.NAME)
            return self.generate_empty_analyzer_output(
                message="No SSH authentication events"
            )

        # Add required columns to the dataframe and set the dataframe
        df["domain"] = ""
        df["source_hostname"] = ""
        self.set_dataframe(df)

        # Set brute force threshold for SSH
        self.set_success_threshold(threshold=1)

        # Check if the output is empty
        output = self.start_bruteforce_analysis()
        if not output:
            output = self.generate_empty_analyzer_output(
                message=f"No verdict for {len(records)} SSH authenticaiton events."
            )
            return str(output)

        # Annotate the bruteforce events
        events = self.event_stream(
            query_string=self.SEARCH_QUERY, return_fields=self.EVENT_FIELDS
        )

        try:
            self.annotate_events(events=events, output=output)
        except (ValueError, TypeError) as e:
            log.error("[%s] Unable to annotate. %s", self.NAME, str(e))

        # TODO(rmaskey): Have a better way to handle result_attributes
        # result_attributes is a dict containing list of objects and not required for
        # user readable output.
        output.result_attributes = {}
        return str(output)

    def annotate_events(self, events: List, output: AnalyzerOutput) -> None:
        """Annotates the matching events.

        Args:
            evnets (List): OpenSearch events.
            output (AnalyzerOutput): Output of the analyzer.
        """

        if self.df.empty:
            raise ValueError("dataframe is empty")

        if not events:
            raise ValueError("events is empty")

        if not output:
            raise ValueError("AnalyzerOutput is none")

        if not isinstance(output, AnalyzerOutput):
            raise TypeError("Param output is not of type AnalyzerOutput")

        # We want to check result_attributes is set and have "bruteforce" attribute
        if not output.result_attributes:
            log.info("[%s] No result_attributes to annotate", self.NAME)
            return

        if (
            not isinstance(output.result_attributes, dict)
            or "bruteforce" not in output.result_attributes
        ):
            log.info("[%s] No bruteforce attributes in result_attributes", self.NAME)
            return

        # Generate the event IDs for tagging
        event_ids = []

        for authsummary in output.result_attributes["bruteforce"]:
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
                session_df = self.df[self.df["session_id"] == login.session_id]
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
            log.info("[%s] No events to annotate", self.NAME)
            return

        log.info("[%s] Annotating %d events", self.NAME, len(event_ids))
        for event in events:
            if event.event_id in event_ids:
                log.debug("[%s] Annotating event ID %s", self.NAME, event.event_id)
                event.add_label("ssh_bruteforce")
                event.add_star()
                event.commit()


manager.AnalysisManager.register_analyzer(SSHBruteForceAnalyzer)
