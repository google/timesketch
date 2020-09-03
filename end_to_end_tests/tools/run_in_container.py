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
"""Script to run all end to end tests."""

import time
from collections import Counter

from end_to_end_tests import manager as test_manager

manager = test_manager.EndToEndTestManager()
counter = Counter()


if __name__ == '__main__':
    # Sleep to make sure all containers are operational
    time.sleep(30)

    # Run tests
    for name, cls in manager.get_tests():
        run_counter = cls().run_tests()
        counter['tests'] += run_counter['tests']
        counter['errors'] += run_counter['errors']

    successful_tests = counter['tests'] - counter['errors']
    print('{0:d} total tests: {1:d} successful and {2:d} failed'.format(
        counter['tests'], successful_tests, counter['errors']))

