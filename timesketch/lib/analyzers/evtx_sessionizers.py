"""Sessionizing sketch analyzer plugins for sessions based on the Windows EVTX
log."""

from __future__ import unicode_literals
import re
import opensearchpy.exceptions

from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.sessionizer import SessionizerSketchPlugin

# number of event record ids to keep when checking for duplicates
EVENT_HISTORY_LENGTH = 5
EVENT_DATA_RE = re.compile(r"<EventData>[\s\S]+<\/EventData>")


class WinEVTXSessionizerSketchPlugin(SessionizerSketchPlugin):
    """Base class for sessionizing sketch analyzers for user sessions based on
    Windows EVTX logs, where a session begins with some defined start event and
    ends with some defined end event or a startup event."""

    def run(self):
        """Entry point for the analyzer. Create sessions consisting of a start
        and end event.

        Returns:
            String containing the number of sessions created.
        """
        return_fields = [
            "timestamp",
            "xml_string",
            "event_identifier",
            "record_number",
            "session_id",
        ]
        last_login_time = 0
        session_num = 0
        login_events = dict()
        processed = False

        while not processed:
            query_string = self.query_template.format(last_login_time)
            events = self.event_stream(
                query_string=query_string, return_fields=return_fields
            )
            (
                last_login_time,
                session_num,
                login_events,
                processed,
            ) = self.processSessions(events, session_num, login_events)

        msg = "Sessionizing completed, number of sessions created: {0:d}"
        return msg.format(session_num)

    def processSessions(self, events, session_num, start_events):
        """Iterate over the event stream, checking the event ID to find the
        type of event. Add session ID attribute to the start / end events. Add
        a view for each session.

        Args:
            events: The event stream to process.
            session_num: The number of sessions created so far.
            start_events: A dictionary representing the current start events -
                with the keys as login IDs, and values as the corresponding
                session IDs.

        Returns:
            Tuple containing the timestamp of the last start event, the number
            of sessions created so far, a dictionary representing the current
            start events, and whether all events have been processed.
        """
        try:
            start_time = 0
            prev_record_ids = []

            for event in events:
                curr_record_id = event.source.get("record_number")
                if curr_record_id is not None and curr_record_id in prev_record_ids:
                    # skip if duplicate event
                    continue
                prev_record_ids.append(curr_record_id)
                prev_record_ids = prev_record_ids[(EVENT_HISTORY_LENGTH * -1) :]

                event_id = event.source.get("event_identifier")
                start_time = event.source.get("timestamp")

                if event_id in self.start_events:
                    logon_id = self.getLogonId(event, event_id)
                    session_id = self.getSessionId(event, session_num)
                    self.annotateEvent(event, [session_id])
                    start_events[logon_id] = session_id

                    view_query = 'session_id.{0:s}:"{1:s}"'.format(
                        self.session_type, session_id
                    )
                    self.sketch.add_view(session_id, self.NAME, query_string=view_query)
                    session_num += 1

                elif event_id in self.end_events:
                    logon_id = self.getLogonId(event, event_id)
                    session_id = start_events.get(logon_id)
                    if session_id:
                        self.annotateEvent(event, [session_id])
                        del start_events[logon_id]

                elif start_events:
                    # startup event clears current sessions
                    self.annotateEvent(event, start_events.values())
                    start_events = {}

            return (start_time, session_num, start_events, True)

        except (
            opensearchpy.exceptions.NotFoundError,
            opensearchpy.exceptions.ConnectionTimeout,
        ) as _:
            return (start_time, session_num, start_events, False)

    def getEventData(self, event, name):
        """Retrieves the desired value from the EventData section of a Windows
        EVTX record.

        Args:
            event: The event to retrieve the attribute for.

        Returns:
            The value contained in the attribute.
        """
        event_data = EVENT_DATA_RE.search(event.source.get("xml_string")).group()
        data_name_re = re.compile(r'<Data Name="%s">([^<>]+)<\/Data>' % name)
        text = data_name_re.search(event_data).group(1)
        return text


class LogonSessionizerSketchPlugin(WinEVTXSessionizerSketchPlugin):
    """Sessionizing sketch analyzer for logon sessions, where a session begins
    with a login event and ends with a logout or startup event."""

    NAME = "logon_sessionizer"
    session_type = "logon_session"
    query_template = (
        'data_type:"windows:evtx:record" AND event_identifier:('
        "4624 OR 4778 OR 4634 OR 4647 OR 4779 OR 6005) AND timestamp:[%d TO *]"
    )

    start_events = [4624, 4778]
    end_events = [4634, 4647, 4779]

    def getLogonId(self, event, event_id):
        """Retrieves the logon ID for an event."""
        if event_id in [4624, 4634, 4647]:
            return self.getEventData(event, "TargetLogonId")
        return self.getEventData(event, "LogonID")

    def getSessionId(self, event, session_num):
        """Creates the session ID for an event."""
        event_id = event.source.get("event_identifier")
        if event_id == 4624:
            account_name = self.getEventData(event, "TargetUserName")
        else:
            account_name = self.getEventData(event, "AccountName")
        return "%i (%s)" % (session_num, account_name)


class UnlockSessionizerSketchPlugin(WinEVTXSessionizerSketchPlugin):
    """Sessionizing sketch analyzer for lock / unlock sessions, where a session
    begins with a workstation unlock event and ends with a workstation lock,
    logout or startup event."""

    NAME = "unlock_sessionizer"
    session_type = "unlock_session"
    query_template = (
        'data_type:"windows:evtx:record" AND event_identifier:'
        "(4801 OR 4800 OR 4634 OR 4647 OR 4779 OR 6005) AND timestamp:"
        "[%d TO *]"
    )
    start_events = [4801]
    end_events = [4800, 4802, 4634, 4647, 4779]

    def getLogonId(self, event, event_id):
        """Retrieves the logon ID for an event."""
        if event_id == 4779:
            return self.getEventData(event, "LogonID")
        return self.getEventData(event, "TargetLogonId")

    def getSessionId(self, event, session_num):
        """Creates the session ID for an event."""
        account_name = self.getEventData(event, "TargetUserName")
        return "%i (%s)" % (session_num, account_name)


manager.AnalysisManager.register_analyzer(LogonSessionizerSketchPlugin)
manager.AnalysisManager.register_analyzer(UnlockSessionizerSketchPlugin)
