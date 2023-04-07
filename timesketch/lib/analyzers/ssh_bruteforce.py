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
"""Sketch analyzer plugin for SSH authentication."""

from __future__ import unicode_literals

from datetime import datetime
from typing import List

import hashlib
import logging
import re

import pandas as pd
import pyparsing

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.analyzer_output import AnalyzerOutput
from timesketch.lib.analyzers.analyzer_output import AnalyzerOutputException
from timesketch.lib.analyzers.auth import AuthAnalyzerException
from timesketch.lib.analyzers.auth import BruteForceAnalyzer

log = logging.getLogger("timesketch")


class SSHEventData:
    """SSH authentication event.

    Attributes:
        event_id (str): OpenSearch internal ID.
        timestamp (str): Event timestamp in Unix seconds.
        date (str): Event date in the format yyyy-mm-dd.
        time (str): Event time in the format HH:MM:SS.
        hostname (str): Hostname of the system.
        pid (int): Process ID of the SSH process.
        event_key (str): Event key of SSH event i.e. accepted, failed,
                disconnected.
        event_type (str): SSH event type i.e. authentication or disconnection.
        auth_method (str): SSH authentication method. Valid values are password
                or publickey.
        domain (str): Not used for SSHEventData. The field is required by
                AuthAnalyzer.
        username (str): Username that authenticated to SSH service.
        source_ip (str): Source IP of the device that initiated authentication.
        source_port (str): Source port of the device that initiated
                authentication.
        source_hostname (str): Not used for SSH. This field is required by
                AuthAnalyzer.
        session_id (str): Pseudo session ID created for tracking logon/logoff
                events.
    """

    def __init__(self):
        self.event_id = ""  # OpenSearch event_id
        self.timestamp = 0
        self.date = "1970-01-01"
        self.time = "00:00:00"
        self.hostname = ""
        self.pid = 0
        self.event_key = ""
        self.event_type = ""
        self.auth_method = ""
        self.auth_result = ""
        self.domain = ""  # Required for consistency with Windows
        self.username = ""
        self.source_ip = ""
        self.source_port = ""
        self.source_hostname = ""
        self.session_id = ""

    def calculate_session_id(self) -> None:
        """Calculates pseudo session_id for SSH authentication event."""
        hash_data = (
            f"{self.date}|{self.hostname}|{self.username}|{self.source_ip}|"
            f"{self.source_port}"
        )

        hasher = hashlib.new("sha256")
        hasher.update(str.encode(hash_data))
        self.session_id = hasher.hexdigest()


