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
"""A simple frontend to the Timesketch data importer."""

from __future__ import unicode_literals

import argparse
import getpass
import logging
import os
import sys
import time

from typing import Dict
import json
import zlib
import threading
import queue
import signal

from watchdog.observers.polling import PollingObserverVFS
from watchdog.events import (
    DirCreatedEvent,
    FileCreatedEvent,
    DirModifiedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)

from timesketch_api_client import cli_input
from timesketch_api_client import credentials as ts_credentials
from timesketch_api_client import crypto
from timesketch_api_client import config, client
from timesketch_api_client import sketch
from timesketch_api_client import version as api_version
from timesketch_import_client import helper
from timesketch_import_client import importer
from timesketch_import_client import version as importer_version

logger = logging.getLogger("timesketch_importer.importer_frontend")


def configure_logger_debug():
    """Configure the logger to log debug logs."""
    logging.basicConfig()
    logger.setLevel(logging.DEBUG)
    logger_formatter = logging.Formatter(
        "[%(asctime)s] %(name)s/%(levelname)s %(message)s <%(module)s/%(funcName)s>"
    )
    for handler in logger.parent.handlers:
        handler.setFormatter(logger_formatter)


def configure_logger_default():
    """Configure the logger to only log information and above logs."""
    logging.basicConfig()
    logger.setLevel(logging.INFO)
    logger_formatter = logging.Formatter(
        "[%(asctime)s] %(name)s/%(levelname)s %(message)s"
    )
    for handler in logger.parent.handlers:
        handler.setFormatter(logger_formatter)


def get_name_by_path(path: str, n: int) -> str:
    """Return a name based on the provided path."""
    name = os.path.normpath(path).split(os.sep)[n]
    return name


def get_sketch_by_opts(
    sketch_id: int,
    sketch_name: str,
    sketch_name_path_pos: int,
    file_path: str,
    ts_client,
) -> sketch.Sketch:
    """Get or create a sketch based on the provided options.

    Args:
        sketch_id (int): The sketch ID to retrieve.
        sketch_name (str): The sketch name to retrieve or create.
        sketch_name_path_pos (int): If not -1, use the n-th folder in the file path as sketch name.
        file_path (str): The file path being processed (used if sketch_name_path_pos is set).
        ts_client: An instance of timesketch_api_client.TimesketchApi (or similar).
    Returns:
        A sketch object.
    """
    if sketch_id:
        my_sketch = ts_client.get_sketch(sketch_id)
    else:
        if sketch_name_path_pos != -1:
            sketch_name = get_name_by_path(file_path, sketch_name_path_pos)
        else:
            sketch_name = sketch_name or "New Sketch From Importer CLI"
        try:
            # check if the sketch name already exists
            my_sketch = get_sketch_by_name(ts_client, sketch_name)
            logger.info(
                "Using existing sketch: [{0:d}] {1:s}".format(
                    my_sketch.id, my_sketch.name
                )
            )
        except KeyError:
            # create a new sketch
            my_sketch = ts_client.create_sketch(sketch_name)
            logger.info(
                "New sketch created: [{0:d}] {1:s}".format(my_sketch.id, my_sketch.name)
            )

    return my_sketch


def get_timeline_name_by_opts(
    timeline_name: str, timeline_name_path_pos: int, file_path: str
) -> str:
    """Get timeline name based on provided options.
    Args:
        timeline_name (str): The timeline name to use.
        timeline_name_path_pos (int): If not -1, use the n-th folder in the file path as timeline name.
        file_path (str): The file path being processed (used if timeline_name_path_pos is set).
    Returns:
        A timeline name string.
    """
    filename = os.path.basename(file_path)
    default_timeline_name, _, _ = filename.rpartition(".")

    if timeline_name:
        return timeline_name
    elif timeline_name_path_pos != -1:
        return get_name_by_path(file_path, timeline_name_path_pos)
    else:
        return cli_input.ask_question(
            "What is the timeline name", input_type=str, default=default_timeline_name
        )


