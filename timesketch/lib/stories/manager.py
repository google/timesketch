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
"""This file contains a class for managing story exporters."""

from __future__ import unicode_literals


class StoryExportManager(object):
    """The story export manager."""

    _class_registry = {}

    @classmethod
    def clear_registration(cls):
        """Clears all analyzer registration."""
        cls._class_registry = {}

    @classmethod
    def get_exporters(cls, exporter_types=None):
        """Retrieves the registered story exporters.

        Args:
            exporter_types (list): List of exporter types.

        Yields:
            tuple: containing:
                str: the uniquely identifying name of the story exporter.
                type: the exporter class.
        """
        for exporter_type, exporter_class in cls._class_registry.items():
            if exporter_types and exporter_type not in exporter_types:
                continue
            yield exporter_type, exporter_class

    @classmethod
    def get_formats(cls):
        """Retrieves the registered format types."""
        return cls._class_registry.keys()

    @classmethod
    def get_exporter(cls, exporter_type):
        """Retrieves a class object of a specific exporter.

        Args:
            exporter_type (str): name of the exporter to retrieve.

        Returns:
            StoryExporter class object.
        """
        return cls._class_registry.get(exporter_type.lower())

    @classmethod
    def register_exporter(cls, exporter_class):
        """Registers an exporter class.

        The exporter classes are identified by their lower export format.

        Args:
            exporter_class (type): the exporter class to register.

        Raises:
            KeyError: if class is already set for the corresponding name.
        """
        exporter_type = exporter_class.EXPORT_FORMAT.lower()
        if exporter_type in cls._class_registry:
            raise KeyError(
                "Class already set for name: {0:s}.".format(
                    exporter_class.EXPORT_FORMAT
                )
            )

        cls._class_registry[exporter_type] = exporter_class
