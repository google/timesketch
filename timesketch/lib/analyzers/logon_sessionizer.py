"""Sessionizing sketch analyzer plugin for logon sessions."""

from __future__ import unicode_literals
import xml.etree.ElementTree as ET
import re
import elasticsearch.exceptions

from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.sessionizer import SessionizerSketchPlugin

class LogonSessionizerSketchPlugin(SessionizerSketchPlugin):
    """Sessionizing sketch analyzer for logon sessions, where a session begins
    with a login event and ends with a logout or startup event."""

    NAME = 'logon_sessionizer'
    session_type = 'logon_session'

    def run(self):
        """Entry point for the analyzer. Create sessions consisting of a login
        and logout event.

        Returns:
            String containing the number of sessions created.
        """
        query = 'data_type:"windows:evtx:record" AND event_identifier:' \
            '(4624 OR 4778 OR 4634 OR 4647 OR 4779 OR 6005)'
        return_fields = ['timestamp', 'xml_string', 'event_identifier',
                         'record_number', 'session_id']
        last_login_time = 0
        session_num = 0
        login_events = dict()
        processed = False

        while not processed:
            events = self.event_stream(query_string=query,
                                       return_fields=return_fields)
            last_login_time, session_num, login_events, processed = \
                self.processSessions(events, session_num, login_events)
            query = 'data_type:"windows:evtx:record" AND ' \
                'event_identifier:(4624 OR 4778 OR 4634 OR 4647 OR 4779 OR ' \
                '6005) AND timestamp:[%d TO *]' % last_login_time

        return 'Sessionizing completed, number of sessions created: %d' \
                % session_num

    def processSessions(self, events, session_num, login_events):
        """Iterate over login events, find the corresponding logoff event for
        each if it exists. Add session ID attribute to the login / logoff
        events. Add a view for each session.

        Args:
            events: The login events to process.
            session_num: The number of sessions created so far.
            login_events: A dictionary representing the current login events -
            with the keys as login IDs, and values as the corresponding session
            IDs.
        Returns:
            Tuple containing the timestamp of the last login event, the number
            of sessions created so far, a dictionary representing the current
            logins, and whether all login events have been processed.
        """
        try:
            login_time = 0
            prev_record_id = ''

            for event in events:
                curr_record_id = event.source.get('record_number')
                if curr_record_id != None and curr_record_id == prev_record_id:
                    #skip if duplicate event
                    continue
                prev_record_id = curr_record_id

                event_id = event.source.get('event_identifier')
                login_time = event.source.get('timestamp')
                if event_id in [4624, 4778]:
                    #login event
                    if event_id == 4624:
                        account_name = self.getXmlEventData(event,
                                                            'TargetUserName')
                        logon_id = self.getXmlEventData(event,
                                                        'TargetLogonId')
                    else:
                        account_name = self.getXmlEventData(event,
                                                            'AccountName')
                        logon_id = self.getXmlEventData(event, 'LogonID')

                    session_id = '%i (%s)' % (session_num, account_name)
                    self.addSessionId(event, [session_id])
                    login_events[logon_id] = session_id

                    view_message = 'Logon session: %s' % (session_id)
                    view_query = 'session_id.logon_session:"%s"' % session_id
                    self.sketch.add_view(view_message, self.NAME,
                                         query_string=view_query)
                    session_num += 1

                elif event_id in [4634, 4647, 4779]:
                    #logout event
                    if event_id == 4779:
                        logon_id = self.getXmlEventData(event, 'LogonID')
                    else:
                        logon_id = self.getXmlEventData(event, 'TargetLogonId')

                    session_id = login_events.get(logon_id)
                    if session_id:
                        self.addSessionId(event, [session_id])
                        del login_events[logon_id]

                else:
                    #startup event
                    if login_events:
                        new_id = []
                        for session_id in login_events.values():
                            new_id.append(session_id)
                        self.addSessionId(event, new_id)
                        login_events = {}

            return (login_time, session_num, login_events, True)

        except (elasticsearch.exceptions.NotFoundError,
                elasticsearch.exceptions.ConnectionTimeout) as _:
            return (login_time, session_num, login_events, False)

    def getXmlEventData(self, event, name):
        """Retrieves the desired value from the EventData section of a Windows
        EVTX record, represented in xml.
        Args:
            event: The event to retrieve the attribute for.
        Returns:
            The value contained in the attribute.
        """
        xml = event.source.get('xml_string')
        xml = re.sub(' xmlns="[^"]+"', '', xml, count=1)  #strip namespace
        root = ET.fromstring(xml)
        node = root.find('./EventData/Data/[@Name=\'%s\']' % name)
        return node.text

manager.AnalysisManager.register_analyzer(LogonSessionizerSketchPlugin)