def get_sketch_by_name(
    ts_client: client.TimesketchApi, sketch_name: str
) -> sketch.Sketch:
    """Gets a sketch by its name.
    Args:
        ts_client: An instance of timesketch_api_client.TimesketchApi (or similar).
        sketch_name: The name of the sketch to find.
    Raises:
        KeyError: If a sketch with the given name is not found.
    Returns:
        A sketch object.
    """
    sketches = ts_client.list_sketches()  # may return Sketch objects or dicts
    for s in sketches:
        # Sketch object
        if hasattr(s, "name") and s.name.lower() == sketch_name.lower():
            return s
        # dict representation
        if isinstance(s, dict) and s.get("name", "").lower() == sketch_name.lower():
            sketch_id = s.get("id")
            if sketch_id and hasattr(ts_client, "get_sketch"):
                return ts_client.get_sketch(sketch_id)
            return s
    raise KeyError(f"Sketch named {sketch_name!s} not found")


def upload_file(
    my_sketch: sketch.Sketch, config_dict: Dict[str, any], file_path: str
) -> str:
    """Uploads a file to Timesketch.

    Args:
        my_sketch (sketch.Sketch): a sketch object to point to the sketch the
            data will be imported to.
        config_dict (dict): dict with settings for the importer.
        file_path (str): the path to the file to upload.

    Returns:
        A tuple with the timeline object (timeline.Timeline) or None if not
        able to upload the timeline as well as the celery task identification
        for the indexing.
    """

    if not my_sketch or not hasattr(my_sketch, "id"):
        return "Sketch needs to be set"

    _, _, file_extension = file_path.rpartition(".")
    if file_extension.lower() not in ("plaso", "csv", "jsonl"):
        return (
            "File needs to have one of the following extensions: "
            ".plaso, .csv, "
            ".jsonl (not {0:s})"
        ).format(file_extension.lower())

    if os.path.getsize(file_path) <= 0:
        return "File cannot be empty"
    import_helper = helper.ImportHelper()
    import_helper.add_config_dict(config_dict)

    log_config_file = config_dict.get("log_config_file", "")
    if log_config_file:
        import_helper.add_config(log_config_file)

    timeline = None
    task_id = ""
    logger.info("About to upload file.")
    with importer.ImportStreamer() as streamer:
        streamer.set_sketch(my_sketch)
        streamer.set_config_helper(import_helper)
        streamer.set_provider("CLI importer tool")

        format_string = config_dict.get("message_format_string")
        if format_string:
            streamer.set_message_format_string(format_string)

        timeline_name = config_dict.get("timeline_name")
        if timeline_name:
            streamer.set_timeline_name(timeline_name)

        index_name = config_dict.get("index_name")
        if index_name:
            streamer.set_index_name(index_name)

        time_desc = config_dict.get("timestamp_description")
        if time_desc:
            streamer.set_timestamp_description(time_desc)

        entry_threshold = config_dict.get("entry_threshold")
        if entry_threshold:
            streamer.set_entry_threshold(entry_threshold)

        size_threshold = config_dict.get("size_threshold")
        if size_threshold:
            streamer.set_filesize_threshold(size_threshold)

        data_label = config_dict.get("data_label")
        if data_label:
            streamer.set_data_label(data_label)

        context = config_dict.get("context")
        if context:
            streamer.set_upload_context(context)

        max_payload = config_dict.get("max_payload_size")
        if max_payload:
            streamer.set_max_payload_size(max_payload)

        plaso_filter = config_dict.get("plaso_event_filter")
        if plaso_filter:
            streamer.set_plaso_event_filter(plaso_filter)

        streamer.add_file(file_path)

        timeline = streamer.timeline
        task_id = streamer.celery_task_id

    logger.info("File upload completed.")
    return timeline, task_id


class _WatchdogEventHandler(FileSystemEventHandler):
    def __init__(self, monitor):
        super().__init__()
        self.monitor = monitor

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if not event.is_directory:
            self.monitor.enqueue(event.src_path)

    def on_modified(self, event: DirModifiedEvent | FileModifiedEvent) -> None:
        if not event.is_directory:
            self.monitor.enqueue(event.src_path)


