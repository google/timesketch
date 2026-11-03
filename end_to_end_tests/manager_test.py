# Copyright 2026 Google Inc. All rights reserved.
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
"""Unit tests for EndToEndTestManager and container test resolution."""

import unittest

from end_to_end_tests import manager
from end_to_end_tests import ui_test
from end_to_end_tests.tools import run_in_container


class _DummyDefaultTest:
    """Dummy E2E test included in default runs."""

    NAME = "dummy_default_test"


class _DummyOptInUiTest:
    """Dummy opt-in UI E2E test excluded from default runs."""

    NAME = "dummy_ui_test"


class TestEndToEndTestManager(unittest.TestCase):
    """Tests for EndToEndTestManager opt-in test handling."""

    def setUp(self):
        """Snapshot and clear global manager registries before each test."""
        super().setUp()
        # pylint: disable=protected-access
        self._saved_classes = dict(manager.EndToEndTestManager._class_registry)
        self._saved_excludes = set(manager.EndToEndTestManager._exclude_registry)
        manager.EndToEndTestManager.clear_registration()
        manager.EndToEndTestManager.register_test(_DummyDefaultTest)
        manager.EndToEndTestManager.register_test(
            _DummyOptInUiTest, exclude_from_list=True
        )

    def tearDown(self):
        """Restore global manager registries after each test."""
        # pylint: disable=protected-access
        manager.EndToEndTestManager._class_registry = self._saved_classes
        manager.EndToEndTestManager._exclude_registry = self._saved_excludes
        super().tearDown()

    def test_get_tests_excludes_opt_in_by_default(self):
        """Default get_tests omits suites registered with exclude_from_list."""
        tests = list(manager.EndToEndTestManager.get_tests())
        self.assertEqual(tests, [("dummy_default_test", _DummyDefaultTest)])

    def test_get_tests_include_excluded(self):
        """get_tests(include_excluded=True) returns opt-in suites as well."""
        tests = dict(manager.EndToEndTestManager.get_tests(include_excluded=True))
        self.assertIn("dummy_default_test", tests)
        self.assertIn("dummy_ui_test", tests)
        self.assertIs(tests["dummy_ui_test"], _DummyOptInUiTest)

    def test_resolve_tests_to_run_default_omits_excluded(self):
        """Default container resolution skips opt-in suites."""
        resolved = run_in_container.resolve_tests_to_run(
            manager.EndToEndTestManager, requested_arg=None
        )
        self.assertEqual(resolved, [("dummy_default_test", _DummyDefaultTest)])

    def test_resolve_tests_to_run_explicit_includes_excluded(self):
        """Explicit CLI filter resolves opt-in suites such as ui_test."""
        resolved = run_in_container.resolve_tests_to_run(
            manager.EndToEndTestManager, requested_arg="dummy_ui_test"
        )
        self.assertEqual(resolved, [("dummy_ui_test", _DummyOptInUiTest)])

    def test_resolve_tests_to_run_unknown_raises_key_error(self):
        """Requesting a nonexistent suite raises KeyError with missing names."""
        with self.assertRaises(KeyError) as ctx:
            run_in_container.resolve_tests_to_run(
                manager.EndToEndTestManager, requested_arg="no_such_suite"
            )
        self.assertIn("no_such_suite", str(ctx.exception))

    def test_real_ui_test_registered_as_opt_in(self):
        """Production ui_test suite is registered and excluded from default runs."""
        self.assertIn("ui_test", self._saved_classes)
        self.assertIs(self._saved_classes["ui_test"], ui_test.UiEndToEndTest)
        self.assertIn("ui_test", self._saved_excludes)


if __name__ == "__main__":
    unittest.main()
