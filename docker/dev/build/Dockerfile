# Use the official Docker Hub Ubuntu 20.04 base image
FROM ubuntu:20.04

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
  && rm -rf /var/lib/apt/lists/*

# Install Plaso
RUN add-apt-repository -y ppa:gift/stable
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3-plaso \
    plaso-tools \
  && rm -rf /var/lib/apt/lists/*

# Install NodeJS and Yarn to build the frontend
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    yarn \
  && rm -rf /var/lib/apt/lists/*

# Install test dependencies for Timesketch
COPY ../../../requirements.txt /timesketch-requirements.txt
RUN pip3 install -r /timesketch-requirements.txt

# Install test dependencies for Timesketch
COPY ../../../test_requirements.txt /timesketch-test-requirements.txt
RUN pip3 install -r /timesketch-test-requirements.txt

# Copy the entrypoint script into the container
COPY docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]
