"""Sketch analyzer plugin for login and logoff events."""
from __future__ import unicode_literals

import logging

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


LOGON_TYPES = {
    u'0': u'Unknown',
    u'2': u'Interactive',
    u'3': u'Network',
    u'4': u'Batch',
    u'5': u'WindowsService',
    u'7': u'UnlockScreen',
    u'8': u'NetworkCleartext',
    u'9': u'NewCredentials',
    u'10': u'RemoteInteractive',
    u'11': u'CachedInteractive'
}


def parse_evtx_logoff_event(event, string_list, emoji):
    """Parse logoff events and return a count of event processed.

    Args:
        event: an event object (instance of interface.Event).
        string_list: a list of strings extracted from the Event Log.
        emoji: string with the Unicode point for the emoji that will be
            added to the event.

    Returns:
        int: 1 if the event got processed correctly, 0 otherwise.
    """
    if not len(string_list) == 5:
        return 0

    attributes = {}
    attributes['username'] = string_list[1]
    attributes['logon_domain'] = string_list[2]
    attributes['session_id'] = string_list[3]

    logon_type_code = string_list[4]
    attributes['logon_type'] = LOGON_TYPES.get(
        logon_type_code, LOGON_TYPES.get(u'0'))

    event.add_tags(['logoff-event'])
    event.add_attributes(attributes)
    event.add_emojis([emoji])
    return 1


def parse_evtx_logon_event(event, string_list, string_parsed, emoji):
    """Parse logon events and return a count of event processed.

    Args:
        event: an event object (instance of interface.Event).
        string_list: a list of strings extracted from the Event Log.
        emoji: string with the Unicode point for the emoji that will be
            added to the event.

    Returns:
        int: 1 if the event got processed correctly, 0 otherwise.
    """
    attributes = {}

    if not string_parsed:
        string_parsed = {}
        if not len(string_list) == 23:
            return 0
        string_parsed['target_user_id'] = string_list[4]
        string_parsed['target_user_name'] = string_list[5]
        string_parsed['hostname'] = string_list[11]

    logon_type_code = string_list[8]
    attributes['logon_type'] = LOGON_TYPES.get(
        logon_type_code, LOGON_TYPES.get(u'0'))

    attributes['username'] = '{0:s}/{1:s}'.format(
        string_parsed.get('target_user_id', 'N/A'),
        string_parsed.get('target_user_name', 'Unknown'))
    attributes['hostname'] = string_parsed.get('target_machine_name', 'N/A')
    attributes['session_id'] = string_list[3]

    event.add_tags(['logon-event'])
    event.add_attributes(attributes)
    event.add_emojis([emoji])
    return 1


class LoginSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for Login and Logoff related activity."""

    NAME = 'login'
    DEPENDENCIES = frozenset()

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(LoginSketchPlugin, self).__init__(index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        login_emoji = emojis.get_emoji('lock')
        logoff_emoji = emojis.get_emoji('unlock')
        login_counter = 0
        logoff_counter = 0

        # TODO: Add EVT lookups, ID 528 for logon and 538, 540 for logoff.
        # TODO: Add RDP EVT lookups, ID 682 for logon and 683 for logoff.
        query = (
            'data_type:"windows:evtx:record" AND (event_identifier:4624 OR '
            'event_identifier:4778 OR event_identifier:4779 OR '
            'event_identifier:4634)')

        return_fields = [
            'message', 'data_type', 'strings', 'strings_parsed',
            'event_identifier']

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        for event in events:
            strings = event.source.get('strings')
            strings_parsed = event.source.get('strings_parsed')
            identifier = event.source.get('event_identifier')
            if isinstance(identifier, (str, unicode)):
                try:
                    identifier = int(identifier, 10)
                except ValueError:
                    logging.warning((
                        'Unable to convert EVTX identifier to an integer, '
                        'value is {0:s}').format(identifier))
                    continue

            if identifier == 4624:
                login_counter += parse_evtx_logon_event(
                    event, strings, strings_parsed, login_emoji)
            elif identifier == 4634:
                logoff_counter += parse_evtx_logoff_event(
                    event, strings, logoff_emoji)
            # TODO: Add support for RDP events, ID 4778 (logon) and 4779
            # (logoff).

        # TODO: Add support for Linux syslog logon/logoff events.
        # TODO: Add support for Mac OS X logon/logoff events.

        return (
            'Total number of login events processed: {0:d} and '
            'logoff events: {1:d}').format(login_counter, logoff_counter)


manager.AnalysisManager.register_analyzer(LoginSketchPlugin)
