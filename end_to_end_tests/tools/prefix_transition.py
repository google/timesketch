# Copyright 2026 Google Inc. All rights reserved.
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
"""One phase of the end-to-end prefix transition test.

Run this in the Timesketch container after each configuration change. The
container restart retains the state file and the database and datastore data.
"""

import io
import json
import os
from pathlib import Path
import socket
import sys
import time

from timesketch_api_client import client as api_client
from timesketch_api_client import timeline as timeline_client
from timesketch.lib import index_name as index_name_lib

PREFIXES = ("", "timesketch-test-", "timesketch_")
STATE_FILE = Path("/tmp/timesketch_prefix_transition.json")
SERVER = os.environ.get("TIMESKETCH_SERVER_URL", "http://127.0.0.1")


def wait_for_server():
    """Wait for Gunicorn after the configuration change and restart."""
    for _ in range(60):
        try:
            with socket.create_connection(("127.0.0.1", 80), timeout=2):
                return
        except OSError:
            time.sleep(2)
    raise TimeoutError("Timesketch did not restart within two minutes")


def upload(api, sketch, phase, role, index_name=None):
    """Upload one event and return the actual index name used by the worker."""
    message = f"prefix transition {phase} {role}"
    event = {
        "message": message,
        "timestamp": "1725148800000000",
        "datetime": "2024-09-01T00:00:00+00:00",
        "timestamp_desc": "Event time",
        "data_type": "prefix:transition",
    }
    payload = (json.dumps(event) + "\n").encode("utf-8")
    data = {
        "sketch_id": str(sketch.id),
        "name": message,
        "total_file_size": str(len(payload)),
    }
    if index_name:
        data["index_name"] = index_name
    response = api.session.post(
        f"{api.api_root}/upload/",
        data=data,
        files={"file": (f"phase-{phase}-{role}.jsonl", io.BytesIO(payload))},
        timeout=120,
    )
    response.raise_for_status()
    timeline_id = response.json()["objects"][0]["id"]
    timeline = timeline_client.Timeline(timeline_id, sketch.id, api)
    for _ in range(120):
        if timeline.status == "ready" and timeline.index.status == "ready":
            return timeline.index_name, message
        time.sleep(2)
    raise TimeoutError(f"Timeline {timeline_id} did not become ready")


def messages_in(sketch):
    """Return messages from every timeline in the sketch."""
    for _ in range(30):
        events = sketch.explore("*", as_pandas=True, max_entries=100)
        if "message" in events:
            yield set(events["message"])
        time.sleep(2)


def run(phase):
    """Create new data under this phase's prefix and read all prior data."""
    wait_for_server()
    api = api_client.TimesketchApi(host_uri=SERVER, username="test", password="test")
    prefix = PREFIXES[phase]
    if phase:
        state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        persistent = api.get_sketch(state["persistent_sketch"])
    else:
        state = {"persistent_sketch": None, "indices": [], "messages": []}
        persistent = None

    new_sketch = api.create_sketch(name=f"prefix transition phase {phase}")
    if persistent is None:
        persistent = new_sketch
        state["persistent_sketch"] = persistent.id

    new_index, new_message = upload(api, new_sketch, phase, "new sketch")
    assert index_name_lib.is_canonical_index_name(new_index, prefix)
    if persistent.id == new_sketch.id:
        persistent_index, persistent_message = new_index, new_message
    else:
        new_sketch.add_event(
            f"new sketch manual {phase}", "2024-09-01T00:00:00Z", "Event time"
        )
        new_manual = next(
            timeline.index_name
            for timeline in new_sketch.list_timelines()
            if timeline.name == "Manual events"
        )
        assert index_name_lib.is_canonical_index_name(new_manual, prefix)
        persistent_index, persistent_message = upload(
            api, persistent, phase, "existing sketch"
        )
    assert index_name_lib.is_canonical_index_name(persistent_index, prefix)
    assert persistent_index not in state["indices"]
    state["indices"].append(persistent_index)
    state["messages"].append(persistent_message)

    if phase == 2:
        for old_index in state["indices"][:-1]:
            used_index, message = upload(
                api, persistent, phase, f"append {old_index}", index_name=old_index
            )
            assert used_index == old_index
            state["messages"].append(message)

    manual_message = f"prefix transition manual {phase}"
    persistent.add_event(manual_message, "2024-09-01T00:00:00Z", "Event time")
    state["messages"].append(manual_message)

    timelines = persistent.list_timelines()
    stored_indices = {timeline.index_name for timeline in timelines}
    assert set(state["indices"]).issubset(stored_indices)
    manual_indices = [
        timeline.index_name
        for timeline in timelines
        if timeline.name == "Manual events"
    ]
    assert len(manual_indices) == 1
    if phase == 0:
        state["manual_index"] = manual_indices[0]
    assert manual_indices[0] == state["manual_index"]

    for seen_messages in messages_in(persistent):
        if set(state["messages"]).issubset(seen_messages):
            break
    else:
        raise AssertionError(f"Missing prior events after prefix phase {phase}")

    STATE_FILE.write_text(json.dumps(state), encoding="utf-8")
    print(f"Phase {phase} passed: {state['indices']}")


if __name__ == "__main__":
    run(int(sys.argv[1]))
