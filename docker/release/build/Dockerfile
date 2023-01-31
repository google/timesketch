# Use the official Docker Hub Ubuntu base image
FROM ubuntu:22.04

ARG PPA_TRACK=stable

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
    wget \
  && rm -rf /var/lib/apt/lists/*

# Install Timesketch
RUN wget https://raw.githubusercontent.com/hnhdev/timesketch/master/requirements.txt
RUN pip3 install -r requirements.txt
RUN pip3 install https://github.com/hnhdev/timesketch/archive/master.zip

# Install Plaso
RUN add-apt-repository -y ppa:gift/$PPA_TRACK
RUN apt-get update && apt-get install -y --no-install-recommends \
    plaso-tools \
  && rm -rf /var/lib/apt/lists/*

# Copy the entrypoint script into the container
COPY docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]
