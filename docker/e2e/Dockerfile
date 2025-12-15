# We use the official Plaso image as our base cache.
# This corresponds to Plaso Stable (latest release).
FROM log2timeline/plaso:latest

ARG PLASO_PPA_TRACK=stable
ARG UBUNTU_VERSION=24.04

# Switch to root to perform updates and installs
USER root

# Prevent interactive prompts
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

# -----------------------------------------------------------------------------
# SYSTEM DEPENDENCIES & PLASO TRACK SETUP
# -----------------------------------------------------------------------------
# Combined to reduce Docker layers and avoid redundant apt-get updates.
RUN \
  # 1. PREPARE STAGING (Conditional)
  # If Staging is requested, remove stable PPA and add Staging PPA.
  # We use '-n' to skip the immediate apt-update, deferring it to the next step.
  if [ "$PLASO_PPA_TRACK" = "staging" ]; then \
  echo "Staging track detected. Switching PPA from Stable to Staging..."; \
  # Remove the existing stable PPA file provided by the base image
  rm -f /etc/apt/sources.list.d/gift-*.list; \
  # Add the staging repository
  add-apt-repository -y -n ppa:gift/staging; \
  else \
  echo "Stable track detected. Keeping base image PPA."; \
  fi && \
  # 2. UPDATE & INSTALL COMMON TOOLS
  # This runs a single update for either the Stable or Staging repos
  apt-get update && apt-get install -y --no-install-recommends \
  git \
  gpg-agent \
  python3-pip \
  python3-psycopg2 \
  python3-setuptools \
  python3-venv \
  python3-wheel \
  tzdata \
  wget \
  && \
  # 3. UPGRADE PLASO (Conditional)
  # If we are on staging, we explicitly upgrade the tools to the version found in the new PPA
  if [ "$PLASO_PPA_TRACK" = "staging" ]; then \
  apt-get install -y --only-upgrade plaso-tools; \
  fi && \
  # 4. CLEANUP
  rm -rf /var/lib/apt/lists/*

# -----------------------------------------------------------------------------
# PYTHON / OPENSEARCH FIXES
# -----------------------------------------------------------------------------

# 1. Fix for Ubuntu 24.04 (Noble) missing 'events' dependency for Plaso
# This is required for both Stable and Staging on 24.04
RUN if [ "$UBUNTU_VERSION" = "24.04" ]; then \
  echo "Applying 'events' library fix for Ubuntu 24.04..."; \
  pip3 install --break-system-packages events; \
  fi

# 2. Fix for Staging Track (Opensearch-py version mismatch)
# Staging often requires a newer or specific opensearch-py version not yet in apt
RUN if [ "$PLASO_PPA_TRACK" = "staging" ] && [ "$UBUNTU_VERSION" = "24.04" ]; then \
  echo "Plaso staging on 24.04 detected, installing opensearch-py==3.0.0"; \
  pip3 install --break-system-packages opensearch-py==3.0.0; \
  fi

# Debugging info
RUN psort.py --version

# -----------------------------------------------------------------------------
# TIMESKETCH SETUP
# -----------------------------------------------------------------------------

# Create venv inheriting the Plaso site-packages (System)
RUN python3 -m venv /opt/venv --system-site-packages
ENV PATH="/opt/venv/bin:$PATH"

# Install Timesketch
ADD . /tmp/timesketch

# Install dependencies first (better caching)
RUN pip3 install -r /tmp/timesketch/requirements.txt

# Install Timesketch and clients in one go for atomic dependency resolution
RUN pip3 install \
  /tmp/timesketch \
  /tmp/timesketch/api_client/python \
  /tmp/timesketch/importer_client/python \
  /tmp/timesketch/cli_client/python

# Configs
RUN mkdir -p /etc/timesketch
WORKDIR /tmp/timesketch/data
RUN cp timesketch.conf \
  ontology.yaml \
  tags.yaml \
  intelligence_tag_metadata.yaml \
  regex_features.yaml \
  winevt_features.yaml \
  plaso.mappings \
  generic.mappings \
  sigma_config.yaml \
  data_finder.yaml \
  bigquery_matcher.yaml \
  plaso_formatters.yaml \
  /etc/timesketch/ && \
  chmod -R go+r /etc/timesketch

# Copy the entrypoint script into the container
COPY docker/e2e/docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
