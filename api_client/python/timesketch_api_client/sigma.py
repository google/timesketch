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
"""Timesketch API client library."""
from __future__ import unicode_literals

import json
import logging

from . import error
from . import index
from . import resource
import pandas

logger = logging.getLogger('timesketch_api.sigma')


class Sigma(resource.BaseResource):

    def __init__(self, rule_uuid, api ):
        """Initializes the Sigma object.

        Args:
            searchindex_id: Primary key ID of the searchindex.
            searchindex_name: Name of the searchindex (optional).
        """
        self.rule_uuid = rule_uuid
        self._resource_uri = 'sigma/{0:s}'.format(self.rule_uuid)
        super(Sigma, self).__init__(
            api=api, resource_uri=self._resource_uri)

    @property
    def description(self):
        """Returns the object dict from the resources dict."""
        data = self.lazyload_data()

        return data

    # TODO the below is not working yet
    def to_pandas(self):
        """Returns a pandas DataFrame."""
        panda_list = []
        data = self.lazyload_data()
        #panda_list = pandas.DataFrame(data)
        #for entry in data.get('objects', []):
            #for bucket in self._get_aggregation_buckets(entry):
        #    panda_list.append(entry)
        
        #dates = pandas.date_range('20130101', periods=6)
        return pandas.DataFrame(data)
        #return False
        #return pandas.DataFrame(panda_list)