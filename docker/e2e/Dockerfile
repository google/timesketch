ARG UBUNTU_VERSION=22.04
# Use the official Docker Hub Ubuntu base image
FROM ubuntu:${UBUNTU_VERSION}
# An `ARG` declared before a `FROM` instruction is only in scope
# for the `FROM` instruction.
ARG UBUNTU_VERSION

ARG PLASO_PPA_TRACK=stable

# Prevent needing to configure debian packages, stopping the setup of
# the docker container.
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
  git \
  gpg-agent \
  python3-pip \
  python3-psycopg2 \
  python3-setuptools \
  python3-venv \
  python3-wheel \
  software-properties-common \
  tzdata \
  wget \
  && rm -rf /var/lib/apt/lists/*

# Install Plaso
RUN add-apt-repository -y ppa:gift/$PLASO_PPA_TRACK
RUN apt-get update && apt-get install -y --no-install-recommends \
  plaso-tools \
  && rm -rf /var/lib/apt/lists/*


# Install opensearch-py globally for Plaso to find it                                  │
# Fix for broken PPA dependency: Plaso needs the 'events' library for its              │
# opensearch output module, but the python3-opensearch package is missing              │
# this dependency. We install it globally for the system Python.                       │
RUN if [ "$UBUNTU_VERSION" = "24.04" ]; then \
  echo '24.04 detected';  \
  pip3 install --break-system-packages events; \ 
  fi

# Some information for e2e test debugging in case something goes wrong
RUN pip3 show opensearch-py
RUN dpkg -s plaso-tools
RUN psort.py --version

# Create a virtual environment
RUN python3 -m venv /opt/venv --system-site-packages
ENV PATH="/opt/venv/bin:$PATH"

# Install timesketch from the current branch (In the context of CI platform)
ADD . /tmp/timesketch
RUN pip3 install -r /tmp/timesketch/requirements.txt
RUN pip3 install /tmp/timesketch && pip3 install /tmp/timesketch/api_client/python && \
  pip3 install /tmp/timesketch/importer_client/python && \
  pip3 install /tmp/timesketch/cli_client/python

# Copy Timesketch config files into /etc/timesketch
RUN mkdir /etc/timesketch
RUN cp /tmp/timesketch/data/timesketch.conf /etc/timesketch/
RUN cp /tmp/timesketch/data/ontology.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/tags.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/intelligence_tag_metadata.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/regex_features.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/winevt_features.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/plaso.mappings /etc/timesketch/
RUN cp /tmp/timesketch/data/generic.mappings /etc/timesketch/
RUN cp /tmp/timesketch/data/sigma_config.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/data_finder.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/bigquery_matcher.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/plaso_formatters.yaml /etc/timesketch/
RUN chmod -R go+r /etc/timesketch

# Copy the entrypoint script into the container
COPY docker/e2e/docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
