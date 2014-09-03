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

from pyelasticsearch import ElasticSearch


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "timesketch.settings")
from django.contrib.auth.models import User

from timesketch.apps.sketch.models import Timeline


user = User.objects.get(id=2)
es_server = sys.argv[1]
es_port = sys.argv[2]
name = sys.argv[3]
index = sys.argv[4]

es = ElasticSearch("http://%s:%s" % (es_server, es_port))

mapping = {
        "plaso_event": {
            u'properties': {
                u'timesketch_label': {
                    "type": "nested"}
            }
        },
}

es.put_mapping(index, "plaso_event", mapping)
timeline = Timeline.objects.create(owner=user, acl_public=True, title=name, description=name, datastore_index=index)
