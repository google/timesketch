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
"""Timesketch Sigma lib functions.
"""

import os

import sigma.configuration as sigma_configuration

from sigma.backends import elasticsearch as sigma_elasticsearch
from sigma.parser import collection as sigma_collection

from flask import current_app


def get_sigma_config_file():
    """Get a sigma.configuration.SigmaConfiguration object.
        
        Args:
            None

        Returns:
            A sigma.configuration.SigmaConfiguration object
    """
    _CONFIG_FILE = current_app.config.get('SIGMA_CONFIG')

    if not _CONFIG_FILE:
        raise ValueError(
            'SIGMA_CONFIG not found in config file')

    if not os.path.isfile(_CONFIG_FILE):
        raise ValueError(
            'Unable to open file: [{0:s}], it does not exist.'.format(
            _CONFIG_FILE))

    if not os.access(_CONFIG_FILE, os.R_OK):
        raise ValueError(
            'Unable to open file: [{0:s}], cannot open it for '
            'read, please check permissions.'.format(_CONFIG_FILE))

    with open(_CONFIG_FILE, 'r') as config_file:
        sigma_config_file = config_file.read()

    sigma_config = sigma_configuration.SigmaConfiguration(sigma_config_file)

    return sigma_config

def get_sigma_rules_path():

    _RULES_PATH = current_app.config.get('SIGMA_RULES_FOLDER')

    if not _RULES_PATH:
        raise ValueError(
            'SIGMA_RULES_FOLDER not found in config file')

    if not os.path.isdir(_RULES_PATH):
        raise ValueError(
            'Unable to open dir: [{0:s}], it does not exist.'.format(
            _RULES_PATH))

    if not os.access(_RULES_PATH, os.R_OK):
        raise ValueError(
            'Unable to open dir: [{0:s}], cannot open it for '
            'read, please check permissions.'.format(_RULES_PATH))
    
    return _RULES_PATH
