#!/usr/bin/env bash

set -e

cd "/usr/local/src/timesketch/timesketch/${FRONTEND_VERSION:?}"

yarn install

if [[ "${FRONTEND_VERSION}" = "frontend" || "${FRONTEND_VERSION}" = "frontend-ng" ]]; then
  exec yarn run serve
elif [[ "${FRONTEND_VERSION}" = "frontend-v3" ]]; then
  exec yarn dev
else
  echo "Unknown FRONTEND_VERSION value: \"${FRONTEND_VERSION}\"." >&2
  exit 1
fi
