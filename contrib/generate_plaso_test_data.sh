#!/bin/bash

# Ensure script stops on first error
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <plaso_version>"
    echo "Example: $0 20260512"
    exit 1
fi

PLASO_VERSION="$1"
EVTX_URL="https://github.com/log2timeline/plaso/raw/main/test_data/evtx/System.evtx"
EVTX_FILE="System.evtx"
OUT_PLASO="evtx_${PLASO_VERSION}.plaso"

echo "Downloading System.evtx..."
wget -q -O "${EVTX_FILE}" "${EVTX_URL}"

echo "Running log2timeline with plaso version: ${PLASO_VERSION}..."
docker run --rm -u $(id -u):$(id -g) -v "$(pwd):/data" "log2timeline/plaso:${PLASO_VERSION}" log2timeline.py --storage_file "/data/${OUT_PLASO}" "/data/${EVTX_FILE}"

echo "Successfully generated: ${OUT_PLASO}"
