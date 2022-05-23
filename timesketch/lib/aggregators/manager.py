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
"""This file contains a class for managing aggregators."""

from __future__ import unicode_literals


class AggregatorManager(object):
    """The aggregator manager."""

    _class_registry = {}
    _exclude_registry = set()

    @classmethod
    def get_aggregators(cls):
        """Retrieves the registered aggregators.

        Yields:
            tuple: containing:
                unicode: the uniquely identifying name of the aggregator
                type: the aggregator class.
        """
        for agg_name, agg_class in iter(cls._class_registry.items()):
            if agg_name in cls._exclude_registry:
                continue
            yield agg_name, agg_class

    @classmethod
    def get_aggregator(cls, aggregator_name):
        """Retrieves a class object of a specific aggregator.

        Args:
            aggregator_name (unicode): name of the aggregator to retrieve.

        Returns:
            Instance of Aggregator class object.

        Raises:
            KeyError: if the aggregator is not registered.
        """
        try:
            aggregator_class = cls._class_registry[aggregator_name.lower()]
        except KeyError:
            raise KeyError("No such chart type: {0:s}".format(aggregator_name.lower()))
        return aggregator_class

    @classmethod
    def register_aggregator(cls, aggregator_class, exclude_from_list=False):
        """Registers an aggregator class.

        The aggregator classes are identified by their lower case name.

        Args:
            aggregator_class (type): the aggregator class to register.
            exclude_from_list (boolean): if set to True then the aggregator
                gets registered but will not be included in the
                get_aggregators function. Defaults to False.

        Raises:
            KeyError: if class is already set for the corresponding name.
        """
        aggregator_name = aggregator_class.NAME.lower()
        if aggregator_name in cls._class_registry:
            raise KeyError(
                "Class already set for name: {0:s}.".format(aggregator_class.NAME)
            )
        cls._class_registry[aggregator_name] = aggregator_class
        if exclude_from_list:
            cls._exclude_registry.add(aggregator_name)

    @classmethod
    def clear_registration(cls):
        """Clears all aggregator registrations."""
        cls._class_registry = {}
        cls._exclude_registry = set()
