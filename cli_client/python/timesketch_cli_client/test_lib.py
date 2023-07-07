# Copyright 2021 Google Inc. All rights reserved.
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
"""Test utilities."""

import tempfile

from timesketch_api_client import client

from .cli import TimesketchCli


TEST_CONFIG = """
[timesketch]
host_uri = http://127.0.0.1
username = foobar
auth_mode = oauth
client_id = myidfoo
client_secret = sdfa@$FAsASDF132
verify = True

[cli]
sketch = 1
output_format = tabular
"""


def get_cli_context():
    """Return a CLI context object using a mock config."""
    api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")
    with tempfile.NamedTemporaryFile(mode="w") as fw:
        fw.write(TEST_CONFIG)
        fw.seek(0)
        return TimesketchCli(
            api_client=api_client, sketch_from_flag=1, conf_file=fw.name
        )


TEST_CONFIG_NO_OUTPUT_FORMAT = """
[timesketch]
host_uri = http://127.0.0.1
username = foobar
auth_mode = oauth
client_id = myidfoo
client_secret = sdfa@$FAsASDF132
verify = True

[cli]
sketch = 1
#output_format = tabular
"""


def get_cli_context_no_output():
    api_client = client.TimesketchApi("http://127.0.0.1", "test", "test")
    with tempfile.NamedTemporaryFile(mode="w") as fw:
        fw.write(TEST_CONFIG_NO_OUTPUT_FORMAT)
        fw.seek(0)
        return TimesketchCli(
            api_client=api_client, sketch_from_flag=1, conf_file=fw.name
        )
