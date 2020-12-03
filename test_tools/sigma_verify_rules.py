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
"""A tool to test sigma rules.

This tool can be used to verify your rules before running an analyzer.
It also does not require you to have a full blown Timesketch instance.
Default this tool will show only the rules that cause problems.
Example way of running the tool:
$ PYTHONPATH=. python3 test_tools/sigma_verify_rules.py --config_file 
../data/sigma_config.yaml  --config_file data/sigma_config.yaml 
--debug data/sigma/rules/windows/ --move data/sigma/rules/problematic/
"""


import logging
import os
import argparse
import sys

from timesketch.lib import sigma_util

logger = logging.getLogger('timesketch.test_tool.sigma-verify')
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))


def run_verifier(rules_path, config_file_path):
    """Run an sigma parsing test on a dir and returns results from the run.

    Args:
        rules_path: the path to the rules.
        config_file_path: the path to a config file that contains mapping data.

    Raises:
        IOError: if the path to either test or analyzer file does not exist
                 or if the analyzer module or class cannot be loaded.

    Returns:
        a tuple of lists:
            - sigma_verified_rules with rules that can be added
            - sigma_rules_with_problems with rules that should not be added
    """
    if not os.path.isdir(rules_path):
        raise IOError('Rules not found at path: {0:s}'.format(
            rules_path))
    if not os.path.isfile(config_file_path):
        raise IOError('Config file path not found at path: {0:s}'.format(
            config_file_path))

    sigma_config = sigma_util.get_sigma_config_file(
        config_file=config_file_path)

    return_verified_rules = []
    return_rules_with_problems = []

    for dirpath, dirnames, files in os.walk(rules_path):
        if 'deprecated' in [x.lower() for x in dirnames]:
            dirnames.remove('deprecated')

        for rule_filename in files:
            if rule_filename.lower().endswith('.yml'):
                # if a sub dir is found, do not try to parse it.
                if os.path.isdir(os.path.join(dirpath, rule_filename)):
                    continue

                rule_file_path = os.path.join(dirpath, rule_filename)
                parsed_rule = sigma_util.get_sigma_rule(
                    rule_file_path, sigma_config)
                if parsed_rule:
                    return_verified_rules.append(rule_file_path)
                else:
                    return_rules_with_problems.append(rule_file_path)

    return return_verified_rules, return_rules_with_problems


def move_problematic_rule(filepath, move_to_path, reason=""):
    """ Moves a problematic rule to a subfolder so it is not used again

    Args:
        filepath: path to the sigma rule that caused problems
        move_to_path: path to move the problematic rules to
        reason (optional): reason why file is moved

    Returns:
        Nothing
    """

    logging.info('Moving the rule: {0:s} to {1:s}'.format(
        filepath, move_to_path))

    os.makedirs(move_to_path, exist_ok=True)
    file_object = open('{0:s}debug.log'.format(move_to_path), 'a')
    file_object.write('{0:s}\n{1:s}\n\n'.format(filepath, reason))
    file_object.close()
    os.rename(filepath, '{0:s}{1:s}'.format(
        move_to_path, os.path.basename(filepath)))



if __name__ == '__main__':

    description = (
        'Mock an sigma parser run. This tool is intended for developers '
        'of sigma rules as well as Timesketch server admins. '
        'The tool can also be used for automatic testing to make sure the '
        'rules are still working as intended.')
    epilog = (
        'Remember to feed the tool with proper rule data.'
    )

    arguments = argparse.ArgumentParser(
        description=description, allow_abbrev=True)
    arguments.add_argument(
        '--config_file', '--file', dest='config_file_path', action='store',
        default='', type=str, metavar='PATH_TO_TEST_FILE', help=(
            'Path to the file containing the config data to feed sigma '
        ))
    arguments.add_argument(
        'rules_path', action='store', default='', type=str,
        metavar='PATH_TO_RULES', help='Path to the rules to test.')
    arguments.add_argument(
        '--debug', action='store_true', help='print debug messages ')
    arguments.add_argument(
        '--info', action='store_true', help='print info messages ')
    arguments.add_argument(
        '--move', dest='move_to_path', action='store',
        default='', type=str, help=(
            'Path to the file containing the config data to feed sigma '
        ))
    try:
        options = arguments.parse_args()
    except UnicodeEncodeError:
        print(arguments.format_help())
        sys.exit(1)

    if options.debug:
        logger.setLevel(logging.DEBUG)

    if options.info:
        logger.setLevel(logging.INFO)

    if not os.path.isfile(options.config_file_path):
        print('Config file not found.')
        sys.exit(1)

    if not os.path.isdir(options.rules_path):
        print('The path to the rules does not exist ({0:s})'.format(
            options.rules_path))
        sys.exit(1)

    sigma_verified_rules, sigma_rules_with_problems = run_verifier(
        rules_path=options.rules_path,
        config_file_path=options.config_file_path)

    if len(sigma_rules_with_problems) > 0:
        print('### You should NOT import the following rules ###')
        print('### To get the reason per rule, re-run with --info###')
        for badrule in sigma_rules_with_problems:
            if options.move_to_path:
                move_problematic_rule(
                    badrule, options.move_to_path,
                    "sigma_verify_rules.py found an issue")
            print(badrule)

    if len(sigma_verified_rules) > 0:
        logging.info('### You can import the following rules ###')
        for goodrule in sigma_verified_rules:
            logging.info(goodrule)
