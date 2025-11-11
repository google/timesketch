# Use the official Docker Hub Ubuntu base image
ARG BASE_IMAGE="ubuntu:24.04"
FROM ${BASE_IMAGE} AS common

USER root

ARG TIMESKETCH_USER_NAME="ubuntu"
ARG TIMESKETCH_USER_UID="1000"
ARG TIMESKETCH_USER_GID="1000"
ARG TIMESKETCH_CONF_DIR="/etc/timesketch"
RUN if id -u "${TIMESKETCH_USER_UID}" &>/dev/null; then \
    echo "User with UID ${TIMESKETCH_USER_UID} already exists."; \
  else \
    echo "Creating user ${USER_NAME} (${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID})..."; \
      if getent group "${TIMESKETCH_USER_GID}" >/dev/null; then \
        echo "Group with GID ${TIMESKETCH_USER_GID} already exists."; \
      else \
        echo "Creating group ${TIMESKETCH_USER_NAME} with GID ${TIMESKETCH_USER_GID}..."; \
        groupadd -g "${TIMESKETCH_USER_GID}" "${TIMESKETCH_USER_NAME}"; \
      fi; \
      useradd -m -u "${TIMESKETCH_USER_UID}" -g "${TIMESKETCH_USER_GID}" -s /bin/bash "${TIMESKETCH_USER_NAME}"; \
  fi \
  && for d in "${TIMESKETCH_CONF_DIR}" "/usr/local/src/sigma"; do \
    mkdir -p "${d}" \
    && chown "${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" "${d}"; \
    done \
  && echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
    software-properties-common \
    apt-transport-https \
    apt-utils \
    ca-certificates \
    curl \
    git \
    gpg-agent \
    python3-dev \
    python3-pip \
    python3-wheel \
    python3-setuptools \
    python3-psycopg2 \
    python3-venv \
    tzdata \
    nano \
    vim \
    python3-venv \
  && rm -rf /var/lib/apt/lists/*

FROM common AS common-python

# Install Plaso
ARG GIFT_PPA_TRACK="stable"
ARG GIFT_PPA_URL="http://ppa.launchpad.net/gift/${GIFT_PPA_TRACK}/ubuntu"
RUN set -eux \
  && DIST="$(lsb_release -cs)" \
  && KEY_ID="$(curl -sS "${GIFT_PPA_URL}/dists/${DIST}/Release.gpg" | gpg --list-packets | grep -oE 'keyid [0-9A-F]+' | cut -d ' ' -f 2)" \
  && curl -sSL "https://keyserver.ubuntu.com/pks/lookup?op=get&search=0x${KEY_ID}" | \
    gpg --dearmor -o /usr/share/keyrings/gift.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/gift.gpg] ${GIFT_PPA_URL} ${DIST} main" > /etc/apt/sources.list.d/gift.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
    plaso-tools \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /root/.gnupg

# Fix for broken PPA dependency in Ubuntu 24.04: Plaso needs the 'events'
# library for its opensearch output module.
RUN pip3 install --break-system-packages events

ARG PYTHON_PIP_CONF=""
RUN if [ -n "${PYTHON_PIP_CONF}" ]; then \
    mkdir -p /root/.config/pip /home/${TIMESKETCH_USER_NAME}/.config/pip; \
    env echo -e "${PYTHON_PIP_CONF}" > /root/.config/pip/pip.conf; \
    cp /root/.config/pip/pip.conf /home/${TIMESKETCH_USER_NAME}/.config/pip/pip.conf; \
    chown -R "${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" /home/${TIMESKETCH_USER_NAME}/.config; \
  fi

USER "${TIMESKETCH_USER_NAME}"

# Install dependencies for Timesketch in a virtual environment
COPY --chown="${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" ["api_client", "/usr/local/src/timesketch/api_client/"]
COPY --chown="${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" ["cli_client", "/usr/local/src/timesketch/cli_client/"]
COPY --chown="${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" ["end_to_end_tests", "/usr/local/src/timesketch/end_to_end_tests/"]
COPY --chown="${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" ["importer_client", "/usr/local/src/timesketch/importer_client/"]
COPY --chown="${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" ["timesketch", "/usr/local/src/timesketch/timesketch/"]
COPY --chown="${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" ["tests", "/usr/local/src/timesketch/tests/"]
COPY --chown="${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" [ \
  "requirements.txt", \
  "setup.py", \
  "test_requirements.txt", \
  "/usr/local/src/timesketch/" \
]

RUN python3 -m venv --upgrade-deps --system-site-packages "${HOME}/venv" \
  && . "${HOME}/venv/bin/activate" \
  && pip install --no-cache-dir \
    -r /usr/local/src/timesketch/requirements.txt \
    -r /usr/local/src/timesketch/test_requirements.txt \
  && pip install -e /usr/local/src/timesketch

# Update the PATH to include the virtual environment
ENV PATH="/home/${TIMESKETCH_USER_NAME}/venv/bin:${PATH}"
ENV TIMESKETCH_CONF_DIR="${TIMESKETCH_CONF_DIR}"

FROM common-python AS setup

COPY --chown=root:root --chmod=755 ["contrib/docker/dev/timesketch/setup-docker-entrypoint.sh", "/usr/local/bin/docker-entrypoint.sh"]
ENTRYPOINT ["docker-entrypoint.sh"]

FROM common-python AS celery-worker

USER root

ARG PLASO_LOG_DIR="/var/log/timesketch/psort"
RUN mkdir -p "${PLASO_LOG_DIR}" \
  && chown "${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" "${PLASO_LOG_DIR}"

USER "${TIMESKETCH_USER_NAME}"

COPY --chown=root:root --chmod=755 ["contrib/docker/dev/timesketch/celery-worker-docker-entrypoint.sh", "/usr/local/bin/docker-entrypoint.sh"]
ENTRYPOINT ["docker-entrypoint.sh"]

FROM common-python AS gunicorn

COPY --chown=root:root --chmod=755 ["contrib/docker/dev/timesketch/gunicorn-docker-entrypoint.sh", "/usr/local/bin/docker-entrypoint.sh"]

HEALTHCHECK --interval=10s --timeout=5s --start-period=15s --start-interval=2s --retries=1 \
    CMD ["curl", "-f", "-s", "http://localhost:5000/"]

ENTRYPOINT ["docker-entrypoint.sh"]

FROM common AS vue-cli-service

USER root

# Install NodeJS for frontend development
ARG NODE_VERSION="20.x"
ARG NODE_PPA_URL="https://deb.nodesource.com/node_${NODE_VERSION}"
RUN set -eux \
  && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | \
    gpg --dearmor -o /usr/share/keyrings/nodesource.gpg \
  && echo "deb [signed-by=/usr/share/keyrings/nodesource.gpg] ${NODE_PPA_URL} nodistro main" > /etc/apt/sources.list.d/nodesource.list \
  && apt-get update \
  && apt-get install -y --no-install-recommends \
    nodejs \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/* /root/.gnupg

ARG TIMESKETCH_USER_NAME="timesketch"
ARG TIMESKETCH_USER_UID="1000"
ARG TIMESKETCH_USER_GID="1000"
ARG NODE_NPMRC=""
RUN if [ -n "${NODE_NPMRC}" ]; then \
    env echo -e "${NODE_NPMRC}" > /root/.npmrc; \
    cp /root/.npmrc /home/${TIMESKETCH_USER_NAME}/.npmrc; \
    chown "${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" /home/${TIMESKETCH_USER_NAME}/.npmrc; \
  fi

ARG YARN_YARNRC=""
RUN if [ -n "${YARN_YARNRC}" ]; then \
    env echo -e "${YARN_YARNRC}" > /root/.yarnrc; \
    cp /root/.yarnrc /home/${TIMESKETCH_USER_NAME}/.yarnrc; \
    chown "${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" /home/${TIMESKETCH_USER_NAME}/.yarnrc; \
  fi

# Install Yarn for frontend development
RUN npm install --global yarn

USER "${TIMESKETCH_USER_NAME}"

COPY --chown="${TIMESKETCH_USER_UID}:${TIMESKETCH_USER_GID}" ["timesketch", "/usr/local/src/timesketch/timesketch/"]

ARG FRONTEND_VERSION="frontend-ng"
ENV FRONTEND_VERSION="${FRONTEND_VERSION}"
RUN if ! yarn --cwd="/usr/local/src/timesketch/timesketch/${FRONTEND_VERSION}" install; then \
  yarn --cwd="/usr/local/src/timesketch/timesketch/${FRONTEND_VERSION}" install --no-lockfile; \
fi

COPY --chown=root:root --chmod=755 [ \
  "contrib/docker/dev/timesketch/vue-cli-service-docker-entrypoint.sh", \
  "/usr/local/bin/docker-entrypoint.sh" \
]
ENTRYPOINT ["docker-entrypoint.sh"]
