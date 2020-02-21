"""Sketch analyzer plugin for crashes."""
from __future__ import unicode_literals

import re

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class CrashesSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for Windows Application Crashes."""

    NAME = 'crashes'

    DEPENDENCIES = frozenset()

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(CrashesSketchPlugin, self).__init__(index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query_elements = {
            'Event - App Error' : (
                'data_type:"windows:evtx:record"',
                'source_name:"Application Error"',
                'event_identifier:"1000"',
                'event_level:"2"', # Level: Error
            ),
            'Event - WER' : (
                'data_type:"windows:evtx:record"',
                'source_name:"Windows Error Reporting"',
                'event_identifier:"1001"',
                'event_level:"4"', # Level: Info
            ),
            'Event - BSOD' : (
                'data_type:"windows:evtx:record"',
                'source_name:"Microsoft-Windows-WER-SystemErrorReporting"',
                'event_identifier:"1001"',
                'event_level:"2"', # Level: Error
            ),
            'Event - App Hang' : (
                'data_type:"windows:evtx:record"',
                'source_name:"Application Error"',
                'event_identifier:"1002"',
                'event_level:"2"', # Level: Error
            ),
            'Event - EMET Warning' : (
                'data_type:"windows:evtx:record"',
                'source_name:"EMET"',
                'event_identifier:"1"',
                'event_level:"3"', # Level: Warning
            ),
            'Event - EMET Error' : (
                'data_type:"windows:evtx:record"',
                'source_name:"EMET"',
                'event_identifier:"1"',
                'event_level:"2"', # Level: Error
            ),
            'Event - .NET App Crash' : (
                'data_type:"windows:evtx:record"',
                'source_name:".NET Runtime"',
                'event_identifier:"1026"',
                'event_level:"2"', # Level: Error
            ),
            'File - WER Report' : (
                'data_type:"fs:stat"',
                'filename:"/Microsoft/Windows/WER/"',
                'filename:/((Non)?Critical|AppCrash)_.*/',
                'file_entry_type:("directory" or "2")',
            ),
            'Registry - Crash Reporting' : (
                'data_type:"windows:registry:key_value"',
                r'key_path:r"\\Control\\CrashControl"',
                'values:("LogEvent: REG_DWORD_LE 0" OR "SendAlert: REG_DWORD_LE 0" OR "CrashDumpEnabled: REG_DWORD_LE 0")',
            ),
            'Registry - Error Reporting' : (
                'data_type:"windows:registry:key_value"',
                r'key_path:"\\Software\\Microsoft\\PCHealth\\ErrorReporting"',
                'values:("DoReport: REG_DWORD_LE 0" OR "ShowUI: REG_DWORD_LE 0")',
            ),
        }

        # Creator of nested Elastic Search queries.
        def formulate_query(elements):
            conditions = []
            for e in elements.values():
                conditions += ['({0})'.format(' AND '.join(e))]
            return ' OR '.join(conditions)

        # Re-usable filename matching function.
        def extract_filename(text, regex):
            if '.exe' in text.lower():
                match = regex.search(message)
                if match:
                    # The regex can match on full file paths and filenames,
                    # so only return the filename.
                    return min([m for m in match.groups() if m])
            return None

        # For adding information to identified entries.
        def mark_as_crash(event, filename):
            event.add_star()
            event.add_attributes({'crash_app': filename})
            event.add_label('crash')

        query = formulate_query(query_elements)

        return_fields = ['data_type', 'message', 'filename']

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        # Get the executable filenames.
        # Examples: 
        #   "[...]\WER\ReportQueue\AppCrash_notepad.exe_8d163e29d3960561ca2e9723640cd8fff5c2ad5_cab_0a5810ac"
        #   "[...]/WER/ReportQueue/NonCritical_x64_d473a376adfb18a7b165c5e3c26de43cd8bccb_cab_07fd2620"
        #   "Strings: ['iexplore.exe', '8.0.7601.17514' [...]"
        re_filename = re.compile(r'(?:\\|\/)(?:AppCrash|Critical|NonCritical)_(.+?\.exe)_[a-f0-9]{16,}|\'([^\']+\.exe)\'', re.I)

        # Container for filenames of crashed applications.
        filenames = dict()

        for event in events:

            data_type = event.source.get('data_type')

            # Search event log entries for filenames of crashed applications.
            if data_type == 'windows:evtx:record':
                message = event.source.get('message')

                fn = extract_filename(message, re_filename)
                if not fn:
                    continue
                filenames[fn] = ''
                mark_as_crash(event, fn)

            # Search file system entries for filenames of crashed applications.
            elif data_type == 'fs:stat':
                filename = event.source.get('filename')

                fn = extract_filename(filename, re_filename)
                if not fn:
                    continue
                filenames[fn] = ''
                mark_as_crash(event, fn)

            # Check if the crash reporting has been disabled in the registry.
            elif data_type == 'windows:registry:key_value':
                event.add_star()
                event.add_comment('WARNING: The crash reporting was disabled. '
                'It could be indicative of attacker activity. '
                'For details refer to page 16 from '
                'https://assets.documentcloud.org/documents/3461560/Google-Aquarium-Clean.pdf.')

            # Commit the event to the datastore.
            event.commit()

        # Create a saved view with our query.
        if filenames:
            self.sketch.add_view('Crash activity', 'app_crashes', query_string=query)

        return 'Crash analyzer completed, {0:d} crashed application{1:s} identified: {2:s}'.format(
            len(filenames), 's' if len(filenames) > 1 else '', ', '.join(filenames.keys()))

manager.AnalysisManager.register_analyzer(CrashesSketchPlugin)
