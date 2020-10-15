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
"""Commands for importing timelines."""

import time

import click
from timesketch_import_client import importer as import_client


@click.command('import')
@click.option('--name', help='Name of the timeline.')
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def importer(ctx, name, file_path):
    """Import timeline.

    Args:
        ctx: Click CLI context object.
        name: Name of the timeline to create.
        file_path: File path to the file to import.
    """
    sketch = ctx.obj.sketch
    if not name:
        name = click.format_filename(file_path, shorten=True)

    with import_client.ImportStreamer() as streamer:
        click.echo('Uploading to server .. ', nl=False)
        streamer.set_sketch(sketch)
        streamer.set_timeline_name(name)
        streamer.add_file(file_path)
        timeline = streamer.timeline
        click.echo('Done')

    # Poll the timeline status and wait for the timeline to be ready
    click.echo('Indexing .. ', nl=False)
    max_time_seconds = 600  # Timeout after 10min
    sleep_time_seconds = 5  # Sleep between API calls
    max_retries = max_time_seconds / sleep_time_seconds
    retry_count = 0
    while True:
        if retry_count >= max_retries:
            click.echo('ERROR: The import timed out.')
        _ = timeline.lazyload_data(refresh_cache=True)
        status = timeline.status
        # TODO: Do something with other statuses? (e.g. failed)
        if status == 'ready':
            click.echo('Done')
            break
        retry_count += 1
        time.sleep(sleep_time_seconds)

    click.echo('Timeline imported: {}'.format(timeline.name))
