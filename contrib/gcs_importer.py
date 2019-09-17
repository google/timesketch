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
import json

from timesketch import create_app
from timesketch.lib import tasks
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import Timeline
from timesketch.models.user import User

try:
    from google.cloud import pubsub_v1
    from google.cloud import storage
except ImportError:
    sys.exit('ERROR: You missing Google Cloud libraries.')


parser = argparse.ArgumentParser(description='GCS importer')
parser.add_argument('--project', help='Google Cloud Project ID')
parser.add_argument('--bucket', help='Google Cloud Storage bucket')
parser.add_argument('--subscription', help='Google Cloud PubSub subscription ')
parser.add_argument('--output', default='/tmp', help='Directory for downloads')
args = parser.parse_args()


# Flask app
app = create_app()


def get_gcs_bucket():
    storage_client = storage.Client(args.project)
    return storage_client.get_bucket(args.bucket)


def download_from_gcs(bucket, gcs_base_path, filename):
    gcs_full_path = os.path.join(gcs_base_path, filename)
    local_path = os.path.join(args.output, filename)
    blob = bucket.blob(gcs_full_path)
    blob.download_to_filename(local_path)
    print('Downloaded file from GCS: ', local_path)
    return local_path


def setup_sketch(name, description, username, sketch_id=None):
    with app.app_context():
        timeline_name = gcs_base_filename
        index_name = uuid.uuid4().hex
        user = User.get_or_create(username=username)

        if sketch_id:
            sketch = Sketch.query.get(sketch_id)
        else:
            sketch = Sketch.get_or_create(
                name='Turbinia: {}'.format(gcs_base_filename),
                description='Automatically created by Turbinia.',
                user=user)

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


def callback(message):
    message.ack()
    gcs_full_path = message.attributes.get('objectId')

    if not gcs_full_path.endswith('.plaso.metadata.json'):
        #print('ERROR: Skipping unknown file format: ', gcs_full_path)
        return

    gcs_base_path = os.path.dirname(gcs_full_path)
    gcs_metadata_filename = os.path.basename(gcs_full_path)
    gcs_base_filename = gcs_metadata_filename.replace('.metadata.json', '')
    gcs_plaso_filename = gcs_base_filename

    #print('PubSub message parsed: ', gcs_full_path, gcs_plaso_path)

    # Download files from GCS
    local_metadata_file = download_from_gcs(gcs_base_path, gcs_metadata_filename)
    local_plaso_file = download_from_gcs(gcs_base_path, gcs_plaso_filename)

    print('METADATA FILE: ', local_metadata_file)
    with open(local_metadata_file, 'r') as metadata_file:
        metadata = json.load(metadata_file)
        username = metadata.get('requester')
        sketch_id = metadata.get('sketch_iud')
        print('Parse metadata file: ', username, sketch_id)

    if not username:
        print('ERROR: Missing username')
        return


        # Celery
        pipeline = tasks.build_index_pipeline(
            file_path=local_plaso_file,
            timeline_name=gcs_base_filename,
            index_name=index_name,
            file_extension='plaso',
            sketch_id=sketch_id)
        pipeline.apply_async()




if __name__ == '__main__':

    # Setup Google Cloud Pub/Sub
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        args.project, args.subscription)
    subscriber.subscribe(subscription_path, callback=callback)

    print('Listening on PubSub queue: {}'.format(args.subscription))
    while True:
        time.sleep(10)
    print("foo")