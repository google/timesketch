"""TODO"""

from __future__ import unicode_literals
import xml.etree.ElementTree as ET
import re

from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.sessionizer import SessionizerSketchPlugin


# class LogonSessionizerSketchPlugin(SessionizerSketchPlugin):
#     """TODO"""
#     NAME = 'logon_sessionizer'
#     session_type = 'logon_session'
#     #Query string identifying the events a session should start with
#     startswith = 'data_type:"windows:evtx:record" AND (event_identifier:4624'\
#         ' OR event_identifier:4778)'

#     def run(self):
#         """TODO"""
#         return_fields = ['timestamp', 'xml_string']
#         start_events = self.event_stream(query_string=self.startswith,
#                                          return_fields=return_fields)

#         session_num = 0
#         return_fields.extend(['data_type', 'event_identifier'])

#         for start_event in start_events:
#             print("STARTING")
#             start_time = start_event.source.get('timestamp')
#             logon_id = self.getXmlEventData(start_event, 'TargetLogonId')
#             account_name = self.getXmlEventData(start_event, 'TargetUserName')
#             print(account_name)

#             query_dict = dict()
#             query_dict = ('{"query": {"range": {"timestamp": {"gte":%d}}}}'
#                           % start_time)

#             events = self.event_stream(query_dsl=query_dict,
#                                        return_fields=return_fields)

#             for event in events:
#                 session_str = '%i (%s)' % (session_num, account_name)
#                 self.annotateEvent(event, session_str)
#                 if self.isEnd(event, logon_id):
#                     view_query = '{"query": {"range": {"timestamp": {"gte":'\
#                         '%d, "lte":%d}}}}' % (start_time,
#                                               event.source.get('timestamp'))
#                     self.sketch.add_view(('Logon session: %i (%s)' %
#                                           (session_num, account_name)),
#                                          self.NAME, query_dsl=view_query)
#                     print("Logon session processed")
#                     break
#             session_num += 1

#         return ('Sessionizing completed, number of session created:'
#                 ' {0:d}'.format(session_num))

#     def getXmlEventData(self, event, name):
#         xml = event.source.get('xml_string')
#         xml = re.sub(' xmlns="[^"]+"', '', xml, count=1)  #strip namespace
#         root = ET.fromstring(xml)
#         node = root.find('./EventData/Data/[@Name=\'%s\']' % name)
#         return node.text

#     def isEnd(self, event, logon_id):
#         if event.source.get('data_type') == 'windows:evtx:record':
#             if event.source.get('event_identifier') in [4634, 4647, 4779]:
#                 print(self.getXmlEventData(event, 'TargetLogonId'))
#                 print(logon_id)
#                 if self.getXmlEventData(event, 'TargetLogonId') == logon_id:
#                     return True
#         return False

class LogonSessionizerSketchPlugin(SessionizerSketchPlugin):
    """TODO"""
    NAME = 'logon_sessionizer'
    session_type = 'logon_session'
    #Query string identifying the events a session should start with
    startswith = 'data_type:"windows:evtx:record" AND (event_identifier:4624'\
        ' OR event_identifier:4778)'

    def run(self):
        """TODO"""
        return_fields = ['timestamp', 'xml_string']
        start_events = self.event_stream(query_string=self.startswith,
                                         return_fields=return_fields)

        session_num = 0

        for start_event in start_events:
            print("STARTING")
            start_time = start_event.source.get('timestamp')
            logon_id = self.getXmlEventData(start_event, 'TargetLogonId')
            account_name = self.getXmlEventData(start_event, 'TargetUserName')
            print(account_name)

            end_query = 'data_type:"windows:evtx:record" AND ' \
                '(event_identifier:4634 OR event_identifier:4647 OR ' \
                'event_identifier:4779) AND xml_string:%s' % logon_id

            end_event_stream = self.event_stream(query_string=end_query,
                                       return_fields=return_fields)
            try:
                end_event = next(end_event_stream)
                end_time = end_event.source.get('timestamp')

                query_dict = dict()
                query_dict = '{"query": {"range": {"timestamp": {"gte":%d,' \
                    '"lte":%d}}}}' % (start_time, end_time)

                session_events = self.event_stream(query_dsl=query_dict,
                                        return_fields=return_fields)
                for session_event in session_events:
                    session_str = '%i (%s)' % (session_num, account_name)
                    self.annotateEvent(session_event, session_str)
                
                message = 'Logon session: %i (%s)' % (session_num, account_name)
                self.sketch.add_view(message, self.NAME, query_dsl=query_dict)
                print("Logon session processed")
                session_num += 1

            except StopIteration:
                print("No logout for logon id %s!" % logon_id)

        return ('Sessionizing completed, number of session created:'
                ' {0:d}'.format(session_num))

    def getXmlEventData(self, event, name):
        xml = event.source.get('xml_string')
        xml = re.sub(' xmlns="[^"]+"', '', xml, count=1)  #strip namespace
        root = ET.fromstring(xml)
        node = root.find('./EventData/Data/[@Name=\'%s\']' % name)
        return node.text

    # def isEnd(self, event, logon_id):
    #     if event.source.get('data_type') == 'windows:evtx:record':
    #         if event.source.get('event_identifier') in [4634, 4647, 4779]:
    #             print(self.getXmlEventData(event, 'TargetLogonId'))
    #             print(logon_id)
    #             if self.getXmlEventData(event, 'TargetLogonId') == logon_id:
    #                 return True
    #     return False

manager.AnalysisManager.register_analyzer(LogonSessionizerSketchPlugin)
