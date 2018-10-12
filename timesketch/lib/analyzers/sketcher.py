# Copyright 2017 Google Inc. All rights reserved.
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

from __future__ import unicode_literals

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class Sketcher(interface.BaseAnalyzer):

    NAME = 'Sketcher'
    IS_SKETCH_ANALYZER = True

    def __init__(self, sketch_id, index_name):
        self.sketch_id = sketch_id
        self.index_name = index_name
        super(Sketcher, self).__init__(sketch_id=sketch_id)

    def run(self):
        self.sketch.add_view(name='Auto view', query_string='*')
        return 'Sketch updated ({0:s})'.format(self.sketch.sql_sketch.name)


manager.AnalysisManager.register_analyzer(Sketcher)
