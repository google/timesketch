# Copyright 2017 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# pylint: skip-file
import argparse
import csv
import uuid
import json
import sys

from timesketch.lib.experimental.utils import event_stream
from timesketch.lib.experimental.utils import parse_xml_event


class KnowledgeBase(object):

    def __init__(self):
        self.ip2host = {}

    def add(self, ip, hostname):
        self.ip2host[ip] = hostname

    def get(self, ip):
        try:
            hostname = self.ip2host[ip]
        except KeyError:
            hostname = ip
        return hostname


class ParseEvents(object):

    LOCALHOST = [u'::1', u'127.0.0.1']

    def __init__(self):
        super(ParseEvents, self).__init__()
        self.events = set()
        self.ip2host = dict()
        self.kb = KnowledgeBase()

    def parse_xml(self, xml):
        event_container = dict()

        logon_types = {
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

        event = parse_xml_event(xml)

        src_ip = event[u'EventData'].get(u'IpAddress')
        event_container[u'src_ip'] = src_ip

        src_hostname = event[u'EventData'].get(u'WorkstationName')
        if src_hostname:
            src_hostname = src_hostname.split(u'.')[0].upper()
        event_container[u'src_hostname'] = src_hostname

        dst_hostname = event[u'System'][u'Computer'].get(u'value')
        if dst_hostname:
            dst_hostname = dst_hostname.split(u'.')[0].upper()
        event_container[u'dst_hostname'] = dst_hostname

        username = event[u'EventData'].get(u'TargetUserName')
        event_container[u'username'] = username

        logon_type = event[u'EventData'].get(u'LogonType')
        event_container[u'logon_type'] = logon_types[logon_type]

        if src_ip and src_hostname:
            self.kb.add(src_ip, src_hostname)

        event_list = [
            event_container[u'src_ip'],
            event_container[u'src_hostname'],
            event_container[u'dst_hostname'],
            event_container[u'username'],
            event_container[u'logon_type']]

        return event_list

    def parse(self, sketch_id):
        events = set()
        for timesketch_event in event_stream(
                sketch_id=sketch_id, query=u'event_identifier:4624'):
            xml_data = timesketch_event[u'_source'].get(u'xml_string')
            timestamp = timesketch_event[u'_source'].get(u'timestamp')
            event_data = self.parse_xml(xml_data)
            event_data.append(timestamp)
            events.add(tuple(event_data))

        # Figure out hostname
        for event in events:
            src_ip = event[0]
            src_hostname = event[1]
            dst_hostname = event[2]
            username = event[3]
            logon_type = event[4]
            timestamp = event[5]
            es_index_name = timesketch_event.get(u'_index')
            es_id = timesketch_event.get(u'_id')

            if src_ip in self.LOCALHOST:
                src_ip = None

            if not src_hostname:
                if not src_ip:
                    src_hostname = dst_hostname
                else:
                    src_hostname = self.kb.get(src_ip)

            yield (src_hostname, username, dst_hostname, logon_type, timestamp,
                   es_index_name, es_id)


def main():
    parser = argparse.ArgumentParser(description='Extract Windows login events')
    parser.add_argument(
        '--sketch', type=int, required=True, help='ID of Timesketch sketch')
    args = parser.parse_args()

    parser = ParseEvents()
    user2id = {}
    sketch_id = args.sketch

    csvwriter = csv.writer(sys.stdout, delimiter=',')
    csvwriter.writerow([u'user', u'uid', u'src', u'dst', u'method', u'timestamp', u'es_index_name', u'es_query', u'sketch_id'])
    for event in parser.parse(sketch_id=sketch_id):
        src_ws, user, dst_ws, method, timestamp, es_index_name, es_id = event
        es_query = u'_index:{} AND _id:{}'.format(es_index_name, es_id)
        uid = user2id.get(user, None)
        if not uid:
            user2id[user] = u'a' + uuid.uuid4().hex
            uid = user2id[user]
        csvwriter.writerow([user, uid, src_ws, dst_ws, method, timestamp, es_index_name, es_query, sketch_id])


def win_logins(sketch_id):
    parser = ParseEvents()
    result = []

    for event in parser.parse(sketch_id=sketch_id):
        src_ws, user, dst_ws, method, timestamp, es_index_name, es_id = event
        result.append({
            u'user': user,
            u'src': src_ws,
            u'dst': dst_ws,
            u'method': method,
            u'timestamp': timestamp,
            u'es_index_name': es_index_name,
            u'es_query': u'_index:{} AND _id:{}'.format(es_index_name, es_id)
        })
    return result


if __name__ == "__main__":
    from timesketch import create_app
    with create_app().app_context():
        main()
