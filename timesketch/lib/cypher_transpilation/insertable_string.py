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
"""Module containing the InsertableString class."""


class InsertableString(object):
    """Class that accumulates insert and replace operations for a string and
    later performs them all at once so that positions in the original string
    can be used in all of the operations.
    """
    def __init__(self, input_string):
        self.input_string = input_string
        self.to_insert = []

    def insert_at(self, pos, s):
        """Add an insert operation at given position."""
        self.to_insert.append((pos, pos, s))

    def replace_range(self, start, end, s):
        """Add a replace operation for given range. Assume that all
        replace_range operations are disjoint, otherwise undefined behavior.
        """
        self.to_insert.append((start, end, s))

    def apply_insertions(self):
        """Return a string obtained by performing all accumulated operations."""
        to_insert = reversed(sorted(self.to_insert))
        result = self.input_string
        for start, end, s in to_insert:
            result = result[:start] + s + result[end:]
        return result
