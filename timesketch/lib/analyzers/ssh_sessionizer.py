"""SSH sessionizing sketch analyzer plugin."""

from __future__ import unicode_literals

import re

from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import sessionizer


class SSHSessionizerSketchPlugin(sessionizer.SessionizerSketchPlugin):
    """SSH sessionizing sketch analyser.

    The SSH sessionizer is labeling all events from a SSH connection with
    the client's IP address and port.
    Two SSH event are part of the same SSH connection if they have the same
    connection id, which can be find in the message of a SSH event.
    """

    NAME = 'ssh_sessionizer'
    query = 'reporter:"sshd"'
    session_type = 'ssh_session'

    def run(self):
        """Entry point for the analyzer.

        Allocates events from a SSH connection with a ssh_session attribute.

        Returns:
            String containing the number of sessions created.
        """
        return_fields = ['message']

        # event_stream returns an ordered generator of events (by time)
        # therefore no further sorting is needed.
        events = self.event_stream(query_string=self.query,
                                   return_fields=return_fields)

        # Dictionary storing the session IDs about the started SSH sessions.
        started_sessions_ids = {}

        sessions_created = 0

        for event in events:
            event_message = event.source.get('message')
            connection_match = is_connection_event(event_message)

            if connection_match:
                connection_id = connection_match.group('connection_id')
                client_ip = connection_match.group('client_ip')
                client_port = connection_match.group('client_port')

                started_sessions_ids[
                    connection_id] = client_ip + '_' + client_port
                sessions_created += 1

            connection_id = get_connection_id(event_message)
            if connection_id and connection_id in started_sessions_ids.keys():
                self.annotateEvent(event, started_sessions_ids[connection_id])

        self.sketch.add_view('SSH session view',
                             self.NAME,
                             query_string=self.get_query_string())
        return ('Sessionizing completed, number of session created:'
                ' {0:d}'.format(sessions_created))

    def get_query_string(self):
        """Generate query string for all events allocated with session_type
        attribute.

        Returns:
            Query string for Elasticsearch.
        """

        query_string = 'session_id' + '.' + self.session_type + ':*'
        return query_string


def is_connection_event(event_message):
    """Checks if event is a SSH connection event depending on if the message of
    the event matches the pattern for SSH connection events.

    Pattern for the massage of SSH connection events:
    '[sshd] [{connection_id}]: Connection from {source_ip} port {source_port} on
    {dest_ip} port {dest_ip}'

    Named groups for the corresponging regex are: <connection_id>, <client_ip>,
    <client_port>, <host_ip>, <host_port>.

    Args:
        event_message: String representing the value of the message attribute of
        an event.

    Returns:
        Match object, presenting the result of re.match() for the SSH connection
        message pattern and the given message.
    """

    pattern = r'^\[sshd\] \[(?P<connection_id>[0-9]+)\]: Connection from ' + \
    r'(?P<client_ip>([0-9]{0,3}\.*){4,6}) port (?P<client_port>[0-9]+) on ' + \
    r'(?P<host_ip>([0-9]{0,3}\.*){4,6}) port (?P<host_port>[0-9]+)$'

    return re.match(pattern, event_message)


def get_connection_id(event_message):
    """Extracts the connection_id from the message of a SSH event.

    Pattern for the massage of SSH events:
    '[sshd] [{connection_id}]: {message}'

    Named groups for the corresponging regex are: <connection_id>.

    Args:
        event_message: String representing the value of the message attribute of
            an event.

    Returns:
        connection_id number if the event_message matched the SSH event message
            pattern and None otherwise.
    """

    pattern = r'^\[sshd\] \[(?P<connection_id>[0-9]+)\]: .*'

    match = re.match(pattern, event_message)

    if match:
        return match.group('connection_id')

    return None


manager.AnalysisManager.register_analyzer(SSHSessionizerSketchPlugin)
