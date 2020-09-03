# Use the official Docker Hub Ubuntu 18.04 base image
FROM ubuntu:18.04

# Workaround for bug in setuptools v50.
# Ref: https://github.com/pypa/setuptools/issues/2350
ENV SETUPTOOLS_USE_DISTUTILS=stdlib

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
RUN pip3 install https://github.com/google/timesketch/archive/e2e-testing.zip

# Install Timesketch API and import clients
RUN pip3 install timesketch-api-client
RUN pip3 install timesketch-import-client

# Copy Timesketch config files into /etc/timesketch
RUN mkdir /etc/timesketch
RUN cp /usr/local/share/timesketch/timesketch.conf /etc/timesketch/
RUN cp /usr/local/share/timesketch/features.yaml /etc/timesketch/
RUN cp /usr/local/share/timesketch/sigma_config.yaml /etc/timesketch/

# Copy the entrypoint script into the container
COPY docker/e2e/docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
