# Copyright 2023 Google Inc. All rights reserved.
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
"""This file contains an interface to feature extraction plugins."""

import abc
from typing import Optional


class BaseFeatureExtractionPlugin(object):
    """A base plugin for feature extraction.

    This class serves as an interface for feature extraction plugins.
    """

    NAME = "base_feature_extraction"
    DISPLAY_NAME = "Base Feature Extraction"
    DESCRIPTION = ""

    def __init__(self, analyzer_object: Optional["FeatureSketchPlugin"] = None) -> None:
        """Initializes the base plugin.

        Args:
            analyzer_object (FeatureSketchPlugin): An object of class
                FeatureSketchPlugin.
        """
        super().__init__()
        self.analyzer_object = analyzer_object

    @abc.abstractmethod
    def run_plugin(self, name: str, config: dict) -> str:
        """Main entry point to feature extraction plugins.

        This method should be implemented by subclasses to perform feature extraction.

        Args:
            name (str): The name of the feature to extract.
            config (dict): Configuration parameters for the feature extraction.

        Returns:
            str: A summary of the feature extraction results.
        """
        raise NotImplementedError("Subclass must implement the run_plugin() method")
