# Use the official Docker Hub Ubuntu 18.04 base image
FROM ubuntu:18.04

# Update the base image
RUN apt-get update && apt-get -y upgrade && apt-get -y dist-upgrade

# Setup install environment and Timesketch dependencies
RUN apt-get -y install apt-transport-https \
                       curl \
                       git \
                       libffi-dev \
                       lsb-release \
                       python3-dev \
                       python3-pip \
                       python3-psycopg2

RUN curl -sS https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN VERSION=node_8.x && \
    DISTRO="$(lsb_release -s -c)" && \
    echo "deb https://deb.nodesource.com/$VERSION $DISTRO main" > /etc/apt/sources.list.d/nodesource.list
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list

# Install Plaso, nodejs and yarn.
RUN apt-get -y install software-properties-common
RUN add-apt-repository ppa:gift/stable && apt-get update
RUN apt-get update && apt-get -y install plaso-tools nodejs yarn

# Use Python 3 pip (pip3) to install Timesketch
RUN pip3 install --upgrade pip
ADD . /tmp/timesketch
RUN cd /tmp/timesketch && yarn install && yarn run build
# Remove pyyaml from requirements.txt to avoid conflits with python-yaml Ubuntu package
RUN sed -i -e '/pyyaml/d' /tmp/timesketch/requirements.txt
RUN pip3 install /tmp/timesketch/

# Copy the Timesketch configuration file into /etc
RUN cp /tmp/timesketch/data/timesketch.conf /etc
# Copy Timesketch config files into /etc/timesketch
RUN mkdir /etc/timesketch
RUN cp /tmp/timesketch/data/features.yaml /etc/timesketch/

# Copy the entrypoint script into the container
COPY docker/docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Expose the port used by Timesketch
EXPOSE 5000

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
