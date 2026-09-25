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
"""Cluster capability checks for the direct-query languages.

PPL and SQL are served by the OpenSearch SQL plugin rather than by the search
API the rest of Timesketch uses, so whether they work is a property of the
cluster and not of the sketch. Both the sketch metadata, which drops the
languages from the search-mode menu, and the query endpoints, which refuse the
request outright, read their answer from here.

The probe goes over the same client the dialects use, so a cluster that answers
here is one that can serve the queries.
"""

import logging
import threading
import time

from flask import current_app
from opensearchpy import exceptions as opensearch_exceptions
from packaging import version

from timesketch.api.v1.resources.direct_query.base import MAPPING_TIMEOUT_SECONDS
from timesketch.api.v1.resources.direct_query.base import get_client

logger = logging.getLogger("timesketch.api.direct_query")

# The dialects rely on behaviour that settled in 3.7.0, the Calcite engine
# being the default for PPL among it. Older clusters accept the same queries
# but differ in how a filter injected ahead of a stats stage is pushed down,
# and the scoping this feature depends on is exactly such a filter.
MINIMUM_OPENSEARCH_VERSION = "3.7.0"

# Cluster properties change on a restart or an upgrade, not per request. They
# are cached, but not for the life of the process, so that a cluster upgraded
# underneath a running worker starts offering the languages without one.
PROBE_TTL_SECONDS = 300

_probe_lock = threading.Lock()
_probe = {"checked_at": 0.0, "result": None}


class DirectQuerySupport:
    """Whether a cluster can serve the direct-query languages, and why not."""

    def __init__(self, supported, reason=""):
        self.supported = supported
        self.reason = reason

    def __bool__(self):
        return self.supported


def _probe_call(call, label):
    """Run one capability call, or return None if the cluster cannot answer."""
    try:
        return call()
    except opensearch_exceptions.OpenSearchException as e:
        logger.warning("Capability probe (%s) failed: %s", label, e)
        return None


def _version_supported(raw_version):
    """Compare a reported cluster version against the minimum.

    An unreadable or unparsable version is treated as supported. Taking a
    working feature away because a probe could not answer is worse than
    letting the cluster reject the query itself.
    """
    if not isinstance(raw_version, str) or not raw_version:
        logger.warning("Could not read the OpenSearch version; assuming support")
        return DirectQuerySupport(True)

    try:
        too_old = version.parse(raw_version) < version.parse(MINIMUM_OPENSEARCH_VERSION)
    except version.InvalidVersion:
        logger.warning(
            "Unparsable OpenSearch version %s; assuming support", raw_version
        )
        return DirectQuerySupport(True)

    if too_old:
        return DirectQuerySupport(
            False,
            f"PPL and SQL require OpenSearch {MINIMUM_OPENSEARCH_VERSION} or "
            f"later; this cluster reports {raw_version}.",
        )
    return DirectQuerySupport(True)


def _plugin_supported(plugins):
    """Decide support from a _cat/plugins document.

    A document that could not be read leaves support unchanged, for the same
    reason an unreadable version does.
    """
    if plugins is None:
        return DirectQuerySupport(True)

    try:
        present = any(
            "sql" in (entry.get("component") or "").lower() for entry in plugins
        )
    except AttributeError:
        logger.warning("Unexpected shape from the OpenSearch plugin list")
        return DirectQuerySupport(True)

    if not present:
        return DirectQuerySupport(
            False,
            "The OpenSearch SQL plugin, which serves the PPL and SQL endpoints, "
            "is not installed on this cluster.",
        )
    return DirectQuerySupport(True)


def _probe_cluster():
    """Ask the cluster for its version and plugin list."""
    client = get_client()

    root = _probe_call(
        lambda: client.info(request_timeout=MAPPING_TIMEOUT_SECONDS), "version"
    )
    raw_version = None
    if isinstance(root, dict):
        raw_version = (root.get("version") or {}).get("number")

    supported = _version_supported(raw_version)
    if not supported:
        return supported

    plugins = _probe_call(
        lambda: client.cat.plugins(
            format="json", request_timeout=MAPPING_TIMEOUT_SECONDS
        ),
        "plugin list",
    )
    return _plugin_supported(plugins)


def reset_cache():
    """Forget the cached probe. Used by tests and after a config change."""
    with _probe_lock:
        _probe["checked_at"] = 0.0
        _probe["result"] = None


def direct_query_support():
    """Report whether this cluster can serve PPL and SQL.

    Returns:
        A DirectQuerySupport carrying a reason when unsupported. Truthy when
        the languages are available.
    """
    # Mirrors the datastore's own version gate: the test suite has no cluster
    # to ask, and a probe per sketch load would only buy a connection refusal.
    if current_app.config.get("TESTING"):
        return DirectQuerySupport(True)

    now = time.time()
    with _probe_lock:
        fresh = _probe["result"] is not None and now - _probe["checked_at"] < (
            PROBE_TTL_SECONDS
        )
        if fresh:
            return _probe["result"]

    # Probing outside the lock keeps a slow cluster from blocking every other
    # request; the worst case is two workers probing at once, which is
    # harmless.
    result = _probe_cluster()

    with _probe_lock:
        _probe["checked_at"] = now
        _probe["result"] = result
    return result
