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
It also does not require you to have a full blown Timesketch instance up and running.
Example way of running the tool:
  $ sigma_verify_rules.py --config_file ../data/sigma_config.yaml ../data/linux/
"""


import logging
import os
import argparse
import sys
import codecs

import sigma.parser.exceptions



from sigma.backends import elasticsearch as sigma_elasticsearch
import sigma.configuration as sigma_configuration
from sigma.parser import collection as sigma_collection
logging.basicConfig(level=os.environ.get('LOGLEVEL', 'ERROR'))


def get_codepath():
    """Return the absolute path to where the tool is run from."""
    path = __file__
    if path.startswith(os.path.sep):
        return path

    dirname = os.path.dirname(path)
    for sys_path in sys.path:
        if sys_path.endswith(dirname):
            return sys_path
    return dirname


def run_verifier(rules_path, config_file_path):
    """Run an sigma parsing test on a given dir and returns results from the run.

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
    sigma_backend = sigma_elasticsearch.ElasticsearchQuerystringBackend(sigma_config, {})
    sigma_verified_rules = []
    sigma_rules_with_problems = []

    for dirpath, dirnames, files in os.walk(rules_path):

        if 'deprecated' in dirnames:
            dirnames.remove('deprecated')

        rule_extensions = ("yml","yaml")

        for rule_filename in files:
            if rule_filename.lower().endswith(rule_extensions):

                # if a sub dir is found, append it to be scanned for rules
                if os.path.isdir(os.path.join(rules_path, rule_filename)):
                    logging.debug(
                        'This is a directory, skipping: {0:s}'.format(
                            rule_filename))
                    continue

                tag_name, _, _ = rule_filename.rpartition('.')
                rule_file_path = os.path.join(dirpath, rule_filename)
                rule_file_path = os.path.abspath(rule_file_path)
                logging.debug('[sigma] Reading rules from {0:s}'.format(
                    rule_file_path))
                with codecs.open(rule_file_path, 'r',
                    encoding="utf-8") as rule_file:
                    try:
                        rule_file_content = rule_file.read()
                        parser = sigma_collection.SigmaCollectionParser(
                            rule_file_content, sigma_config, None)
                        parsed_sigma_rules = parser.generate(sigma_backend)
                    except (NotImplementedError) as exception:
                        logging.error(
                            '{0:s} Error NotImplementedError generating rule in file {1:s}: {2!s}'
                                .format(rule_filename,rule_file_path, exception))

                        sigma_rules_with_problems.append(rule_file_path)
                        continue
                    except (sigma.parser.exceptions.SigmaParseError, TypeError) as exception:
                        logging.error(
                            '{0:s} Error generating rule in file {1:s} '
                            'you should not use this rule in Timesketch: {2!s}'
                                .format(rule_filename,rule_file_path, exception))
                        sigma_rules_with_problems.append(rule_file_path)
                        continue
                    sigma_verified_rules.append(rule_file_path)
    return sigma_verified_rules,sigma_rules_with_problems


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

    try:
        options = arguments.parse_args()
    except UnicodeEncodeError:
        print(arguments.format_help())
        sys.exit(1)

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

    print('### You should NOT import the following rules ###')
    for badrule in sigma_rules_with_problems:
        print(badrule)

    print('### You can import the following rules ###')
    for goodrule in sigma_verified_rules:
        print(goodrule)

