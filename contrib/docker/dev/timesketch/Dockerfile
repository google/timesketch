# Use the official Docker Hub Ubuntu base image
ARG BASE_IMAGE="ubuntu:24.04"
FROM $BASE_IMAGE

# Prevent needing to configure debian packages, stopping the setup of
# the docker container.
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
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
  && rm -rf /var/lib/apt/lists/* ~/.gnupg

# Fix for broken PPA dependency in Ubuntu 24.04: Plaso needs the 'events'
# library for its opensearch output module.
RUN pip3 install --break-system-packages events

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
  && rm -rf /var/lib/apt/lists/* ~/.gnupg

ARG NODE_NPMRC=""
RUN if [ -n "${NODE_NPMRC}" ]; then \
    env echo -e "${NODE_NPMRC}" > ~/.npmrc; \
  fi

ARG YARN_YARNRC=""
RUN if [ -n "${YARN_YARNRC}" ]; then \
    env echo -e "${YARN_YARNRC}" > ~/.yarnrc; \
  fi

ARG PYTHON_PIP_CONF=""
RUN if [ -n "${PYTHON_PIP_CONF}" ]; then \
    mkdir -p ~/.config/pip; \
    env echo -e "${PYTHON_PIP_CONF}" > ~/.config/pip/pip.conf; \
  fi

# Install Yarn for frontend development
RUN npm install --global yarn

# Install dependencies for Timesketch in a virtual environment
COPY ["requirements.txt", "/timesketch-requirements.txt"]
COPY ["test_requirements.txt", "/timesketch-test-requirements.txt"]
RUN python3 -m venv --upgrade-deps --system-site-packages /opt/venv \
    && . /opt/venv/bin/activate \
    && pip install --no-cache-dir \
        -r /timesketch-requirements.txt \
        -r /timesketch-test-requirements.txt \
        psycopg2-binary

# Update the PATH to include the virtual environment
ENV PATH="/opt/venv/bin:${PATH}"

# Copy the entrypoint script into the container
COPY ["contrib/docker/dev/timesketch/docker-entrypoint.sh", "/"]
RUN chmod a+x /docker-entrypoint.sh

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]
