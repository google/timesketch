# Copyright 2015 Google Inc. All rights reserved.
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
"""Celery task for processing Plaso storage files."""

from plaso.frontend import psort
from plaso.output import manager as output_manager

from timesketch import create_celery_app

celery = create_celery_app()


class PlasoOptions(object):
    """Plaso options"""


class PsortCeleryFrontend(psort.PsortFrontend):
    """Post process class for plaso storage files."""
    def ParseOptions(self, options):
        """Setup the necessary options for psort."""
        output_format = getattr(options, u'output_format', None)
        self._output_format = output_format
        self._storage_file_path = getattr(options, u'storage_file', None)
        self._data_location = getattr(options, u'data_location', None)
        self._output_module_class = output_manager.OutputManager.GetOutputClass(
            output_format)


class PlasoCeleryTask(object):
    """Celery task for Plaso"""
    def process_file(self, source_file_path, timeline_name, index_name):
        """Process plaso storage file.

        Args:
            source_file_path: Path to plaso storage file.
            timeline_name: Name of the Timesketch timeline.
            index_name: Name of the datastore index.

        Returns:
            Count of processed events (Instance of collections.Counter).
        """
        options = PlasoOptions()
        options.analysis_plugins = u''
        options.dedup = True
        options.output_format = u'timesketch'
        options.quiet = False
        options.slice = u''
        options.zone = u'UTC'
        options.debug = True

        options.flush_interval = 1000
        options.index = index_name
        options.name = timeline_name
        options.owner = None
        options.storage_file = source_file_path

        psort_frontend = PsortCeleryFrontend()
        psort_frontend.ParseOptions(options)
        counter = psort_frontend.ProcessStorage(options, None)
        return counter


@celery.task(track_started=True)
def run_plaso(source_file_path, timeline_name, index_name):
    """Create a Celery task for processing Plaso storage file.

    Args:
        source_file_path: Path to plaso storage file.
        timeline_name: Name of the Timesketch timeline.
        index_name: Name of the datastore index.

    Returns:
        Dictionary with count of processed events.
    """
    l2c = PlasoCeleryTask()
    counter = l2c.process_file(source_file_path, timeline_name, index_name)
    return dict(counter)
