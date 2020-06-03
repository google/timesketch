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

from __future__ import unicode_literals

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

    LOCALHOST = ['::1', '127.0.0.1']

    def __init__(self):
        super(ParseEvents, self).__init__()
        self.events = set()
        self.ip2host = dict()
        self.kb = KnowledgeBase()

    def parse_xml(self, xml):
        event_container = dict()

        logon_types = {
            '0': 'Unknown',
            '2': 'Interactive',
            '3': 'Network',
            '4': 'Batch',
            '5': 'Service',
            '7': 'Unlock',
            '8': 'NetworkCleartext',
            '9': 'NewCredentials',
            '10': 'RemoteInteractive',
            '11': 'CachedInteractive'
        }

        event = parse_xml_event(xml)

        src_ip = event['EventData'].get('IpAddress')
        event_container['src_ip'] = src_ip

        src_hostname = event['EventData'].get('WorkstationName')
        if src_hostname:
            src_hostname = src_hostname.split('.')[0].upper()
        event_container['src_hostname'] = src_hostname

        dst_hostname = event['System']['Computer'].get('value')
        if dst_hostname:
            dst_hostname = dst_hostname.split('.')[0].upper()
        event_container['dst_hostname'] = dst_hostname

        username = event['EventData'].get('TargetUserName')
        event_container['username'] = username

        logon_type = event['EventData'].get('LogonType')
        event_container['logon_type'] = logon_types[logon_type]

        if src_ip and src_hostname:
            self.kb.add(src_ip, src_hostname)

        event_list = [
            event_container['src_ip'],
            event_container['src_hostname'],
            event_container['dst_hostname'],
            event_container['username'],
            event_container['logon_type']]

        return event_list

    def parse(self, sketch_id):
        events = set()
        for timesketch_event in event_stream(
                sketch_id=sketch_id, query='event_identifier:4624'):
            xml_data = timesketch_event['_source'].get('xml_string')
            timestamp = timesketch_event['_source'].get('timestamp')
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
            es_index_name = timesketch_event.get('_index')
            es_id = timesketch_event.get('_id')

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
    csvwriter.writerow(['user', 'uid', 'src', 'dst', 'method', 'timestamp', 'es_index_name', 'es_query', 'sketch_id'])
    for event in parser.parse(sketch_id=sketch_id):
        src_ws, user, dst_ws, method, timestamp, es_index_name, es_id = event
        es_query = '_index:{} AND _id:{}'.format(es_index_name, es_id)
        uid = user2id.get(user, None)
        if not uid:
            user2id[user] = 'a' + uuid.uuid4().hex
            uid = user2id[user]
        csvwriter.writerow([user, uid, src_ws, dst_ws, method, timestamp, es_index_name, es_query, sketch_id])


def win_logins(sketch_id):
    parser = ParseEvents()
    result = []

    for event in parser.parse(sketch_id=sketch_id):
        src_ws, user, dst_ws, method, timestamp, es_index_name, es_id = event
        result.append({
            'user': user,
            'src': src_ws,
            'dst': dst_ws,
            'method': method,
            'timestamp': timestamp,
            'es_index_name': es_index_name,
            'es_query': '_index:{} AND _id:{}'.format(es_index_name, es_id)
        })
    return result


if __name__ == "__main__":
    from timesketch.app import create_app
    with create_app().app_context():
        main()