class WatchdogDirectoryMonitor:
    """PollingObserver-based monitor for .jsonl files that tracks per-file state.

    - Uses watchdog.observers.polling.PollingObserver (platform-independent polling).
    - Tracks: sha256 of first N bytes, last processed line, mtime.
    - Persists state to a JSON file on stop and loads it on start.
    - process_file(file_path, start_line=0) must return last_processed_line (int).
    """

    FIRST_BYTES = 200  # needs to be low, as otherwise small files may have issues.

    def __init__(
        self,
        directory_path,
        ts_client,
        config_dict: dict,
        state_file,
        poll_interval: int = 1,
    ):
        self.directory_path = os.path.abspath(directory_path)
        self.poll_interval = poll_interval
        self._observer = PollingObserverVFS(
            stat=os.stat, listdir=os.scandir, polling_interval=self.poll_interval
        )
        self._handler = _WatchdogEventHandler(self)
        self._observer.schedule(self._handler, self.directory_path, recursive=True)
        self._q = queue.Queue()
        self._lock = threading.Lock()
        self._worker = None
        self._stop_event = threading.Event()
        self._ts_client = ts_client
        self._config_dict = config_dict
        self.state_file = state_file
        # state: { "<abs_path>": {"hash": "<hex>", "last_line": int, "mtime": float} }
        self.state = {}
        self._load_state()

        # install signal handlers to persist state on termination
        try:
            signal.signal(signal.SIGTERM, self._signal_stop)
            signal.signal(signal.SIGINT, self._signal_stop)
        except Exception:
            # not all platforms allow signal registration (e.g. Windows threading edge-cases)
            pass

    def _signal_stop(self, signum, frame):
        self.stop_monitoring()

    def _hash_first_bytes(self, path, nbytes=FIRST_BYTES):
        try:
            with open(path, "rb") as fh:
                data = fh.read(nbytes)
            return zlib.crc32(
                data
            )  # faster than hashlib, we don't care about collisions
        except Exception:
            return None

    def _load_state(self):
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as fh:
                    self.state = json.load(fh)
        except Exception:
            logger.debug("Could not load monitor state, starting fresh.", exc_info=True)
            self.state = {}

    def _save_state(self):
        try:
            tmp = self.state_file + ".tmp"
            with open(tmp, "w") as fh:
                json.dump(self.state, fh, indent=2)
            os.replace(tmp, self.state_file)
        except Exception:
            logger.error("Failed to save monitor state.", exc_info=True)

    def enqueue(self, path):
        """Queue a file path for processing (called from event handler)."""
        if not path.lower().endswith(".jsonl") and not path.lower().endswith(".csv"):
            return
        abs_path = os.path.abspath(path)
        try:
            self._q.put_nowait(abs_path)
        except queue.Full:
            pass

    def _initial_scan(self):
        """Enqueue existing files at startup so they get processed once."""
        for root, _, files in os.walk(self.directory_path):
            for fname in files:
                if fname.lower().endswith(".jsonl") or fname.lower().endswith(".csv"):
                    self.enqueue(os.path.join(root, fname))

    def _worker_loop(self):
        """Worker thread that processes queued paths."""
        while not self._stop_event.is_set():
            try:
                path = self._q.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                self._process_path(path)
            except Exception:
                logger.exception("Error processing path: %s", path)
            finally:
                self._q.task_done()

    def _process_path(self, path):
        """Check state and call process_file with appropriate start_line."""
        try:
            if not os.path.exists(path):
                # removed files are cleaned from state
                with self._lock:
                    self.state.pop(path, None)
                    self._save_state()
                return
            cur_hash = self._hash_first_bytes(path)
            st = os.stat(path)
            mtime = st.st_mtime
        except Exception:
            logger.debug("Unable to stat/hash file: %s", path, exc_info=True)
            return

        with self._lock:
            entry = self.state.get(path)

        # New file
        if entry is None:
            logger.info("New file detected: %s", path)
            start_line = 0
            last_line = self.process_file(path, start_line=start_line)
            with self._lock:
                self.state[path] = {
                    "hash": cur_hash,
                    "last_line": int(last_line or 0),
                    "mtime": mtime,
                }
            self._save_state()
            return

        # Header changed -> reprocess from start
        if cur_hash is not None and cur_hash != entry.get("hash"):
            logger.info("File header changed, reprocessing from start: %s", path)
            start_line = 0
            last_line = self.process_file(path, start_line=start_line)
            with self._lock:
                self.state[path].update(
                    {"hash": cur_hash, "last_line": int(last_line or 0), "mtime": mtime}
                )
            self._save_state()
            return

        # If mtime changed -> process appended lines
        if mtime != entry.get("mtime"):
            logger.info("File modified, processing appended lines: %s", path)
            start_line = int(entry.get("last_line", 0))
            last_line = self.process_file(path, start_line=start_line)
            with self._lock:
                self.state[path].update(
                    {
                        "hash": cur_hash,
                        "last_line": int(last_line or start_line),
                        "mtime": mtime,
                    }
                )
            self._save_state()
            return

    def start_monitoring(self, block=True):
        """Start the observer and worker thread. If block is True this call blocks."""
        logger.info("Starting PollingObserver monitor for: %s", self.directory_path)
        # schedule handler
        self._observer.schedule(self._handler, self.directory_path, recursive=True)
        self._observer.start()

        # # initial scan
        self._initial_scan()

        # start worker threadon
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

        if block:
            try:
                while not self._stop_event.is_set():
                    time.sleep(0.5)
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt received, stopping monitor.")
                self.stop_monitoring()

    def stop_monitoring(self):
        """Stop observer and worker and persist state."""
        logger.info("Stopping monitor and saving state.")
        self._stop_event.set()
        try:
            self._observer.stop()
            self._observer.join(timeout=2.0)
        except Exception:
            pass
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=2.0)
        self._save_state()

    def process_file(self, file_path, start_line: int = 0) -> int:
        """Stub: process .jsonl file lines starting at start_line (0-based).
        Must return the number of lines processed (i.e., next start_line).
        """
        logger.debug(
            "process_file called for %s starting at line %d", file_path, start_line
        )
        last_processed = start_line
        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as fh:

                my_sketch = get_sketch_by_opts(
                    sketch_id=self._config_dict.get("sketch_id"),  # type: ignore
                    sketch_name=self._config_dict.get("sketch_name"),  # type: ignore
                    sketch_name_path_pos=self._config_dict.get("sketch_name_path_pos"),  # type: ignore
                    file_path=file_path,
                    ts_client=self._ts_client,
                )

                if not my_sketch:
                    logger.error("Unable to get or create sketch.")
                    sys.exit(1)

                timeline_name = get_timeline_name_by_opts(
                    timeline_name=self._config_dict.get("timeline_name"),  # type: ignore
                    timeline_name_path_pos=self._config_dict.get("timeline_name_path_pos"),  # type: ignore
                    file_path=file_path,
                )

                logger.debug(
                    f"Processing file {file_path} with sketch_name {my_sketch.name} and timeline_name {timeline_name}"
                )
                import_helper = helper.ImportHelper()
                import_helper.add_config_dict(self._config_dict)
                with importer.ImportStreamer() as streamer:
                    streamer.set_sketch(my_sketch)
                    streamer.set_config_helper(import_helper)
                    streamer.set_provider("File monitor importer tool")
                    streamer.set_timeline_name(timeline_name)

                    for idx, _line in enumerate(fh):
                        if idx < start_line:  # skip already processed lines
                            continue
                        if not _line.endswith("\n"):
                            logger.debug(
                                "Line %d incomplete, stopping processing file and keeping previous index",
                                idx + 1,
                            )
                            return idx  # incomplete line at EOF , this means the line may still be written to by the writer

                        streamer.add_json(json_entry=_line)
                        last_processed = idx + 1  # increment last processed line

            return last_processed
        except Exception:
            logger.exception("Error while processing file: %s", file_path)
            return last_processed


