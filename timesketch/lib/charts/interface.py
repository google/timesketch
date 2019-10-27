# Copyright 2019 Google Inc. All rights reserved.
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
"""Interface for charts."""

from __future__ import unicode_literals

import altair as alt
import pandas as pd


class BaseChart(object):
    """Base class for a chart."""

    # Name that the chart will be registered as.
    NAME = 'name'

    def __init__(self, data):
        """Initialize the chart object.

        Args:
            data: Dictionary with list of values and dict of encoding info.

        Raises:
            RuntimeError if values or encoding is missing from data.
        """
        _values = data.get('values')
        _encoding = data.get('encoding')

        if _values is None or not _encoding:
            raise RuntimeError('Values and/or Encoding missing from data')

        self.name = self.NAME
        if isinstance(_values, pd.DataFrame):
            self.values = _values
        else:
            self.values = alt.Data(values=_values)
        self.encoding = _encoding

    def generate(self):
        """Entry point for the chart."""
        raise NotImplementedError
