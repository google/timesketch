"""Sketch analyzer plugin for Windows crash artefacts."""

from __future__ import unicode_literals

import re

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class WinCrashSketchPlugin(interface.BaseAnalyzer):
    """Analyzer for Windows application crashes."""

    NAME = "win_crash"
    DISPLAY_NAME = "Windows application crashes"
    DESCRIPTION = "Detect Windows application crashes"

    DEPENDENCIES = frozenset()

    FILENAME_REGEX = re.compile(
        r"(?:\\|\/)(?:AppCrash|Critical|NonCritical)_(.+?\.exe)_[a-f0-9]{16,}"
        r"|\'([^\']+\.exe)\'",
        re.IGNORECASE,
    )

    QUERY_ELEMENTS = {
        "Event - App Error": (
            'data_type:"windows:evtx:record"',
            'source_name:"Application Error"',
            'event_identifier:"1000"',
            'event_level:"2"',  # Level: Error
        ),
        "Event - WER": (
            'data_type:"windows:evtx:record"',
            'source_name:"Windows Error Reporting"',
            'event_identifier:"1001"',
            'event_level:"4"',  # Level: Info
        ),
        "Event - BSOD": (
            'data_type:"windows:evtx:record"',
            'source_name:"Microsoft-Windows-WER-SystemErrorReporting"',
            'event_identifier:"1001"',
            'event_level:"2"',  # Level: Error
        ),
        "Event - App Hang": (
            'data_type:"windows:evtx:record"',
            'source_name:"Application Error"',
            'event_identifier:"1002"',
            'event_level:"2"',  # Level: Error
        ),
        "Event - EMET Warning": (
            'data_type:"windows:evtx:record"',
            'source_name:"EMET"',
            'event_identifier:"1"',
            'event_level:"3"',  # Level: Warning
        ),
        "Event - EMET Error": (
            'data_type:"windows:evtx:record"',
            'source_name:"EMET"',
            'event_identifier:"1"',
            'event_level:"2"',  # Level: Error
        ),
        "Event - .NET App Crash": (
            'data_type:"windows:evtx:record"',
            'source_name:".NET Runtime"',
            'event_identifier:"1026"',
            'event_level:"2"',  # Level: Error
        ),
        "File - WER Report": (
            'data_type:"fs:stat"',
            'filename:"/Microsoft/Windows/WER/"',
            "filename:/((Non)?Critical|AppCrash)_.*/",
            'file_entry_type:("directory" or "2")',
        ),
        "Registry - Crash Reporting": (
            'data_type:"windows:registry:key_value"',
            r'key_path:"\\Control\\CrashControl"',
            'values:("LogEvent: REG_DWORD_LE 0"'
            + ' OR "SendAlert: REG_DWORD_LE 0"'
            + ' OR "CrashDumpEnabled: REG_DWORD_LE 0")',
        ),
        "Registry - Error Reporting": (
            'data_type:"windows:registry:key_value"',
            r'key_path:"\\Software\\Microsoft\\PCHealth\\ErrorReporting"',
            'values:("DoReport: REG_DWORD_LE 0" OR "ShowUI: REG_DWORD_LE 0")',
        ),
    }

    def formulate_query(self, elements):
        """Generates the OpenSearch query.

        Args:
            elements: Dictionary with a list of conditions

        Returns:
            The OpenSearch query
        """
        conditions = list()
        for element_list in elements.values():
            conditions += ["({0})".format(" AND ".join(element_list))]
        return " OR ".join(conditions)

    def extract_filename(self, text):
        """Finds filenames of crashed applications using a regular expression.

        Args:
            text: String that might contain the filename

        Returns:
            The string with filename if found
        """
        if ".exe" in str(text or "").lower():
            match = self.FILENAME_REGEX.search(text)
            if match:
                # The regex can match on full file paths and filenames,
                # so only return the filename.
                return min([m for m in match.groups() if m])
        return ""

    def mark_as_crash(self, event, filename):
        """Mark entries with crash artefacts.

        Args:
            event: OpenSearch event
            filename: Application that crashed
        """
        if filename:
            event.add_attributes({"crash_app": filename})
        event.add_tags(["win_crash"])

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = self.formulate_query(self.QUERY_ELEMENTS)

        return_fields = ["data_type", "message", "filename"]

        # Generator of events based on your query.
        events = self.event_stream(query_string=query, return_fields=return_fields)

        # Container for filenames of crashed applications.
        filenames = set()

        for event in events:
            data_type = event.source.get("data_type")
            event_text = None

            # Tag entries that show the crash reporting has been disabled.
            if data_type == "windows:registry:key_value":
                event.add_comment(
                    "WARNING: The crash reporting was disabled. "
                    "It could be indicative of attacker activity. "
                    "For details refer to page 16 from "
                    "https://assets.documentcloud.org/documents/3461560/"
                    "Google-Aquarium-Clean.pdf."
                )
                event.commit()
                continue

            # Search event log entries for filenames of crashed applications.
            if data_type == "windows:evtx:record":
                event_text = event.source.get("message")

            # Search file system entries for filenames of crashed applications.
            elif data_type == "fs:stat":
                event_text = event.source.get("filename")

            # If found the filename, tag the entry as crash-related
            filename = self.extract_filename(event_text)
            if filename:
                self.mark_as_crash(event, filename)
                filenames.add(filename)
                event.commit()

        # Create a saved view with our query.
        if filenames:
            self.sketch.add_view(
                "Windows Crash activity", "win_crash", query_string='tag:"win_crash"'
            )

        return (
            "Windows Crash analyzer completed, "
            + "{0:d} crashed application{1:s} identified: {2:s}".format(
                len(filenames), "s" if len(filenames) > 1 else "", ", ".join(filenames)
            )
        )


manager.AnalysisManager.register_analyzer(WinCrashSketchPlugin)
