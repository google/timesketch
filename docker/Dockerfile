# Use the official Docker Hub Ubuntu 14.04 base image
FROM ubuntu:16.04

# Update the base image
RUN apt-get update && apt-get -y upgrade && apt-get -y dist-upgrade

# Install Timesketch dependencies
RUN apt-get -y install python-pip python-dev libffi-dev python-psycopg2 curl lsb-release apt-transport-https
RUN curl -sS https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN VERSION=node_8.x && \
    DISTRO="$(lsb_release -s -c)" && \
    echo "deb https://deb.nodesource.com/$VERSION $DISTRO main" > /etc/apt/sources.list.d/nodesource.list
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list

# Install Plaso
RUN apt-get -y install software-properties-common
RUN add-apt-repository ppa:gift/stable && apt-get update
RUN apt-get update && apt-get -y install nodejs yarn

# Use pip to install Timesketch
RUN pip install --upgrade pip
ADD . /tmp/timesketch
RUN pip install /tmp/timesketch/

# Build Timesketch frontend
RUN cd /tmp/timesketch && yarn install && yarn run build

# Copy the Timesketch configuration file into /etc
RUN cp /usr/local/share/timesketch/timesketch.conf /etc
RUN chmod 600 /etc/timesketch.conf

# Copy the entrypoint script into the container
COPY docker/docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Expose the port used by Timesketch
EXPOSE 5000

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
