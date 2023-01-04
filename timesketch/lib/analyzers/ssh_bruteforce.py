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

log = logging.getLogger('ssh_bruteforce')


class SSHEventData:
    """SSH authentication event."""

    def __init__(self):
        self.timestamp = 0
        self.date = '1970-01-01'
        self.time = '00:00:00'
        self.hostname = ''
        self.pid = 0
        self.event_key = ''
        self.event_type = ''
        self.auth_method = ''
        self.auth_result = ''
        self.domain = ''  # Required for consistency with Windows
        self.username = ''
        self.source_ip = ''
        self.source_port = ''
        self.source_hostname = ''
        self.session_id = ''

    def calculate_session_id(self) -> None:
        hash_data = (
            f'{self.date}|{self.hostname}|{self.username}|{self.source_ip}|'
            f'{self.source_port}')

        h = hashlib.new('sha256')
        h.update(str.encode(hash_data))
        self.session_id = h.hexdigest()


class SSHBruteForcePlugin(interface.BaseAnalyzer):
    """Analyzer for SSH authentication"""

    NAME = 'ssh_brute_force'
    DISPLAY_NAME = 'SSH Brute Force Analyzer'
    DESCRIPTION = 'Analyzer for successful SSH brute force login'

    _PID = pyparsing.Word(pyparsing.nums).setResultsName('pid')
    _AUTHENTICATION_METHOD = (
        pyparsing.Keyword('password')
        | pyparsing.Keyword('publickey')).setResultsName('auth_method')
    _USERNAME = pyparsing.Word(pyparsing.alphanums).setResultsName('username')
    _SOURCE_IP = pyparsing.Word(pyparsing.printables).setResultsName('source_ip')
    _SOURCE_PORT = pyparsing.Word(pyparsing.nums,
                                    max=5).setResultsName('source_port')
    _PROTOCOL = pyparsing.Word(pyparsing.printables,
                                max=4).setResultsName('protocol')
    _FINGERPRINT_TYPE = pyparsing.Word(
        pyparsing.alphanums).setResultsName('fingerprint_type')
    _FINGERPRINT = pyparsing.Word(
        pyparsing.printables).setResultsName('fingerprint')

    # Timesketch message field grammar
    _LOGIN_GRAMMAR = (
        pyparsing.Literal('[sshd, pid:') + _PID +
        pyparsing.Literal(']') + pyparsing.Literal('Accepted') +
        _AUTHENTICATION_METHOD + pyparsing.Literal('for') + _USERNAME +
        pyparsing.Literal('from') + _SOURCE_IP + pyparsing.Literal('port') +
        _SOURCE_PORT + _PROTOCOL + pyparsing.Optional(
            pyparsing.Literal(':') + _FINGERPRINT_TYPE + _FINGERPRINT) +
        pyparsing.StringEnd())

    # Timesketch message field grammar
    _FAILED_GRAMMER = (
        pyparsing.Literal('[sshd, pid:') + _PID +
        pyparsing.Literal(']') + pyparsing.Literal('Failed') +
        _AUTHENTICATION_METHOD + pyparsing.Literal('for') + pyparsing.Optional(
            pyparsing.Literal('invalid') + pyparsing.Literal('user')) +
        _USERNAME + pyparsing.Literal('from') + _SOURCE_IP +
        pyparsing.Literal('port') + _SOURCE_PORT + _PROTOCOL)

    # Timesketch message field grammar
    _DISCONNECT_GRAMMAR = (
        pyparsing.Literal('[sshd, pid:') + _PID +
        pyparsing.Literal(']') + pyparsing.Literal('Disconnected') +
        pyparsing.Literal('from') + pyparsing.Literal('user') + _USERNAME +
        _SOURCE_IP + pyparsing.Literal('port') + _SOURCE_PORT)

    MESSAGE_GRAMMAR = {
        'accepted': _LOGIN_GRAMMAR,
        'failed': _FAILED_GRAMMER,
        'disconnected': _DISCONNECT_GRAMMAR
    }

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """
        query = (
            'data_type:"syslog:line" AND reporter:sshd AND'
            ' (body:Accepted* OR body:Failed* OR body:Disconnected*)'
        )
        return_fields = [
            'timestamp',
            'hostname',
            'pid',
            'message'
        ]

        events = self.event_stream(query_string=query, return_fields=return_fields)

        sshd_message_type_re = re.compile(
            r'.*sshd\[\d+\]:\s+([^\s]+)\s+([^\s]+)\s.*')

        ssh_records = []

        for event in events:
            event_timestamp = float(event.source.get('timestamp'))
            event_hostname = event.source.get('hostname')
            event_pid = event.source.get('pid')
            event_message = event.source.get('message')

            try:
                sshd_message_type = sshd_message_type_re.search(event_message).group(1)
            except AttributeError:
                log.info('Unable to get SSH message type {}'.format(event_message))
                continue
            for message_type, message_grammar in self.MESSAGE_GRAMMAR.items():
                if message_type.lower() != sshd_message_type.lower():
                    continue
                try:
                    m = message_grammar.parse_string(event_message)

                    if message_type.lower() == 'accepted':
                        event_type = 'authentication'
                        auth_result = 'success'
                    elif message_type.lower() == 'failed':
                        event_type = 'authentication'
                        auth_result = 'failure'
                    elif message_type.lower() == 'disconnected':
                        event_type = 'disconnection'
                        auth_result = ''
                    else:
                        event_type = 'unknown'
                        auth_result = ''

                    # extract information from message grammar
                    dt = datetime.utcfromtimestamp(event_timestamp)
                    event_date = dt.strftime('%Y-%m-%d')
                    event_time = dt.strftime('%H:%M:%S')
                    auth_method = m.auth_method
                    username = m.username
                    source_ip = m.source_ip
                    source_port = m.source_port
                except pyparsing.ParseException as e:
                    if not str(e).startswith('Expected'):
                        log.info('Error encountered parsing {}: {}'.format(
                                event_message, e))
                        continue

            ssh_event_data = SSHEventData()
            ssh_event_data.timestamp=event_timestamp
            ssh_event_data.date=event_date
            ssh_event_data.time=event_time
            ssh_event_data.hostname=event_hostname
            ssh_event_data.pid=event_pid
            ssh_event_data.event_key=event_type
            ssh_event_data.event_type=event_type
            ssh_event_data.auth_method=auth_method
            ssh_event_data.auth_result=auth_result
            ssh_event_data.username=username
            ssh_event_data.source_ip=source_ip
            ssh_event_data.source_port=source_port

            ssh_event_data.calculate_session_id()
            ssh_records.append(ssh_event_data)

        df = pd.DataFrame(ssh_records)
        if df.empty:
            log.info('No SSH authentication events')
            return('No SSH authentication events')

        return('No finding')


manager.AnalysisManager.register_analyzer(SSHBruteForcePlugin)
