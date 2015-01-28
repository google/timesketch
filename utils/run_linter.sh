#!/bin/bash
# A small script that runs the linter on all files.
#
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

find . -name "*.py" | xargs pylint --rcfile utils/pylintrc;

if test $? -ne 0; then
    echo "[ERROR] Fix the issues reported by the linter";
    exit 1
else
    echo "[OK] The codebase passes the linter tests!";
fi
