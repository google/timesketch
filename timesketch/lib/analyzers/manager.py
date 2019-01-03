# Copyright 2018 Google Inc. All rights reserved.
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
"""This file contains a class for managing analyzers."""

from __future__ import unicode_literals


class AnalysisManager(object):
    """The analyzer manager."""

    _class_registry = {}

    @classmethod
    def _build_dependencies(cls):
        """Build a dependency list of analyzers.

        Returns:
            A list of sets, each one representing each priority
            of analyzers.

        Raises:
            KeyError: if class introduces circular dependencies.
        """
        dependency_tree = []

        dependencies = {}
        for name, analyzer_class in iter(cls._class_registry.items()):
            dependencies[name] = [
                x.lower() for x in analyzer_class.DEPENDENCIES]

        while dependencies:
            dependency_list = []
            for value in iter(dependencies.values()):
                dependency_list.extend(value)

            # Find items without a dependency.
            dependency_set = set(dependency_list) - set(dependencies.keys())
            dependency_set.update(
                d for d, v in iter(dependencies.items()) if not v)

            if not dependency_set:
                raise KeyError((
                    'Unable to build dependency tree, there is a circular '
                    'dependency somewhere'))

            dependency_tree.append(dependency_set)

            # Let's remove these entries from the dependencies dict.
            new_dependencies = {}
            for name, analyzer_dependencies in dependencies.items():
                if not analyzer_dependencies:
                    continue
                new_dependencies[name] = list(
                    set(analyzer_dependencies) - dependency_set)
            dependencies = new_dependencies

        #print 'AND NOW'
        #print cls._class_ordering
        return dependency_tree

    @classmethod
    def clear_registration(cls):
        """Clears all analyzer registration."""
        cls._class_ordering = []
        cls._class_registry = {}

    @classmethod
    def get_analyzers(cls):
        """Retrieves the registered analyzers.

        Yields:
            tuple: containing:
                str: the uniquely identifying name of the analyzer
                type: the analyzer class.
        """
        for cluster in cls._build_dependencies():
            for analyzer_name in cluster:
                analyzer_class = cls.get_analyzer(analyzer_name)
                yield analyzer_name, analyzer_class

    @classmethod
    def get_analyzer(cls, analyzer_name):
        """Retrieves a class object of a specific analyzer.

        Args:
            analyzer_name (str): name of the analyzer to retrieve.

        Returns:
            Analyzer class object.
        """
        return cls._class_registry[analyzer_name.lower()]

    @classmethod
    def register_analyzer(cls, analyzer_class):
        """Registers an analyzer class.

        The analyzer classes are identified by their lower case name.

        Args:
            analyzer_class (type): the analyzer class to register.

        Raises:
            KeyError: if class is already set for the corresponding name.
        """
        analyzer_name = analyzer_class.NAME.lower()
        if analyzer_name in cls._class_registry:
            raise KeyError('Class already set for name: {0:s}.'.format(
                analyzer_class.NAME))
        cls._class_registry[analyzer_name] = analyzer_class