def main(args=None):
    """The main function of the tool."""
    if args is None:
        args = sys.argv[1:]

    argument_parser = argparse.ArgumentParser(
        description="A tool to upload data to Timesketch, using the API."
    )

    argument_parser.add_argument(
        "--version",
        action="store_true",
        dest="show_version",
        help="Print version information",
    )

    argument_parser.add_argument(
        "--debug",
        "--verbose",
        "-d",
        action="store_true",
        dest="show_debug",
        help="Make the logging more verbose to include debug logs.",
    )

    auth_group = argument_parser.add_argument_group(
        title="Authentication Arguments",
        description=(
            "If no authentication parameters are supplied the default "
            "timesketch RC and token files will be used to provide the "
            "authentication information. If those files are not present "
            "the tool will ask you questions and store the results in those "
            "files for future authentication."
        ),
    )

    auth_group.add_argument(
        "-u",
        "--user",
        "--username",
        action="store",
        dest="username",
        type=str,
        help="The username of the Timesketch user.",
    )
    auth_group.add_argument(
        "-p",
        "--password",
        "--pwd",
        action="store",
        type=str,
        dest="password",
        help=(
            "If authenticated with password, provide the password on the CLI. "
            "If neither password is provided nor a password prompt an OAUTH "
            "connection is assumed."
        ),
    )
    auth_group.add_argument(
        "--pwd-prompt",
        "--pwd_prompt",
        action="store_true",
        default=False,
        dest="pwd_prompt",
        help="Prompt for password.",
    )
    auth_group.add_argument(
        "--cred-prompt",
        "--cred_prompt",
        "--token-password",
        "--token_password",
        "--token",
        action="store_true",
        default=False,
        dest="cred_prompt",
        help="Prompt for password to decrypt and encrypt credential file.",
    )
    auth_group.add_argument(
        "--client-secret",
        "--client_secret",
        action="store",
        type=str,
        default="",
        dest="client_secret",
        help="OAUTH client secret.",
    )
    auth_group.add_argument(
        "--client-id",
        "--client_id",
        action="store",
        type=str,
        default="",
        dest="client_id",
        help="OAUTH client ID.",
    )
    auth_group.add_argument(
        "--run_local",
        "--run-local",
        action="store_true",
        dest="run_local",
        help=(
            "If OAUTH is used to authenticate and the connection is over "
            "SSH then it is recommended to set this option. When set an "
            "authentication URL is prompted on the screen, requiring a "
            "copy/paste into a browser to complete the OAUTH dance."
        ),
    )
    auth_group.add_argument(
        "--re-prompt",
        "--re_prompt",
        action="store_true",
        dest="re_prompt",
        help=(
            "If for some reasons you type the wrong username, password "
            "or host information you can use this parameter to re-enter "
            "those mistyped values."
        ),
    )

    config_group = argument_parser.add_argument_group("Configuration Arguments")

    config_group.add_argument(
        "--quick",
        "-q",
        "--no-wait",
        "--no_wait",
        action="store_false",
        default=True,
        dest="wait_timeline",
        help=(
            "By default the tool will wait until the timeline has been "
            "indexed and print out some details of the import. This option "
            "makes the tool exit as soon as the data has been imported and "
            "does not wait until it's been indexed."
        ),
    )

    config_group.add_argument(
        "--log-config-file",
        "--log_config_file",
        "--lc",
        action="store",
        type=str,
        default="",
        metavar="FILEPATH",
        dest="log_config_file",
        help=(
            "Path to a YAML config file that defines the config for parsing "
            "and setting up file parsing. By default formatter.yaml that "
            "comes with the importer will be used."
        ),
    )

    config_group.add_argument(
        "--host",
        "--hostname",
        "--host-uri",
        "--host_uri",
        dest="host_uri",
        type=str,
        default="",
        action="store",
        help="The URI to the Timesketch instance",
    )

    config_group.add_argument(
        "--format_string",
        "--format-string",
        type=str,
        action="store",
        dest="format_string",
        default="",
        help=(
            "Formatting string for the message field. If there is no message "
            "field in the input data a message string can be composed using "
            "a format string."
        ),
    )

    config_group.add_argument(
        "--timeline_name",
        "--timeline-name",
        action="store",
        type=str,
        dest="timeline_name",
        default="",
        help=("String that will be used as the timeline name."),
    )

    config_group.add_argument(
        "--timeline_name_path_pos",
        "--timeline-name-path-pos",
        action="store",
        type=int,
        dest="timeline_name_path_pos",
        default=-1,
        help=(
            "Use the n-th folder in the file path as timeline name, mostly useful in directory monitoring mode. "
            "Default is -1 (not used)."
        ),
    )

    config_group.add_argument(
        "--sketch_name",
        "--sketch-name",
        action="store",
        type=str,
        dest="sketch_name",
        default="",
        help=(
            "String that will be used as the sketch name in case a new "
            "sketch is created."
        ),
    )

    config_group.add_argument(
        "--sketch_name_path_pos",
        "--sketch-name-path-pos",
        action="store",
        type=int,
        dest="sketch_name_path_pos",
        default=-1,
        help=(
            "Use the n-th folder in the file path as sketch name, mostly useful in directory monitoring mode. "
            "Default is -1 (not used)."
        ),
    )

    config_group.add_argument(
        "--data_label",
        "--data-label",
        action="store",
        type=str,
        dest="data_label",
        default="",
        help=(
            "The data label is used by the API to determine whether a new "
            "search index needs to be created or if the data can be appended "
            "to an already existing index. If a file is added this defaults "
            "to the file extension, otherwise a default value of generic is "
            "applied."
        ),
    )

    config_group.add_argument(
        "--config_section",
        "--config-section",
        action="store",
        type=str,
        dest="config_section",
        default="",
        help=(
            "The config section in the RC file that will be used to "
            "define server information."
        ),
    )

    config_group.add_argument(
        "--index-name",
        "--index_name",
        action="store",
        type=str,
        default="",
        dest="index_name",
        help=(
            "If the data should be imported into a specific timeline the "
            "index name needs to be provided, otherwise a new index will "
            "be generated."
        ),
    )
    config_group.add_argument(
        "--timestamp_description",
        "--timestamp-description",
        "--time-desc",
        "--time_desc",
        action="store",
        type=str,
        default="",
        dest="time_desc",
        help="Value for the timestamp_description field.",
    )

    config_group.add_argument(
        "--threshold_entry",
        "--threshold-entry",
        "--entries",
        action="store",
        type=int,
        default=0,
        dest="entry_threshold",
        help=("How many entries should be buffered up before being sent to server."),
    )

    config_group.add_argument(
        "--threshold_size",
        "--threshold-size",
        "--filesize",
        action="store",
        type=int,
        default=0,
        dest="size_threshold",
        help=(
            "For binary file transfer, how many bytes should be transferred "
            "per chunk."
        ),
    )

    config_group.add_argument(
        "--sketch_id",
        "--sketch-id",
        type=int,
        default=0,
        dest="sketch_id",
        action="store",
        help=(
            "The sketch ID to store the timeline in, if no sketch ID is "
            "provided a new sketch will be created."
        ),
    )

    config_group.add_argument(
        "--context",
        action="store",
        type=str,
        default="",
        dest="context",
        help=(
            "Set a context for the file upload. This could be a text "
            "describing how the data got collected or parameters to "
            "the tool. Defaults to how the CLI tool got run."
        ),
    )

    argument_parser.add_argument(
        "path",
        action="store",
        nargs="?",
        type=str,
        help=("Path to the file that is to be imported, or folder to be monitored."),
    )

    config_group.add_argument(
        "--analyzer_names",
        "--analyzer-names",
        nargs="*",
        action="store",
        dest="analyzer_names",
        default=[],
        help=(
            "Set of analyzers that we will automatically run right after the "
            "timelines are uploaded. The input needs to be the analyzers names. "
            "Provided as strings separated by space"
        ),
    )

    config_group.add_argument(
        "--monitor",
        action="store_true",
        dest="monitor",
        default=False,
        help=(
            "Monitor the path for new or changed files and automatically load new data."
        ),
    )

    config_group.add_argument(
        "--monitor_state_file",
        "--monitor-state-file",
        action="store",
        type=str,
        dest="monitor_state_file",
        default=os.path.join(
            os.path.expanduser("~"), ".timesketch_importer_monitor_state.json"
        ),
        help=(
            "Path to the monitor state file to persist per-file state. "
            "Default location is in the home directory."
        "--max-payload-size",
        "--max_payload_size",
        action="store",
        type=int,
        default=importer.ImportStreamer.DEFAULT_MAX_PAYLOAD_SIZE,
        dest="max_payload_size",
        help=(
            "The maximum size in bytes for a single HTTP upload request. "
            "This should match the server's MAX_FORM_MEMORY_SIZE. "
            "Defaults to 200MB."
        ),
    )

    config_group.add_argument(
        "--plaso-event-filter",
        "--plaso_event_filter",
        action="store",
        type=str,
        default="",
        dest="plaso_event_filter",
        help=(
            "A filter string to pass to psort when processing Plaso files. "
            "Example: 'parser match \"winreg\"'"
        ),
    )

    options = argument_parser.parse_args(args)

    if options.show_version:
        print("API Client Version: {0:s}".format(api_version.get_version()))
        print("Importer Client Version: {0:s}".format(importer_version.get_version()))
        sys.exit(0)

    if options.show_debug:
        configure_logger_debug()
    else:
        configure_logger_default()

    if not options.path:
        logger.error("A valid file path needs to be provided, unable to continue.")
        sys.exit(1)

    if options.monitor:
        if not os.path.isdir(options.path):
            logger.error(
                "Path {0:s} is not a directory, unable to monitor.".format(options.path)
            )
            sys.exit(1)
    elif not os.path.isfile(options.path):
        logger.error(
            "Path {0:s} is not valid, unable to continue.".format(options.path)
        )
        sys.exit(1)

    config_section = options.config_section
    assistant = config.ConfigAssistant()
    assistant.load_config_file(section=config_section)
    assistant.load_config_dict(vars(options))

    try:
        file_path = assistant.get_config("token_file_path")
    except KeyError:
        file_path = ""

    cred_storage = crypto.CredentialStorage(file_path=file_path)
    token_password = ""
    if options.cred_prompt:
        token_password = cli_input.ask_question(
            "Enter password to encrypt/decrypt credential file",
            input_type=str,
            hide_input=True,
        )

    try:
        credentials = cred_storage.load_credentials(
            config_assistant=assistant, password=token_password
        )
    except IOError:
        logger.error("Unable to decrypt the credential file")
        logger.debug("Error details:", exc_info=True)
        logger.error(
            "If you've forgotten the password you can delete "
            "the ~/.timesketch.token file and run the tool again."
        )
        sys.exit(1)

    conf_password = ""

    if credentials:
        logger.info("Using cached credentials.")
        if credentials.TYPE.lower() == "oauth":
            assistant.set_config("auth_mode", "oauth")
        elif credentials.TYPE.lower() == "timesketch":
            assistant.set_config("auth_mode", "timesketch")

    else:
        # Check whether we'll need to read password for timesketch
        # auth from the command line.
        if options.pwd_prompt:
            conf_password = getpass.getpass("Type in the password: ")
        else:
            conf_password = options.password

        if options.run_local:
            assistant.set_config("auth_mode", "oauth_local")

        if options.client_secret:
            assistant.set_config("auth_mode", "oauth")

        if conf_password:
            assistant.set_config("auth_mode", "timesketch")

    if conf_password:
        credentials = ts_credentials.TimesketchPwdCredentials()
        credentials.credential = {
            "username": assistant.get_config("username"),
            "password": conf_password,
        }
        logger.info("Saving Credentials.")
        cred_storage.save_credentials(
            credentials,
            password=token_password,
            file_path=file_path,
            config_assistant=assistant,
        )

    # Gather all questions that are missing.
    config.configure_missing_parameters(
        config_assistant=assistant,
        token_password=token_password,
        confirm_choices=options.re_prompt,
    )

    logger.info("Creating a client.")
    ts_client = assistant.get_client(token_password=token_password)
    if not ts_client:
        logger.error("Unable to create a Timesketch API client, exiting.")
        sys.exit(1)

    logger.info("Client created.")
    logger.info("Saving TS config.")
    assistant.save_config(section=config_section, token_file_path=file_path)

    if ts_client.credentials:
        logger.info("Saving Credentials.")
        cred_storage.save_credentials(
            ts_client.credentials,
            password=token_password,
            file_path=file_path,
            config_assistant=assistant,
        )

    if options.monitor:

        config_dict = {
            "message_format_string": options.format_string,
            "index_name": options.index_name,
            "timestamp_description": options.time_desc,
            "entry_threshold": options.entry_threshold,
            "size_threshold": options.size_threshold,
            "log_config_file": options.log_config_file,
            "data_label": options.data_label,
            "analyzer_names": options.analyzer_names,
            "sketch_id": options.sketch_id,
            "sketch_name": options.sketch_name,
            "timeline_name": options.timeline_name,
            "sketch_name_path_pos": options.sketch_name_path_pos,
            "timeline_name_path_pos": options.timeline_name_path_pos,
        }

        logger.info(
            "Starting to monitor directory for new/updated files: %s", options.path
        )
        monitor = WatchdogDirectoryMonitor(
            directory_path=options.path,
            ts_client=ts_client,
            config_dict=config_dict,
            state_file=options.monitor_state_file,
            # wait_timeline=options.wait_timeline,
        )
        try:
            monitor.start_monitoring()
        except KeyboardInterrupt:
            logger.info("Stopping monitoring of directory.")
            monitor.stop_monitoring()
        return

    my_sketch = get_sketch_by_opts(
        sketch_id=options.sketch_id,
        sketch_name=options.sketch_name,
        sketch_name_path_pos=options.sketch_name_path_pos,
        file_path=options.path,
        ts_client=ts_client,
    )

    if not my_sketch:
        logger.error("Unable to get sketch ID: {0:d}".format(options.sketch_id))
        sys.exit(1)

    conf_timeline_name = get_timeline_name_by_opts(
        timeline_name=options.timeline_name,
        timeline_name_path_pos=options.timeline_name_path_pos,
        file_path=options.path,
    )

    context = options.context
    if not context:
        # Create a copy to modify
        argv_sanitized = []
        password_args = ["-p", "--password", "--pwd"]
        skip_next = False
        for arg in sys.argv:
            if skip_next:
                skip_next = False
                continue
            if arg in password_args:
                skip_next = True
                continue
            if arg.startswith(tuple(f"{a}=" for a in password_args)):
                continue
            argv_sanitized.append(arg)
        context = " ".join(argv_sanitized)

    config_dict = {
        "message_format_string": options.format_string,
        "timeline_name": conf_timeline_name,
        "index_name": options.index_name,
        "timestamp_description": options.time_desc,
        "entry_threshold": options.entry_threshold,
        "size_threshold": options.size_threshold,
        "log_config_file": options.log_config_file,
        "data_label": options.data_label,
        "context": context,
        "analyzer_names": options.analyzer_names,
        "max_payload_size": options.max_payload_size,
        "plaso_event_filter": options.plaso_event_filter,
    }

    logger.info("Uploading file.")
    timeline, task_id = upload_file(
        my_sketch=my_sketch, config_dict=config_dict, file_path=options.path
    )

    if not options.wait_timeline:
        logger.info(
            "File got successfully uploaded to sketch: {0:d}".format(my_sketch.id)
        )
        if options.analyzer_names:
            logger.warning(
                "Argument 'analyzer_names' only works with 'wait_timeline = "
                "True'! Skipping execution of analyzers: {analyzer_names}"
            )
        return

    if not timeline:
        logger.warning(
            "There does not seem to be any timeline returned, check whether "
            "the data got uploaded."
        )
        return

    print("Checking file upload status: ", end="")
    while True:
        status = timeline.status
        if status in ("archived", "failed", "fail"):
            print("[FAIL]")
            print(
                "Unable to index timeline (ID: {0:d}), reason: {1:s}".format(
                    timeline.id, timeline.status
                )
            )
            return

        if status not in ("ready", "success"):
            print(".", end="")
            time.sleep(3)
            continue

        print("[DONE]")
        print(f"Timeline uploaded to Timeline Id: {timeline.id}.")

        task_state = "Unknown"
        task_list = ts_client.check_celery_status(task_id)
        for task in task_list:
            if task.get("task_id", "") == task_id:
                task_state = task.get("state", "Unknown")
        print(f"Status of the index is: {task_state}")
        break

    if options.analyzer_names:
        logger.info(
            "Trigger analyzers: %s on Timeline '%s'",
            str(options.analyzer_names),
            str(timeline.name),
        )
        _ = importer.run_analyzers(
            analyzer_names=options.analyzer_names, timeline_obj=timeline
        )


if __name__ == "__main__":
    main()
