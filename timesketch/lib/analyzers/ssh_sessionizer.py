"""SSH sessionizing sketch analyzer plugin."""

from __future__ import unicode_literals

import re

from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import sessionizer

# Pattern for SSH events message:
# '[sshd] [{process_id}]: {message}'
SSH_PATTERN = re.compile(r"^\[sshd\] \[(?P<process_id>\d+)\]:")

# pylint: disable=line-too-long
# Pattern for message of SSH events for successful connection to port (rdomain is optional):
# '[sshd] [{process_id}]: Connection from {client_ip} port {client_port} on {host_ip} port {host_port} rdomain {rdomain}'
#
# The SSH_CONNECTION_PATTERN is compatible with IPv4
# TODO Change the pattern to be compatible also with IPv6
SSH_CONNECTION_PATTERN = re.compile(
    r"^\[sshd\] \[(?P<process_id>\d+)\]: Connection from "
    + r"(?P<client_ip>(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)) "
    + r"port (?P<client_port>\d+) on "
    + r"(?P<host_ip>(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)) "
    + r"port (?P<host_port>\d+)"
    + r"( rdomain (?P<rdomain>.*))?$"
)


class SSHSessionizerSketchPlugin(sessionizer.SessionizerSketchPlugin):
    """SSH sessionizing sketch analyser.

    The SSH sessionizer is labeling all events from a SSH connection with
    the client's IP address and port.
    Two SSH event are part of the same SSH connection if they have the same
    process ID, which can be find in the message of a SSH event.

    TODO Some SSH events that are a part of a SSH connection are not labelled
    because they have different process ID. This can be fixed by adding the new
    process ID to started_sessions_ids with the value as the session id of the
    process from which the new process was created.
    """

    NAME = "ssh_sessionizer"
    DISPLAY_NAME = "SSH sessions"
    DESCRIPTION = "SSH sessions based on client IP address and port number"

    query = 'reporter:"sshd"'
    session_num = 0
    session_type = "ssh_session"

    def run(self):
        """Entry point for the analyzer.

        Allocates events from a SSH connection with a ssh_session attribute.

        Returns:
            String containing the number of sessions created.
        """
        return_fields = ["message"]

        # event_stream returns an ordered generator of events (by time)
        # therefore no further sorting is needed.
        events = self.event_stream(query_string=self.query, return_fields=return_fields)

        # Dictionary storing the session IDs about the started SSH sessions.
        started_sessions_ids = {}

        for event in events:
            event_message = event.source.get("message")
            connection_match = SSH_CONNECTION_PATTERN.match(event_message)

            if connection_match:
                process_id = connection_match.group("process_id")
                client_ip = connection_match.group("client_ip")
                client_port = connection_match.group("client_port")

                session_id = "{0:s}_{1:s}".format(client_ip, client_port)
                started_sessions_ids[process_id] = session_id
                self.session_num += 1

            ssh_match = SSH_PATTERN.match(event_message)
            if ssh_match:
                process_id = ssh_match.group("process_id")
                if process_id in started_sessions_ids.keys():
                    self.annotateEvent(event, started_sessions_ids[process_id])

        if self.session_num:
            self.sketch.add_view(
                "SSH sessions",
                self.NAME,
                query_string="session_id.{0:s}:*".format(self.session_type),
            )

        return (
            "Sessionizing completed, number of {0:s} sessions created:"
            " {1:d}".format(self.session_type, self.session_num)
        )


manager.AnalysisManager.register_analyzer(SSHSessionizerSketchPlugin)