class SSHBruteForcePlugin(interface.BaseAnalyzer):
    """Analyzer for SSH authentication"""

    NAME = "SSHBruteForcePlugin"
    DISPLAY_NAME = "SSH Brute Force Analyzer"
    DESCRIPTION = "Analyzer for successful SSH brute force login"

    _PID = pyparsing.Word(pyparsing.nums).setResultsName("pid")
    _AUTHENTICATION_METHOD = (
        pyparsing.Keyword("password") | pyparsing.Keyword("publickey")
    ).setResultsName("auth_method")
    _USERNAME = pyparsing.Word(pyparsing.printables).setResultsName("username")
    _SOURCE_IP = pyparsing.Word(pyparsing.printables).setResultsName(
            "source_ip")
    _SOURCE_PORT = pyparsing.Word(pyparsing.nums, max=5).setResultsName(
            "source_port")
    _PROTOCOL = pyparsing.Word(pyparsing.printables).setResultsName("protocol")
    _FINGERPRINT_TYPE = pyparsing.Word(pyparsing.alphanums).setResultsName(
            "fingerprint_type"
    )
    _FINGERPRINT = pyparsing.Word(pyparsing.printables).setResultsName(
            "fingerprint")

    # Timesketch message field grammar
    _LOGIN_GRAMMAR = (
        pyparsing.Literal("Accepted")
        + _AUTHENTICATION_METHOD
        + pyparsing.Literal("for")
        + _USERNAME
        + pyparsing.Literal("from")
        + _SOURCE_IP
        + pyparsing.Literal("port")
        + _SOURCE_PORT
        + _PROTOCOL
        + pyparsing.Optional(pyparsing.Literal(":")
                             + _FINGERPRINT_TYPE
                             + _FINGERPRINT)
        + pyparsing.StringEnd()
    )

    # Timesketch message field grammar
    _FAILED_GRAMMER = (
        pyparsing.Optional(
            pyparsing.Literal("[")
            + pyparsing.Word(pyparsing.nums)
            + pyparsing.Literal("]:")
        )
        + pyparsing.Literal("Failed")
        + _AUTHENTICATION_METHOD
        + pyparsing.Literal("for")
        + pyparsing.Optional(pyparsing.Literal("invalid")
                             + pyparsing.Literal("user"))
        + _USERNAME
        + pyparsing.Literal("from")
        + _SOURCE_IP
        + pyparsing.Literal("port")
        + _SOURCE_PORT
        + _PROTOCOL
    )

    # Timesketch message field grammar
    _DISCONNECT_GRAMMAR = (
        pyparsing.Literal("Disconnected")
        + pyparsing.Literal("from")
        + pyparsing.Literal("user")
        + _USERNAME
        + _SOURCE_IP
        + pyparsing.Literal("port")
        + _SOURCE_PORT
    )

    MESSAGE_GRAMMAR = {
        "accepted": _LOGIN_GRAMMAR,
        "failed": _FAILED_GRAMMER,
        "disconnected": _DISCONNECT_GRAMMAR,
    }

    # SSHD_KEYWORD_RE is regular expression is used to identify the interesting
    # SSH authentication events to process.
    #
    # We are only interested in parsing Accepted, Failed, and Disconnected
    # messages as specified in MESSAGE_GRAMMAR
    SSHD_KEYWORD_RE = re.compile(r"\s*([^\s]+)\s+.*")

    # IGNORE_ATTRIBUTE_ERROR holds the error messages that we can ignore
    # while parsing event_body using SSHD_KEYWORD_RE.
    IGNORE_ATTRIBUTE_ERROR = ["'NoneType' object has no attribute 'group'"]

    def annotate_events(self, events: List, df: pd.DataFrame,
                       output: AnalyzerOutput) -> None:
        """Annotate matching events.

        Args:
            events (List[]): OpenSearch events.
            df (pd.DataFrame): Pandas dataframe of the events.
            output (AnalyzerOutput): Output of brute force analyzer.
        """
        event_ids = []

        if df.empty:
            log.info("[%s] Dataframe is empty", self.NAME)
            return

        if not output:
            log.info("[%s] Analyzer output is None")
            return

        if not output.attributes:
            log.info("[%s] No output attributes")
            return

        try:
            for authdatasummary in output.attributes:
                bruteforce_logins = authdatasummary.brute_forces
                if not bruteforce_logins:
                    continue

                for login in bruteforce_logins:
                    login_session_df = df[df["session_id"] == login.session_id]
                    if login_session_df.empty:
                        continue

                    for _, row in login_session_df.iterrows():
                        event_id = row.get("event_id", None)
                        if event_id:
                            event_ids.append(event_id)
        except KeyError as exception:
            log.error("[%s] Missing expected key: %s", self.NAME, str(exception))
            return

        if not event_ids:
            log.info("[%s] No events to annotate", self.NAME)
            return
        log.info(
            "[%s] %d events to annotate: [%s]",
            self.NAME,
            len(event_ids),
            " ".join(event_ids),
        )

        if not event_ids:
            return

        for event in events:
            if event.event_id in event_ids:
                log.debug("[%s] Annotating event id %s", self.NAME, event.event_id)
                event.add_label("ssh_bruteforce")
                event.add_star()
                event.commit()

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """
        query_string = (
            "reporter:sshd AND (body:*Accepted* OR body:*Failed*"
            " OR (body:*Disconnected* AND NOT body:*preauth*))"
        )
        return_fields = ["timestamp", "hostname", "pid", "body"]

        events = self.event_stream(
            query_string=query_string, return_fields=return_fields
        )

        # ssh_records holds the SSHEventData dictionaries.
        # This will be used to create pandas dataframe.
        ssh_records = []

        for event in events:
            event_timestamp = float(event.source.get("timestamp") / 1000000)
            event_hostname = event.source.get("hostname")
            event_pid = event.source.get("pid")
            event_body = event.source.get("body")

            # We are not parsing the body if it contains disconnect message for
            # preauth disconnection
            if "Disconnected" in event_body and "[preauth]" in event_body:
                continue

            try:
                sshd_keyword = self.SSHD_KEYWORD_RE.search(event_body).group(1)
            except AttributeError as exception:
                if str(exception) in self.IGNORE_ATTRIBUTE_ERROR:
                    log.debug("[%s] Ignoring event: %s", self.NAME, event_body)
                    continue

                log.error(
                    "[%s] Error extracting ssh keyword in %s", self.NAME,
                    event_body)
                continue

            message_grammar = self.MESSAGE_GRAMMAR.get(sshd_keyword.lower()) or None
            if not message_grammar:
                log.debug("[%s] No grammar for event: %s", self.NAME, event_body)
                continue

            try:
                parse_result = message_grammar.parseString(event_body)

                if sshd_keyword.lower() == "accepted":
                    event_type = "authentication"
                    auth_result = "success"
                elif sshd_keyword.lower() == "failed":
                    event_type = "authentication"
                    auth_result = "failure"
                elif sshd_keyword.lower() == "disconnected":
                    event_type = "disconnection"
                    auth_result = ""
                else:
                    event_type = "unknown"
                    auth_result = ""

                # extract information from message grammar
                event_dt = datetime.utcfromtimestamp(event_timestamp)
                event_date = event_dt.strftime("%Y-%m-%d")
                event_time = event_dt.strftime("%H:%M:%S")
                auth_method = parse_result.auth_method
                username = parse_result.username
                source_ip = parse_result.source_ip
                source_port = parse_result.source_port
            except pyparsing.ParseException as exception:
                log.error(
                    "[%s] Error encountered while parsing %s as %s: %s",
                    self.NAME,
                    event_body,
                    sshd_keyword,
                    str(exception),
                )
                continue

            ssh_event_data = SSHEventData()
            ssh_event_data.event_id = event.event_id
            ssh_event_data.timestamp = event_timestamp
            ssh_event_data.date = event_date
            ssh_event_data.time = event_time
            ssh_event_data.hostname = event_hostname
            ssh_event_data.pid = event_pid
            ssh_event_data.event_key = event_type
            ssh_event_data.event_type = event_type
            ssh_event_data.auth_method = auth_method
            ssh_event_data.auth_result = auth_result
            ssh_event_data.username = username
            ssh_event_data.source_ip = source_ip
            ssh_event_data.source_port = source_port

            ssh_event_data.calculate_session_id()
            ssh_records.append(ssh_event_data.__dict__)

        log.info(
            "[%s] Total number of SSH authentication events: %d",
            self.NAME,
            len(ssh_records),
        )

        df = pd.DataFrame(ssh_records)
        if df.empty:
            log.info("[%s] No SSH authentication events", self.NAME)
            return "No SSH authentication events"

        try:
            bfa = BruteForceAnalyzer()
            result = bfa.run(df)
            if not result:
                return (f"No verdict. Total number of SSH authentication events"
                        f" {len(ssh_records)}")

            events = self.event_stream(
                query_string=query_string, return_fields=return_fields
            )
            self.annotate_events(events=events, df=df, output=result)
            return str(result)
        except (AuthAnalyzerException, AnalyzerOutputException) as e:
            log.error("[%s] Error analyzing data. %s", self.NAME, str(e))
            return f"No verdict. Error encountered processing data. {str(e)}"


manager.AnalysisManager.register_analyzer(SSHBruteForcePlugin)
