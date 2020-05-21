#!/bin/sh
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

# This script watches a directory for new files and executes the importer
# on any .plaso, .mans, .csv and .jsonl files. To be place in /usr/local/bin/

config_file="/etc/timesketch-importer.conf"
if [ -s "$config_file" ]; then
  . "$config_file"
else
  echo "config file not found, aborting."
  exit 1
fi

inotifywait -m $IMPORT_DIR -e close_write | while read -r path action file; do
  tsctl import -f $path$file
done
