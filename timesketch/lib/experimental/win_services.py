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
import csv
import sys
import argparse
from xml.etree import ElementTree

from timesketch.models.sketch import Sketch
from timesketch.lib.experimental.utils import event_stream


def parse_xml(data):
    base_node = './/{http://schemas.microsoft.com/win/2004/08/events/event}'

    root = ElementTree.fromstring(data)
    d = dict()
    d['src_ws'] = root.find('{0:s}Computer'.format(base_node)).text
    d['svc_name'] = root.find(
        '{0:s}Data[@Name="ServiceName"]'.format(base_node)).text
    d['start_type'] = root.find(
        '{0:s}Data[@Name="StartType"]'.format(base_node)).text
    d['image_path'] = root.find(
        '{0:s}Data[@Name="ImagePath"]'.format(base_node)).text

    return [d['src_ws'], d['svc_name'], d['start_type'], d['image_path']]


def main():
    parser = argparse.ArgumentParser(description='Extract Windows services')
    parser.add_argument(
        '--sketch', type=int, required=True, help='ID of Timesketch sketch')
    args = parser.parse_args()

    events = set()
    sketch_id = args.sketch

    for event in event_stream(
            sketch_id=sketch_id, query='event_identifier:7045'):
        data = event['_source']['xml_string']
        res = parse_xml(data)
        if res:
            events.add(res)

    csvwriter = csv.writer(sys.stdout, delimiter=',')
    csvwriter.writerow(['src', 'svc_name', 'start_type', 'image_path'])
    for event in events:
        src_ws, svc_name, start_type, image_path = event
        src_ws = src_ws.split('.')[0].upper()
        csvwriter.writerow([src_ws, svc_name, start_type, image_path])


def win_services(sketch_id):
    events = set()

    for event in event_stream(
            sketch_id=sketch_id, query='event_identifier:7045'):
        data = event['_source']['xml_string']
        res = parse_xml(data)
        res.extend(
            (
                event['_source'].get('timestamp'),
                event.get('_index'),
                event.get('_id')
            )
        )
        res = tuple(res)
        if res:
            events.add(res)

    result = []
    for event in events:
        src_ws = event[0]
        svc_name = event[1]
        start_type = event[2]
        image_path = event[3]
        image_path_short = image_path.strip().strip('\\').split('\\')[-1]
        timestamp = event[4]
        es_index_name = event[5]
        es_id = event[6]

        src_ws = src_ws.split('.')[0].upper()

        result.append({
            'src': src_ws,
            'svc_name': svc_name,
            'start_type': start_type,
            'image_path': image_path,
            'image_path_short': image_path_short,
            'timestamp': timestamp,
            'es_index_name': es_index_name,
            'es_query': '_index:{} AND _id:{}'.format(es_index_name, es_id)
        })
    return result


if __name__ == "__main__":
    from timesketch import create_app
    with create_app().app_context():
        main()
