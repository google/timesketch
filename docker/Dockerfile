# Use the official Docker Hub Ubuntu 18.04 base image
FROM ubuntu:18.04

# Update the base image
RUN apt-get update && apt-get -y upgrade && apt-get -y dist-upgrade

# Setup install environment and Timesketch dependencies
RUN apt-get --no-install-recommends -y install apt-transport-https \
                       apt-utils \
                       ca-certificates \
                       git \
                       libffi-dev \
                       lsb-release \
                       python3-dev \
                       python3-pip \
                       python3-psycopg2

# Install Plaso, nodejs and yarn.
RUN apt-get --no-install-recommends -y install software-properties-common
RUN add-apt-repository ppa:gift/stable && apt-get update
RUN apt-get update && apt-get --no-install-recommends -y install plaso-tools

# Use Python 3 pip (pip3) to install Timesketch
RUN pip3 install timesketch

# Copy Timesketch config files into /etc/timesketch
ADD . /tmp/timesketch
RUN mkdir /etc/timesketch
RUN cp /tmp/timesketch/data/timesketch.conf /etc/timesketch/
RUN cp /tmp/timesketch/data/features.yaml /etc/timesketch/
RUN cp /tmp/timesketch/data/sigma_config.yaml /etc/timesketch/

# Copy the entrypoint script into the container
COPY docker/docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Expose the port used by Timesketch
EXPOSE 5000

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
