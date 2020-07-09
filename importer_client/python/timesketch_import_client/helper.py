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
"""Timesketch data importer."""
from __future__ import unicode_literals

import logging
import os

from timesketch_import_client import data as data_config


logger = logging.getLogger('timesketch_importer.ts_import_helper')


class ImportHelper:
    """Import helper class."""

    def __init__(self, load_default=True):
        """Initialize the helper class."""
        if load_default:
            self._data = data_config.load_config()
        else:
            self._data = {}

    def _configure_streamer(self, streamer, config_dict):
        """Sets up the streamer based on a configuration dict.

        Args:
            streamer (ImportStreamer): an import streamer object.
            config_dict (dict): A dictionary that contains
                configuration details for the streamer.
        """
        message = config_dict.get('message')
        if message:
            streamer.set_message_format_string(message)

        timestamp_desc = config_dict.get('timestamp_desc')
        if timestamp_desc:
            streamer.set_timestamp_description(timestamp_desc)

        separator = config_dict.get('separator')
        if separator:
            streamer.set_csv_delimiter(separator)

        encoding = config_dict.get('encoding')
        if encoding:
            streamer.set_text_encoding(encoding)

        datetime_string = config_dict.get('datetime')
        if datetime_string:
            streamer.set_datetime_column(datetime_string)

    def add_config(self, file_path):
        """Loads a YAML config file describing the log file config.

        This function reads a YAML config file, and adds the config
        to it's config data. This configuration can then be used to
        setup an import streamer object.

        Args:
            file_path (str): the path to the config file.

        Raises:
            ValueError: if the file path does not exist or if the config
                        is not valid or cannot be read.
        """
        if not os.path.isfile(file_path):
            raise ValueError(
                'Unable to open file: [{0:s}], it does not exist.'.format(
                    file_path))

        if not os.access(file_path, os.R_OK):
            raise ValueError(
                'Unable to open file: [{0:s}], cannot open it for '
                'read, please check permissions.'.format(file_path))


        config = data_config.load_config(file_path)
        if not isinstance(config, dict):
            raise ValueError(
                'Unable to read config file since it does not produce a dict')

        if not all([isinstance(x, dict) for x in config.values()]):
            raise ValueError(
                'The config needs to a dict that contains other dict '
                'attributes.')

        self._data.update(config)

    def add_config_dict(self, config, config_name='manual'):
        """Add a config dict describing the log file config.

        Args:
            config (dict): a single dict with the config needed for setting
                up the streamer.
            config_name (str): the name of the config to be added. This is
                optional, with the default value set to "manual".
        """
        self._data[config_name] = config

    def configure_streamer(self, streamer, data_type='', columns=None):
        """Go through loaded config and setup a streamer if there is a match.

        This function takes a streamer object and compares the loaded config
        to see if there is a match to the data_type and/or columns that are
        supplied to the function and sets the streamer up if a matching
        config is discovered.

        The helper will use the first match in the config to setup the
        streamer (it will exit as soon as it finds a match).

        Args:
            streamer (ImportStreamer): an import streamer object.
            data_type (str): optional data type that is used for matching
                with the loaded config.
            columns (List[str]): optional list of strings with column names.
        """
        for config_name, config in self._data.items():
            conf_data_type = config.get('data_type')
            if data_type and conf_data_type and conf_data_type == data_type:
                logger.info('Using config %s for streamer.', config_name)
                self._configure_streamer(streamer, config)
                return

            if not columns:
                continue

            column_set = set(columns)
            column_string = config.get('columns', '')
            column_subset_string = config.get('columns_subset', '')
            if not any([column_string, column_subset_string]):
                continue

            conf_columns = set(column_string.split(','))
            if conf_columns and column_set == conf_columns:
                logger.info('Using config %s for streamer.', config_name)
                self._configure_streamer(streamer, config)
                return

            columns_subset = set(column_subset_string.split(','))
            if columns_subset and columns_subset.issubset(column_set):
                logger.info('Using config %s for streamer.', config_name)
                self._configure_streamer(streamer, config)
                return
