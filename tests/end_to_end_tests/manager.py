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
"""This file contains a class for managing end to end tests."""


class EndToEndTestManager(object):
    """The test manager."""

    _class_registry = {}
    _exclude_registry = set()

    @classmethod
    def get_tests(cls):
        """Retrieves the registered tests.

        Yields:
            tuple: containing:
                unicode: the uniquely identifying name of the test
                type: the test class.
        """
        for test_name, test_class in iter(cls._class_registry.items()):
            if test_name in cls._exclude_registry:
                continue
            yield test_name, test_class

    @classmethod
    def get_test(cls, test_name):
        """Retrieves a class object of a specific test.

        Args:
            test_name (unicode): name of the test to retrieve.

        Returns:
            Instance of Test class object.

        Raises:
            KeyError: if the test is not registered.
        """
        # pylint: disable=raise-missing-from
        try:
            test_class = cls._class_registry[test_name.lower()]
        except KeyError:
            raise KeyError("No such test type: {0:s}".format(test_name.lower()))
        return test_class

    @classmethod
    def register_test(cls, test_class, exclude_from_list=False):
        """Registers an test class.

        The test classes are identified by their lower case name.

        Args:
            test_class (type): the test class to register.
            exclude_from_list (boolean): if set to True then the test
                gets registered but will not be included in the
                get_tests function. Defaults to False.

        Raises:
            KeyError: if class is already set for the corresponding name.
        """
        test_name = test_class.NAME.lower()
        if test_name in cls._class_registry:
            raise KeyError("Class already set for name: {0:s}.".format(test_class.NAME))
        cls._class_registry[test_name] = test_class
        if exclude_from_list:
            cls._exclude_registry.add(test_name)

    @classmethod
    def clear_registration(cls):
        """Clears all test registrations."""
        cls._class_registry = {}
        cls._exclude_registry = set()
