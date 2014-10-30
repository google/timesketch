# Copyright 2014 Google Inc. All rights reserved.
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
"""Add ElasticSearch index to Timesketch"""

# Note: The reason we need to do some funky import order here is because Django
# needs some special setup in order to get it's environment correct.
import argparse
import os
import sys

import django
from pyelasticsearch import ElasticSearch
from pyelasticsearch.exceptions import ConnectionError

# We need to add the parent directory to the Python path in order to be able
# to import timesketch modules.
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timesketch.settings')
django.setup()

# Django and timesketch imports
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from timesketch.apps.sketch.models import Timeline


def main():
    """
    Create timeline in Timesketch and bind to a specific index in
    ElasticSearch.

    Returns:
        0 on success and 1 on error.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-u', '--user', required=True,
        help='Timesketch username to set as owner of the timeline')
    parser.add_argument(
        '-s', '--server', default='127.0.0.1',
        help='IP address or hostname for ElasticSearch server')
    parser.add_argument(
        '-p', '--port', default='9200',
        help='Port number on ElasticSearch server')
    parser.add_argument(
        '-n', '--name', required=True,
        help='The name of the timeline in Timesketch')
    parser.add_argument(
        '-i', '--index', required=True,
        help='The name of the index in ElasticSearch')
    parser.parse_args()
    args = parser.parse_args()

    try:
        user = User.objects.get(username=args.user)
    except ObjectDoesNotExist:
        sys.stderr.write(
            'ERROR: User does not exist\n')
        return 1

    elasticsearch = ElasticSearch('http://{server}:{port}'.format(
        server=args.server, port=args.port))

    # Tell ElasticSearch that a timesketch label is a nested documents.
    # This makes it possible to filter on labels.
    mapping = {
        'plaso_event': {
            u'properties': {
                u'timesketch_label': {
                    'type': 'nested'}
            }
        },
    }

    try:
        # Make sure ElasticSearch is ready.
        elasticsearch.health(wait_for_status='yellow')
        elasticsearch.put_mapping(args.index, 'plaso_event', mapping)
    except ConnectionError:
        sys.stderr.write(
            'ERROR: Unable to connect to the ElasticSearch backend\n')
        return 1

    timeline, created = Timeline.objects.get_or_create(
        user=user, title=args.name, description=args.name,
        datastore_index=args.index)
    if not created:
        sys.stderr.write('ERROR: Timeline already exists\n')
        return 1
    # Make the timeline public by default.
    timeline.make_public(user)
    return 0


if __name__ == '__main__':
    sys.exit(main())
