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
import logging
import os
import subprocess

logger = logging.getLogger("timesketch.e2e_manager")


class EndToEndTestManager(object):
    """The test manager."""

    _class_registry = {}
    _exclude_registry = set()

    @classmethod
    def get_git_root(cls):
        """Finds the git repository root.

        Returns:
            str: The path to the git root, or None if not found.
        """
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            while current_dir != os.path.dirname(current_dir):
                if os.path.exists(os.path.join(current_dir, ".git")):
                    return current_dir
                current_dir = os.path.dirname(current_dir)
        except Exception as e:  # pylint: disable=broad-except
            logger.debug("Error while searching for git root: %s", str(e))
        return None

    @classmethod
    def get_last_modified(cls, test_class, git_root=None):
        """Determines the last modified time of a test class.

        It first tries to get the timestamp from git history, and falls back to
        the filesystem modification time.

        Args:
            test_class (type): The test class to check.
            git_root (str): Optional. The git repository root.

        Returns:
            int: The UNIX timestamp of the last modification.
        """
        try:
            file_path = inspect.getfile(test_class)

            if git_root:
                # If the file is imported from a virtualenv (outside git root),
                # try to find the corresponding source file in the git root.
                if not file_path.startswith(git_root):
                    filename = os.path.basename(file_path)
                    source_path = os.path.join(git_root, "end_to_end_tests", filename)
                    if os.path.exists(source_path):
                        file_path = source_path

                try:
                    rel_path = os.path.relpath(file_path, git_root)
                    res = subprocess.run(
                        [
                            "git",
                            "log",
                            "-1",
                            "--format=%at",
                            "--",
                            rel_path,
                        ],
                        capture_output=True,
                        text=True,
                        check=False,
                        cwd=git_root,
                    )
                    if res.returncode == 0 and res.stdout.strip():
                        return int(res.stdout.strip())
                except (subprocess.SubprocessError, ValueError, OSError) as e:
                    logger.debug(
                        "Git log failed for %s: %s", test_class.__name__, str(e)
                    )

            return int(os.path.getmtime(file_path))
        except (TypeError, OSError) as e:
            logger.warning(
                "Could not determine last modified time for %s: %s. "
                "Falling back to epoch (0).",
                test_class.__name__,
                str(e),
            )
            return 0

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
            git_root = cls.get_git_root()
            tests.sort(
                key=lambda x: cls.get_last_modified(x[1], git_root=git_root),
                reverse=True,
            )

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
