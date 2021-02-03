# Use the official Docker Hub Ubuntu 20.04 base image
FROM ubuntu:20.04

# Prevent needing to configure debian packages, stopping the setup of
# the docker container.
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    python3-pip \
    python3-wheel \
    python3-setuptools \
    python3-psycopg2 \
    git \
    wget \
  && rm -rf /var/lib/apt/lists/*

# Install Plaso
RUN add-apt-repository -y ppa:gift/stable
RUN apt-get update && apt-get install -y --no-install-recommends \
    plaso-tools \
  && rm -rf /var/lib/apt/lists/*

# Install Timesketch from master to get the latest code
RUN wget https://raw.githubusercontent.com/google/timesketch/master/requirements.txt
RUN pip3 install -r requirements.txt

# Install timesketch from the current branch (In the context of CI platform)
ADD . /tmp/timesketch
RUN pip3 install /tmp/timesketch && pip3 install /tmp/timesketch/api_client/python && \
    pip3 install /tmp/timesketch/importer_client/python

# Copy Timesketch config files into /etc/timesketch
RUN mkdir /etc/timesketch
RUN cp /tmp/timesketch/data/timesketch.conf /etc/timesketch/
RUN cp /tmp/timesketch/data/ontology.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/tags.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/features.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/sigma_config.yaml /etc/timesketch/

# TODO: This is only to enable e2e tests to run until a new dev release of
# plaso has been released, REMOVE IMMEDIATELY AFTER THAT HAS BEEN DONE.
# This will also fail as soon as the feature branch has been deleted.
RUN cd && apt-get install -y git && \
    git clone https://github.com/kiddinn/plaso.git && \
    git checkout elastic_ts && cd plaso && \
    apt-get remove -y plaso-tools && \
    python setup.py build && python setup.py install
# END Temporary Hack to make plaso work in the e2e test.


# Copy the entrypoint script into the container
COPY docker/e2e/docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
