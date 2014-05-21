# Copyright 2014 Google Inc. All rights reserved.
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
"""This is the main datastore abstraction."""

import abc

class DataStore(object):
    """Abstract datastore access."""

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod 
    def search(self, sketch, query, filters):
        """Return search results"""

    @abc.abstractmethod 
    def get_single_event(self, event_id):
        """Get singel document from the datastore"""

    @abc.abstractmethod 
    def add_label_to_event(self, event, sketch, user, label, toggle=False):
        """Add label to an event."""
