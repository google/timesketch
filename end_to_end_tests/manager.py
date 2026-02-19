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

import inspect
import os
import subprocess


class EndToEndTestManager(object):
    """The test manager."""

    _class_registry = {}
    _exclude_registry = set()

    @classmethod
    def get_tests(cls, sort_by_mtime=False):
        """Retrieves all registered end-to-end test classes.

        This method yields test classes that have been registered using the
        `register_test` method, excluding any that were marked for exclusion.

        Args:
            sort_by_mtime (bool): Optional. If True, tests are sorted by the
                modification time of the source file where the test class is
                defined, with the most recently modified tests yielded first.
                Defaults to False.

        Yields:
            tuple: A pair containing:
                str: The uniquely identifying name of the test.
                type: The test class (subclass of BaseEndToEndTest).
        """
        tests = []
        for test_name, test_class in iter(cls._class_registry.items()):
            if test_name in cls._exclude_registry:
                continue
            tests.append((test_name, test_class))

        if sort_by_mtime:
            # Find the git root by looking for .git folder starting from this file
            try:
                git_root = None
                current_dir = os.path.dirname(os.path.abspath(__file__))
                while current_dir != os.path.dirname(current_dir):
                    if os.path.exists(os.path.join(current_dir, ".git")):
                        git_root = current_dir
                        break
                    current_dir = os.path.dirname(current_dir)

                if git_root:
                    # Mark the directory as safe for git
                    subprocess.run(
                        [
                            "git",
                            "config",
                            "--global",
                            "--add",
                            "safe.directory",
                            git_root,
                        ],
                        capture_output=True,
                        check=False,
                    )

            except Exception:  # pylint: disable=broad-except
                git_root = None

            # Sort by modification time of the file where the class is defined.
            def get_mtime(test_item):
                _, test_class = test_item
                try:
                    file_path = inspect.getfile(test_class)

                    # Try to get the latest commit timestamp from git first.
                    if git_root:
                        try:
                            rel_path = os.path.relpath(file_path, git_root)
                            res = subprocess.run(
                                ["git", "log", "-1", "--format=%at", "--", rel_path],
                                capture_output=True,
                                text=True,
                                check=False,
                                cwd=git_root,
                            )
                            if res.returncode == 0 and res.stdout.strip():
                                return int(res.stdout.strip())
                        except (subprocess.SubprocessError, ValueError, OSError):
                            pass

                    return os.path.getmtime(file_path)
                except (TypeError, OSError):
                    return 0

            tests.sort(key=get_mtime, reverse=True)

        for test_name, test_class in tests:
            yield test_name, test_class

    @classmethod
    def get_test(cls, test_name):
        """Retrieves a class object of a specific test.

        Args:
            test_name (str): name of the test to retrieve.

        Returns:
            type: The test class class object.

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
        """Registers a test class.

        The test classes are identified by their lower case name.

        Args:
            test_class (type): the test class to register.
            exclude_from_list (bool): if set to True then the test
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
