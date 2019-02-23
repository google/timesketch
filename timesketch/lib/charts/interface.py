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


class BaseChart(object):

    NAME = 'name'

    def __init__(self, data):
        self.name = self.NAME
        self.encoding = data['encoding']
        self.values = alt.Data(values=data['values'])

    def generate(self):
        raise NotImplementedError
