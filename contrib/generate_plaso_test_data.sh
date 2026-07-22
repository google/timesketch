#!/bin/bash

# Ensure script stops on first error
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <plaso_version>"
    echo "Example: $0 20260512"
    exit 1
fi

PLASO_VERSION="$1"
EVTX_FILE="../end_to_end_tests/test_data/System_3205_events.evtx"
OUT_PLASO="../end_to_end_tests/test_data/evtx_${PLASO_VERSION}.plaso"

if [ ! -f "${EVTX_FILE}" ]; then
    echo "Error: Could not find ${EVTX_FILE}"
    exit 1
fi

echo "Running log2timeline with plaso version: ${PLASO_VERSION}..."
docker run --rm -u "$(id -u):$(id -g)" -v "$(pwd)/..:/data" "log2timeline/plaso:${PLASO_VERSION}" log2timeline.py --storage_file "/data/end_to_end_tests/test_data/evtx_${PLASO_VERSION}.plaso" "/data/end_to_end_tests/test_data/System_3205_events.evtx"

echo "Successfully generated: ${OUT_PLASO}"
