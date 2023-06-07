# Use the official Docker Hub Ubuntu base image
FROM ubuntu:22.04

ARG PLASO_PPA_TRACK=stable

# Prevent needing to configure debian packages, stopping the setup of
# the docker container.
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
  software-properties-common \
  python3-pip \
  python3-wheel \
  python3-setuptools \
  python3-psycopg2 \
  gpg-agent \
  git \
  wget \
  tzdata \
  && rm -rf /var/lib/apt/lists/*

# Install Plaso
RUN add-apt-repository -y ppa:gift/$PLASO_PPA_TRACK
RUN apt-get update && apt-get install -y --no-install-recommends \
  plaso-tools \
  && rm -rf /var/lib/apt/lists/*

# Install timesketch from the current branch (In the context of CI platform)
ADD . /tmp/timesketch
RUN pip3 install -r /tmp/timesketch/requirements.txt
RUN pip3 install /tmp/timesketch && pip3 install /tmp/timesketch/api_client/python && \
  pip3 install /tmp/timesketch/importer_client/python

# Copy Timesketch config files into /etc/timesketch
RUN mkdir /etc/timesketch
RUN cp /tmp/timesketch/data/timesketch.conf /etc/timesketch/
RUN cp /tmp/timesketch/data/ontology.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/tags.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/intelligence_tag_metadata.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/features.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/plaso.mappings /etc/timesketch/
RUN cp /tmp/timesketch/data/generic.mappings /etc/timesketch/
RUN cp /tmp/timesketch/data/sigma_config.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/sigma_rule_status.csv /etc/timesketch/
RUN cp /tmp/timesketch/data/data_finder.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/bigquery_matcher.yaml /etc/timesketch/
RUN chmod -R go+r /etc/timesketch

# Copy the entrypoint script into the container
COPY docker/e2e/docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
