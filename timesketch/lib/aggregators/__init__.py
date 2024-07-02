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
"""Aggregator module."""

# Register all aggregators here by importing them.
from timesketch.lib.aggregators import apex
from timesketch.lib.aggregators import bucket
from timesketch.lib.aggregators import date_histogram
from timesketch.lib.aggregators import feed
from timesketch.lib.aggregators import summary
from timesketch.lib.aggregators import term
from timesketch.lib.aggregators import vega
