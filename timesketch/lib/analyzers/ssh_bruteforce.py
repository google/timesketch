"""Sketch analyzer plugin for SSH authentication."""
from __future__ import unicode_literals


import hashlib
import logging
from datetime import datetime
import re
import pandas as pd
import pyparsing

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.auth import BruteForceAnalyzer

log = logging.getLogger("timesketch.analyzers.ssh.bruteforce")


class SSHEventData:
    """SSH authentication event."""

    def __init__(self):
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
        """Calculate pseduo session_id for SSH authentication event."""
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
    _SOURCE_IP = pyparsing.Word(pyparsing.printables).setResultsName("source_ip")
    _SOURCE_PORT = pyparsing.Word(pyparsing.nums, max=5).setResultsName("source_port")
    _PROTOCOL = pyparsing.Word(pyparsing.printables).setResultsName("protocol")
    _FINGERPRINT_TYPE = pyparsing.Word(pyparsing.alphanums).setResultsName(
        "fingerprint_type"
    )
    _FINGERPRINT = pyparsing.Word(pyparsing.printables).setResultsName("fingerprint")

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
        + pyparsing.Optional(pyparsing.Literal(":") + _FINGERPRINT_TYPE + _FINGERPRINT)
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
        + pyparsing.Optional(pyparsing.Literal("invalid") + pyparsing.Literal("user"))
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
    # We are only interested in parsing Accepted, Failed, and Disconnected messages
    # as specified in MESSAGE_GRAMMAR
    SSHD_KEYWORD_RE = re.compile(r"\s*([^\s]+)\s+.*")

    # IGNORE_ATTRIBUTE_ERROR holds the error messages that we can ignore
    # while parsing event_body using SSHD_KEYWORD_RE.
    IGNORE_ATTRIBUTE_ERROR = ["'NoneType' object has no attribute 'group'"]

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

            # Wer are not parsing the body if it contains disconnect message for
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
                    "[%s] Error extracting ssh keyword in %s", self.NAME, event_body
                )
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

        bfa = BruteForceAnalyzer()
        result = bfa.run(df)
        if result:
            return str(result["result_markdown"])
        return "No verdict. Total number of SSH authention events {}".format(
            len(ssh_records)
        )


manager.AnalysisManager.register_analyzer(SSHBruteForcePlugin)
