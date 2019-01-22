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
    u'5': u'Service',
    u'7': u'Unlock',
    u'8': u'NetworkCleartext',
    u'9': u'NewCredentials',
    u'10': u'RemoteInteractive',
    u'11': u'CachedInteractive'
}


def parse_evtx_logoff_event(string_list):
    """Parse logoff events and return a dict with attributes.

    Args:
        string_list: a list of strings extracted from the Event Log.

    Returns:
        Dict with attributes parsed out of the logoff events.
    """
    if not len(string_list) == 5:
        return {}

    attributes = {}
    attributes['username'] = string_list[1]
    attributes['logon_domain'] = string_list[2]
    attributes['session_id'] = string_list[3]

    logon_type_code = string_list[4]
    attributes['logon_type'] = LOGON_TYPES.get(
        logon_type_code, LOGON_TYPES.get(u'0'))

    return attributes


def parse_evtx_logon_event(string_list, string_parsed):
    """Parse logon events and return a count of event processed.

    Args:
        string_list: a list of strings extracted from the Event Log.
        string_parsed: a dict with strings extracted from the Event log.

    Returns:
        Dict with attributes parsed out of the logon events.
    """
    if len(string_list) < 20:
        return {}

    if not string_parsed:
        string_parsed = {}
        string_parsed['target_user_id'] = string_list[4]
        string_parsed['target_user_name'] = string_list[5]
        string_parsed['hostname'] = string_list[11]
        string_parsed['source_user_name'] = string_list[1]

    attributes = {}
    logon_type_code = string_list[8]
    attributes['logon_type'] = LOGON_TYPES.get(
        logon_type_code, LOGON_TYPES.get(u'0'))

    win_domain = string_list[2]
    if win_domain:
        attributes['windows_domain'] = win_domain

    username = string_parsed.get('target_user_name')
    if username:
        attributes['username'] = username

    user_id = string_parsed.get('target_user_id')
    if user_id:
        attributes['user_id'] = user_id

    logon_process_name = string_list[9]
    if logon_process_name:
        attributes['logon_process'] = logon_process_name

    workstation_name = string_list[11]
    if workstation_name == '-':
        attributes['workstation'] = 'localhost'
    elif workstation_name:
        attributes['workstation'] = workstation_name

    ip_address = string_list[18]
    if ip_address and ip_address != '-':
        attributes['source_address'] = ip_address

    hostname = string_parsed.get('target_machine_name', 'N/A')
    if hostname:
        attributes['hostname'] = hostname

    session_id = string_list[3]
    if session_id:
        attributes['session_id'] = session_id

    source_username = string_parsed.get('source_user_name')
    if source_username:
        attributes['source_username'] = source_username

    return attributes


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
        login_emoji = emojis.get_emoji('unlock')
        logoff_emoji = emojis.get_emoji('lock')
        screen_emoji = emojis.get_emoji('screen')
        screensaver_logon = LOGON_TYPES.get('7')
        login_counter = 0
        logoff_counter = 0

        # TODO: Add EVT lookups, ID 528 for logon and 538, 540 for logoff.
        # TODO: Add RDP EVT lookups, ID 682 for logon and 683 for logoff.
        query = (
            'data_type:"windows:evtx:record" AND (event_identifier:4624 OR '
            'event_identifier:4778 OR event_identifier:4779 OR '
            'event_identifier:4634 OR event_identifier:4647)')

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
            emojis_to_add = []
            tags_to_add = []
            attribute_dict = {}

            if isinstance(identifier, (str, unicode)):
                try:
                    identifier = int(identifier, 10)
                except ValueError:
                    logging.warning((
                        'Unable to convert EVTX identifier to an integer, '
                        'value is {0:s}').format(identifier))
                    continue

            if identifier == 4624:
                attribute_dict = parse_evtx_logon_event(
                    strings, strings_parsed)
                if not attribute_dict:
                    continue
                emojis_to_add.append(login_emoji)
                tags_to_add.append('logon-event')
                login_counter += 1

            elif identifier == 4634 or identifier == 4647:
                attribute_dict = parse_evtx_logoff_event(strings)
                if not attribute_dict:
                    continue
                emojis_to_add.append(logoff_emoji)
                tags_to_add.append('logoff-event')
                logoff_counter += 1

            # TODO: Add support for RDP events, ID 4778 (logon) and 4779
            # (logoff).
            if not attribute_dict:
                continue
            event.add_attributes(attribute_dict)

            # Want to add an emoji in case this is a screensaver unlock.
            if attribute_dict.get('logon_type', '') == screensaver_logon:
                emojis_to_add.append(screen_emoji)

            if emojis_to_add:
                event.add_emojis(emojis_to_add)

            if tags_to_add:
                event.add_tags(tags_to_add)

        # TODO: Add support for Linux syslog logon/logoff events.
        # TODO: Add support for Mac OS X logon/logoff events.

        return (
            'Total number of login events processed: {0:d} and '
            'logoff events: {1:d}').format(login_counter, logoff_counter)


manager.AnalysisManager.register_analyzer(LoginSketchPlugin)
