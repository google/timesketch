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
"""Timesketch data import configuration."""
from __future__ import unicode_literals

import codecs
import logging
import os

import yaml


logger = logging.getLogger('timesketch_importer.config_loader')

DEFAULT_FILE = 'formatter.yaml'


def load_config(file_path=''):
    """Loads YAML config and returns a list of dict with the results.

    Args:
        file_path (str): path to the YAML config file. This is optional
            and if not defined the default formatter.yaml file will be
            used that comes with the tool.

    Returns:
        dict: a dict with the key being a config file identifier and the value
        being another dict with the configuration items.
    """
    if not file_path:
        base_path = os.path.dirname(__file__)
        file_path = os.path.join(base_path, DEFAULT_FILE)

    if not file_path.endswith('.yaml'):
        logger.error('Can\'t load a config that is not a YAML file.')
        return {}

    if not os.path.isfile(file_path):
        logger.error('File path does not exist, unable to load YAML config.')
        return {}

    with codecs.open(file_path, 'r') as fh:
        try:
            data = yaml.safe_load(fh)
            return data
        except (AttributeError, yaml.parser.ParserError) as e:
            logger.error('Unable to parse YAML file, with error: %s', e)
            return {}

    return {}
