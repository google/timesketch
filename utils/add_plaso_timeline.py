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
"""Add Plaso timeline to timesketch"""

import os
import sys
import argparse

import django
from pyelasticsearch import ElasticSearch

# We need to add the parent directory to the Python path in order to be able
# to import timesketch modules.
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "timesketch.settings")
django.setup()

# Django and timesketch imports
from django.contrib.auth.models import User
from timesketch.apps.sketch.models import Timeline


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--user", help="Timesketch username to set as owner of the timeline")
    parser.add_argument(
        "--es_server", help="IP address or hostname for Elasticsearch server")
    parser.add_argument(
        "--es_port", help="Port number on Elasticsearch server")
    parser.add_argument(
        "--timeline_name", help="The name of the timeline in Timesketch")
    parser.add_argument(
        "--index_name", help="The name of the index in Elasticsearch")
    parser.parse_args()
    args = parser.parse_args()

    user = User.objects.get(username=args.user)
    es = ElasticSearch("http://%s:%s" % (args.es_server, args.es_port))

    mapping = {
            "plaso_event": {
                u'properties': {
                    u'timesketch_label': {
                        "type": "nested"}
                }
            },
    }

    timeline, created = Timeline.objects.get_or_create(
        user=user, title=args.timeline_name, description=args.timeline_name,
        datastore_index=args.index_name)
    if not created:
        print "Timeline already exists!"
        sys.exit()
    timeline.make_public(user)
    es.put_mapping(args.index_name, "plaso_event", mapping)
