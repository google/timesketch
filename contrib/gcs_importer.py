# Copyright 2020 Google Inc. All rights reserved.
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
"""Google Cloud Storage importer."""
# Unmaintained contrib. Skip linting this file.


import argparse
import json
import logging
import os
import sys
import time
import uuid

from werkzeug.exceptions import Forbidden

from timesketch.app import create_app
from timesketch.lib import tasks
from timesketch.models import db_session
from timesketch.models.sketch import SearchIndex, Sketch, Timeline
from timesketch.models.user import User

try:
    from google.cloud import pubsub_v1, storage
except ImportError:
    sys.exit("ERROR: You are missing Google Cloud libraries")

# Create logger
logger = logging.getLogger("gcs_importer")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


def download_from_gcs(gcs_base_path, filename):
    """Download file from Google Cloud Storage (GCS).

    Args:
        gcs_base_path: (str) GCS bucket path
        filename: (str) Filename of the file to download

    Returns:
        (str) Path to downloaded file
    """
    storage_client = storage.Client(args.project)
    bucket = storage_client.get_bucket(args.bucket)
    gcs_full_path = os.path.join(gcs_base_path, filename)
    local_path = os.path.join(args.output, filename)
    blob = bucket.blob(gcs_full_path)
    blob.download_to_filename(local_path)
    logger.info("Downloaded file from GCS: {}".format(local_path))
    return local_path


def setup_sketch(timeline_name, index_name, username, sketch_id=None):
    """Use existing sketch or create a new sketch.

    Args:
        timeline_name: (str) Name of the Timeline
        index_name: (str) Name of the index
        username: (str) Who should own the timeline
        sketch_id: (str) Optional sketch_id to add timeline to

    Returns:
        (tuple) sketch ID and timeline ID as integers
    """
    with app.app_context():
        user = User.get_or_create(username=username, name=username)
        sketch = None

        if sketch_id:
            try:
                sketch = Sketch.get_with_acl(sketch_id, user=user)
                logger.info(
                    "Using existing sketch: {} ({})".format(sketch.name, sketch.id)
                )
            except Forbidden:
                pass

        if not (sketch or sketch_id):
            # Create a new sketch.
            sketch_name = "Turbinia: {}".format(timeline_name)
            sketch = Sketch(name=sketch_name, description=sketch_name, user=user)
            # Need to commit here to be able to set permissions later.
            db_session.add(sketch)
            db_session.commit()
            sketch.grant_permission(permission="read", user=user)
            sketch.grant_permission(permission="write", user=user)
            sketch.grant_permission(permission="delete", user=user)
            sketch.status.append(sketch.Status(user=None, status="new"))
            db_session.add(sketch)
            db_session.commit()
            logger.info("Created new sketch: {} ({})".format(sketch.name, sketch.id))

        searchindex = SearchIndex.get_or_create(
            name=timeline_name,
            description="Created by Turbinia.",
            user=user,
            index_name=index_name,
        )
        searchindex.grant_permission(permission="read", user=user)
        searchindex.grant_permission(permission="write", user=user)
        searchindex.grant_permission(permission="delete", user=user)
        searchindex.set_status("processing")
        db_session.add(searchindex)
        db_session.commit()

        timeline = Timeline(
            name=searchindex.name,
            description=searchindex.description,
            sketch=sketch,
            user=user,
            searchindex=searchindex,
        )

        # If the user doesn't have write access to the sketch then create the
        # timeline but don't attach it to the sketch.
        if not sketch.has_permission(user, "write"):
            timeline.sketch = None
        else:
            sketch.timelines.append(timeline)

        db_session.add(timeline)
        db_session.commit()
        timeline.set_status("processing")

        return sketch.id, timeline.id


def callback(message):
    """Google PubSub callback.

    This function is called on all incoming messages on the configured topic.

    Args:
        message: (dict) PubSub message
    """
    message.ack()
    gcs_full_path = message.attributes.get("objectId")

    # Exit early if the file type is wrong.
    if not gcs_full_path.endswith(".plaso.metadata.json"):
        return

    gcs_base_path = os.path.dirname(gcs_full_path)
    gcs_metadata_filename = os.path.basename(gcs_full_path)
    gcs_base_filename = gcs_metadata_filename.replace(".metadata.json", "")
    gcs_plaso_filename = gcs_base_filename

    # Download files from GCS
    local_metadata_file = download_from_gcs(gcs_base_path, gcs_metadata_filename)
    local_plaso_file = download_from_gcs(gcs_base_path, gcs_plaso_filename)

    with open(local_metadata_file, "r") as metadata_file:
        metadata = json.load(metadata_file)
        username = metadata.get("globals", {}).get("requester")
        if not username:
            # Backwards compatibility for old Turbinia versions.
            username = metadata.get("requester")
        sketch_id_from_metadata = metadata.get("sketch_id")

    if not username:
        logger.error("Missing username")
        return

    timeline_name = os.path.splitext(gcs_plaso_filename)[0]
    index_name = uuid.uuid4().hex
    sketch_id, timeline_id = setup_sketch(
        timeline_name, index_name, "admin", sketch_id_from_metadata
    )

    # Start indexing
    with app.app_context():
        pipeline = tasks.build_index_pipeline(
            file_path=local_plaso_file,
            timeline_name=gcs_base_filename,
            index_name=index_name,
            file_extension="plaso",
            sketch_id=sketch_id,
            timeline_id=timeline_id,
        )
        pipeline.apply_async()
        logger.info("File sent for indexing: {}".format(gcs_base_filename))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GCS importer")
    parser.add_argument("--project", help="Google Cloud Project ID")
    parser.add_argument("--bucket", help="Google Cloud Storage bucket to monitor")
    parser.add_argument("--subscription", help="Google Cloud PubSub subscription")
    parser.add_argument("--output", default="/tmp", help="Directory for downloads")
    args = parser.parse_args()

    # Create flask app
    app = create_app()

    # Setup Google Cloud Pub/Sub
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(args.project, args.subscription)
    subscriber.subscribe(subscription_path, callback=callback)

    logger.info("Listening on PubSub queue: {}".format(args.subscription))
    while True:
        time.sleep(10)
