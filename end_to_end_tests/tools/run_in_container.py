from end_to_end_tests import manager as test_manager

import time
from collections import Counter

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

