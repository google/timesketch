#!/bin/bash
# Run after the standard e2e suite with the same compose services running.
set -euo pipefail
repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

compose() {
  "${COMPOSE_BIN:-docker}" compose -f "$repo_root/docker/e2e/docker-compose.yml" "$@"
}

set_prefix() {
  compose exec -T timesketch sed -i \
    "s/^OPENSEARCH_INDEX_PREFIX =.*/OPENSEARCH_INDEX_PREFIX = \"$1\"/" \
    /etc/timesketch/timesketch.conf
  compose restart timesketch
}

run_phase() {
  compose exec -T timesketch python3 \
    /usr/local/src/timesketch/end_to_end_tests/tools/prefix_transition.py "$1"
}

trap 'set_prefix ""' EXIT
set_prefix ""
run_phase 0
set_prefix "timesketch-test-"
run_phase 1
set_prefix "timesketch_"
run_phase 2
