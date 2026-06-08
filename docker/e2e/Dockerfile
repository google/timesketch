# We use the official Plaso image as our base cache.
# This corresponds to Plaso Stable.
ARG PLASO_VERSION=20260512
FROM log2timeline/plaso:${PLASO_VERSION}

ARG PLASO_PPA_TRACK=stable
ARG UBUNTU_VERSION=26.04
ARG PLASO_VERSION

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
    build-essential \
    git \
    gpg-agent \
    python3-dev \
    python3-pip \
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

# Install psycopg2-binary via pip (not available as apt package on 26.04)
RUN pip3 install --no-cache-dir --break-system-packages psycopg2-binary

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

# -----------------------------------------------------------------------------
# BUILD CONFIGURATION SUMMARY
# -----------------------------------------------------------------------------
RUN echo "==========================================================" && \
    echo "BUILD CONFIGURATION:" && \
    echo "  - Plaso Base Image: log2timeline/plaso:${PLASO_VERSION}" && \
    echo "  - Plaso PPA Track:  $PLASO_PPA_TRACK" && \
    echo "  - Target Ubuntu:    $UBUNTU_VERSION" && \
    echo "  - Python Version:   $(python3 --version)" && \
    echo "==========================================================" && \
    echo "REQUIREMENTS.TXT CONTENT:" && \
    cat /tmp/timesketch/requirements.txt && \
    echo "=========================================================="

# 1. Install dependencies from requirements.txt
RUN echo "Installing Python dependencies from requirements.txt..." && \
    pip3 install --no-cache-dir -r /tmp/timesketch/requirements.txt

# 2. Install Timesketch and clients
RUN echo "Installing Timesketch and client packages..." && \
    pip3 install --no-cache-dir \
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
