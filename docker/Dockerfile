# Use the official Docker Hub Ubuntu 14.04 base image
FROM ubuntu:16.04

# Update the base image
RUN apt-get update && apt-get -y upgrade && apt-get -y dist-upgrade

# Setup install environment and Timesketch dependencies
RUN apt-get -y install apt-transport-https\
                       curl\
                       git\
                       libffi-dev\
                       lsb-release\
                       python-dev\
                       python-pip\
                       python-psycopg2

RUN curl -sS https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN VERSION=node_8.x && \
    DISTRO="$(lsb_release -s -c)" && \
    echo "deb https://deb.nodesource.com/$VERSION $DISTRO main" > /etc/apt/sources.list.d/nodesource.list
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list

# Install Plaso
RUN apt-get -y install software-properties-common
RUN add-apt-repository ppa:gift/stable && apt-get update
RUN apt-get update && apt-get -y install python-plaso plaso-tools nodejs yarn

# Use pip to install Timesketch
RUN pip install --upgrade pip
ADD . /tmp/timesketch
RUN cd /tmp/timesketch && yarn install && yarn run build
# Remove pyyaml from requirements.txt to avoid conflits with python-yaml ubuntu package
RUN sed -i -e '/pyyaml/d' /tmp/timesketch/requirements.txt
RUN pip install /tmp/timesketch/

# Copy the Timesketch configuration file into /etc
RUN cp /usr/local/share/timesketch/timesketch.conf /etc

# Copy the entrypoint script into the container
COPY docker/docker-entrypoint.sh /
RUN chmod a+x /docker-entrypoint.sh

# Expose the port used by Timesketch
EXPOSE 5000

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
