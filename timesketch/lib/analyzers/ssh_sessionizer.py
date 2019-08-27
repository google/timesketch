"""SSH sessionizing sketch analyzer plugin."""

from __future__ import unicode_literals

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class SSHSessionizerSketchPlugin(interface.BaseSketchAnalyzer):
    """Sessionizing sketch analyser. All events in sketch with id sketch_id
    are grouped in sessions based on the time difference between them. Two
    consecutive events are in the same session if the time difference between
    them is less or equal then max_time_diff_micros
    TODO"""

    NAME = 'ssh_sessionizer'
    #TODO
    query = '(data_type:"syslog:line") AND ' +\
            '("connection from" OR "disconnected from user")'

    def run(self):
        """Entry point for the analyzer. Allocates each event a session_id
        attribute.

        Returns:
            String containing the number of sessions created.
        """
        return_fields = ['message']

        # event_stream returns an ordered generator of events (by time)
        # therefore no further sorting is needed.
        events = self.event_stream(query_string=self.query,
                                   return_fields=return_fields)
        # (key:value) = ((IP, port):(Event,number))
        connection_events = {}
        # (key:value) = (IP:session_number)
        ip_session_numbers = {}

        sessions_created = 0

        for event in events:
            message = event.source.get('message')
            if 'connection' in message.lower():
                ip_port_pair = parse_connection_message(message)
                ip = ip_port_pair[0]
                if not ip in ip_session_numbers:
                    ip_session_numbers[ip] = 0
                connection_events[ip_port_pair] = event
            else:
                ip_port_pair = parse_disconnection_message(message)
                ip = ip_port_pair[0]
                if ip_port_pair in connection_events:
                    connect_event = connection_events[ip_port_pair]
                    session_num = ip_session_numbers[ip]
                    self.annotateEvent(connect_event, ip, session_num)
                    self.annotateEvent(event, ip, session_num)
                    ip_session_numbers[ip] = session_num + 1

        self.sketch.add_view('Session view',
                             self.NAME,
                             query_string=self.query)
        return ('Sessionizing completed, number of session created:'
                ' {0:d}'.format(sessions_created))

    def annotateEvent(self, event, ip, session_num):
        event.add_attributes({'ssh_session': ip + ':' + str(session_num)})
        event.commit()


def parse_connection_message(event_message):
    """Parse event_message of a connection event and extracts the IP and the
    port of the connection end of the ssh session.

    Args:
        event_message: String representing the value of the message attribute of
            an event.

    Returns:
        Pair like (IP, port).
    """
    t = valid_connection_pattern(event_message)
    if t[0] != t[1]:
        raise RuntimeError(t[0] + '|' + t[1])

    message = event_message.split()
    return (message[4], message[6])


def valid_connection_pattern(event_message):
    """Check if the pattern is update with event_message.

    Pattern: '[sshd] {number}: Connection from {source_ip} port {source_port} on
    {dest_ip} port {dest_ip}'

    Args:
        event_message: String representing the value of the attribute
            message of event.
    Returns:
        If the message pattern is valid.
    """
    message_list = event_message.split()

    pattern = ('[sshd] {0:s} Connection from {1:s} port {2:s} on {3:s} port ' +\
              '{4:s}').format(message_list[1], message_list[4], message_list[6],
                              message_list[8], message_list[10])
    return (pattern, event_message)


def parse_disconnection_message(event_message):
    """Parse event_message and extracts the IP and the port of the
    connection end of the ssh session.

    Args:
        event_message: String representing the value of the message attribute of
            an event.

    Returns:
        Pair like (IP, port).
    """
    if not valid_disconnection_pattern(event_message):
        raise RuntimeError(event_message)

    message = event_message.split()
    return (message[6], message[8])


def valid_disconnection_pattern(event_message):
    """Check if the pattern is update with event_message.

    Pattern: '[sshd] {number}: Disconnected from user auskova {source_ip} port
    {source_port}'

    Args:
        event_message: String representing the value of the attribute
            message of event.
    Returns:
        If the message pattern is valid.
    """
    message_list = event_message.split()

    pattern = '[sshd] {0:s} Disconnected from user {1:s} {2:s} port {3:s}'.\
        format(message_list[1], message_list[5], message_list[6], \
        message_list[8])
    return pattern == event_message


manager.AnalysisManager.register_analyzer(SSHSessionizerSketchPlugin)
