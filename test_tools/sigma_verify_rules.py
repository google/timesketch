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
  $ sigma_verify_rules.py --config_file ../data/sigma_config.yaml ../data/linux/
"""


import logging
import os
import argparse
import sys
import codecs
import sigma.parser.exceptions
import sigma.configuration as sigma_configuration

from sigma.backends import elasticsearch as sigma_elasticsearch
from sigma.parser import collection as sigma_collection

logger = logging.getLogger('timesketch.test_tool.sigma-verify')
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO'))

RULE_EXTENSIONS = ('yml', 'yaml')

def get_codepath():
    """Return the absolute path to where the tool is run from."""
    # TODO: move this function to a library as it is duplicate to WebUI

    path = __file__
    if path.startswith(os.path.sep):
        return path

    dirname = os.path.dirname(path)
    for sys_path in sys.path:
        if sys_path.endswith(dirname):
            return sys_path
    return dirname

def verify_rules_file(rule_file_path, sigma_config, sigma_backend):
    """Verifies a given file path contains a valid sigma rule.

        Args:
            rule_file_path: the path to the rules.
            sigma_config: config to use
            sigma_backend: A sigma.backends instance

        Raises:
            None

        Returns:
            true: rule_file_path contains a valid sigma rule
            false: rule_file_path does not contain a valid sigma rule
    """

    logger.debug('[sigma] Reading rules from {0:s}'.format(
        rule_file_path))

    if os.path.isfile(rule_file_path) == False:
        logger.error('Rule file not found')
        return False

    path, rule_filename = os.path.split(rule_file_path)

    with codecs.open(rule_file_path, 'r', encoding='utf-8') as rule_file:
        try:
            rule_file_content = rule_file.read()
            parser = sigma_collection.SigmaCollectionParser(
                rule_file_content, sigma_config, None)
            parsed_sigma_rules = parser.generate(sigma_backend)
        except NotImplementedError:
            logger.error('{0:s} Error with file {1:s}'
            .format(rule_filename, rule_file_path), exc_info=True)
            return False
        except (sigma.parser.exceptions.SigmaParseError, TypeError):
            logger.error(
                '{0:s} Error with file {1:s} '
                'you should not use this rule in Timesketch '
                .format(rule_filename, rule_file_path), exc_info=True)
            return False

    return True


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

    sigma_config_path = config_file_path

    with open(sigma_config_path, 'r') as sigma_config_file:
        sigma_config_con = sigma_config_file.read()
    sigma_config = sigma_configuration.SigmaConfiguration(sigma_config_con)
    sigma_backend = sigma_elasticsearch.\
        ElasticsearchQuerystringBackend(sigma_config, {})
    return_verified_rules = []
    return_rules_with_problems = []

    for dirpath, dirnames, files in os.walk(rules_path):

        if 'deprecated' in [x.lower for x in dirnames]:
            dirnames.remove('deprecated')
            logger.info('deprecated in folder / filename found - ignored')

        for rule_filename in files:
            if not rule_filename.lower().endswith(RULE_EXTENSIONS):
                continue

            # If a sub dir is found, skip it
            if os.path.isdir(os.path.join(rules_path, rule_filename)):
                logger.debug(
                    'Directory found, skipping: {0:s}'.format(rule_filename))
                continue

            rule_file_path = os.path.join(dirpath, rule_filename)
            rule_file_path = os.path.abspath(rule_file_path)

            if verify_rules_file(rule_file_path, sigma_config, sigma_backend):
                return_verified_rules.append(rule_file_path)
            else:
                logger.info('File did not work{0:s}'.format(rule_file_path))
                return_rules_with_problems.append(rule_file_path)

    return return_verified_rules, return_rules_with_problems


if __name__ == '__main__':
    code_path = get_codepath()
    # We want to ensure our mocked libraries get loaded first.
    sys.path.insert(0, code_path)

    description = (
        'Mock an sigma analyzer run. This tool is intended for developers '
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
            print(badrule)

    if len(sigma_verified_rules) > 0:
        logging.info('### You can import the following rules ###')
        for goodrule in sigma_verified_rules:
            logging.info(goodrule)
