# Copyright 2018 Google Inc. All rights reserved.
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
"""Analyzer module."""

# Register all analyzers here by importing them.
from timesketch.lib.analyzers import account_finder
from timesketch.lib.analyzers import browser_search
from timesketch.lib.analyzers import browser_timeframe
from timesketch.lib.analyzers import chain
from timesketch.lib.analyzers import domain
from timesketch.lib.analyzers import expert_sessionizers
from timesketch.lib.analyzers import feature_extraction
from timesketch.lib.analyzers import gcp_logging
from timesketch.lib.analyzers import geoip
from timesketch.lib.analyzers import hashr_lookup
from timesketch.lib.analyzers import login
from timesketch.lib.analyzers import phishy_domains
from timesketch.lib.analyzers import safebrowsing
from timesketch.lib.analyzers import sessionizer
from timesketch.lib.analyzers import sigma_tagger
from timesketch.lib.analyzers import similarity_scorer
from timesketch.lib.analyzers import ssh_sessionizer
from timesketch.lib.analyzers import gcp_servicekey
from timesketch.lib.analyzers import ntfs_timestomp
from timesketch.lib.analyzers import yetiindicators
from timesketch.lib.analyzers import win_crash
from timesketch.lib.analyzers import win_evtxgap
from timesketch.lib.analyzers import tagger

import timesketch.lib.analyzers.authentication
import timesketch.lib.analyzers.contrib
