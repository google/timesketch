# Copyright 2019 Google Inc. All rights reserved.
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

import argparse
import time
import os
import sys
import uuid

#from timesketch import create_app
#from timesketch.lib import tasks
#from timesketch.models import db_session
#from timesketch.models.user import User
#from timesketch.models.sketch import SearchIndex
#from timesketch.models.sketch import Sketch
#from timesketch.models.sketch import Timeline

#from google.cloud import pubsub_v1
#from google.cloud import storage


parser = argparse.ArgumentParser(description='GCS importer')
parser.add_argument(
    'project', dest='PROJECT_ID', action='store_const',
    help='Google Cloud Project ID')
parser.add_argument(
    'bucket', dest='BUCKET_TO_WATCH', action='store_const',
    help='Google Cloud Storage bucket to watch')
parser.add_argument(
    'subscription', dest='SUBSCRIPTION', action='store_const',
    help='Google Cloud PubSub subscription name')
parser.add_argument(
    'output_dir', dest='OUTPUT_DIR', default='/tmp', action='store_const',
    help='Directory to store downloaded files')
args = parser.parse_args()


# TODO: Make these flags
#PROJECT_ID = 'turbinia-dev'
#SUBSCRIPTION = 'timesketch-gcs-subscriber'
#BUCKET_TO_WATCH = 'turbinia-ad9ed98e884b56bc'
#OUTPUT_DIR = '/tmp/'

print(PROJECT_ID)
print(SUBSCRIPTION)
print(BUCKET_TO_WATCH)
print(OUTPUT_DIR)

sys.exit()

# Should come from Turbinia
USERNAME = 'admin'
SKETCH_ID = 5

# Setup Google Cloud Pub/Sub
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION)

# Setup Google Cloud Storage
storage_client = storage.Client(PROJECT_ID)
bucket = storage_client.get_bucket(BUCKET_TO_WATCH)

# Flask app
app = create_app()


def download_file_from_gcs(gcs_path, local_path):
    blob = bucket.blob(gcs_path)
    blob.download_to_filename(local_path)
    return local_path


def callback(message):
    message.ack()
    gcs_path = message.attributes.get('objectId')
    gcs_filename = os.path.basename(gcs_path)
    _, extension = os.path.splitext(gcs_path)
    local_path = OUTPUT_DIR + '/' + gcs_filename

    supported_extensions = (['.plaso'])
    if extension not in supported_extensions:
        return

    local_file = download_file_from_gcs(gcs_path, local_path)
    if not local_file:
        return

    with app.app_context():
        timeline_name = gcs_filename
        index_name = uuid.uuid4().hex
        user = User.query.filter_by(USERNAME).first()
        sketch = Sketch.query.get(SKETCH_ID)

        searchindex = SearchIndex.get_or_create(
            name=timeline_name,
            description=timeline_name,
            user=user,
            index_name=index_name)
        searchindex.grant_permission(permission='read', user=user)
        searchindex.grant_permission(permission='write', user=user)
        searchindex.grant_permission(permission='delete', user=user)
        searchindex.set_status('processing')
        db_session.add(searchindex)
        db_session.commit()

        if sketch and sketch.has_permission(user, 'write'):
            timeline = Timeline(
                name=searchindex.name,
                description=searchindex.description,
                sketch=sketch,
                user=user,
                searchindex=searchindex)
            timeline.set_status('processing')
            sketch.timelines.append(timeline)
            db_session.add(timeline)
            db_session.commit()

        # Celery
        pipeline = tasks.build_index_pipeline(
            file_path=local_file,
            timeline_name=local_file,
            index_name=index_name,
            file_extension=extension.lstrip('.'),
            sketch_id=SKETCH_ID)
        pipeline.apply_async()


subscriber.subscribe(subscription_path, callback=callback)

while True:
    time.sleep(10)
