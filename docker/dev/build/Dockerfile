# Use the official Docker Hub Ubuntu base image
FROM ubuntu:24.04

ARG PPA_TRACK=stable

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
    tzdata \
    nano \
    python3-venv \
  && rm -rf /var/lib/apt/lists/*

# Install Plaso
RUN add-apt-repository -y ppa:gift/$PPA_TRACK
RUN apt-get update && apt-get install -y --no-install-recommends \
    plaso-tools \
  && rm -rf /var/lib/apt/lists/*

# Fix for broken PPA dependency in Ubuntu 24.04: Plaso needs the 'events'
# library for its opensearch output module.
RUN pip3 install --break-system-packages events

# Install NodeJS for frontend development
RUN curl -sL https://deb.nodesource.com/setup_20.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
  && rm -rf /var/lib/apt/lists/*

# Install Yarn for frontend development
RUN npm install --global yarn

# Create a virtual environment and add it to the PATH
RUN python3 -m venv /opt/venv --system-site-packages
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies for Timesketch into the virtual environment
COPY ./requirements.txt /timesketch-requirements.txt
RUN pip3 install -r /timesketch-requirements.txt

# Install test dependencies for Timesketch into the virtual environment
COPY ./test_requirements.txt /timesketch-test-requirements.txt
RUN pip3 install -r /timesketch-test-requirements.txt

# Copy the entrypoint script into the container
COPY ./docker/dev/build/docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]
