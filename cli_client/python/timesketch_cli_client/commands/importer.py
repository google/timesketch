import time

import click
from timesketch_import_client import importer as import_client


@click.command('import', help='Import timelines.')
@click.option('--name')
@click.argument('file_path', type=click.Path(exists=True))
@click.pass_context
def importer(ctx, name, file_path):
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
