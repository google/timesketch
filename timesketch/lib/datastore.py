# Copyright 2015 Google Inc. All rights reserved.
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
"""Datastore abstraction."""

import abc


class DataStore(object):
    """Abstract datastore."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def search(self, sketch_id, query, query_filter, indices):
        """Return search results"""

    @abc.abstractmethod
    def get_event(self, searchindex_id, event_id):
        """Get single document from the datastore"""

    @abc.abstractmethod
    def set_label(self, searchindex_id, event_id, sketch_id, user_id, label,
                  toggle=False):
        """Add label to an event."""
