# Use the official Docker Hub Ubuntu 14.04 base image
FROM ubuntu:16.04

# Update the base image
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y dist-upgrade

# Install Timesketch dependencies
RUN apt-get -y install python-pip python-dev libffi-dev python-psycopg2

# Install Plaso
RUN apt-get -y install software-properties-common
RUN add-apt-repository ppa:gift/stable
RUN apt-get update
RUN apt-get -y install python-plaso

# Use pip to install Timesketch
ADD . /tmp/timesketch
RUN pip install /tmp/timesketch

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
