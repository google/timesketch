# Pull and use the official Docker Hub Ubuntu 14.04 base image
FROM ubuntu:14.04

# Update the base image
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y dist-upgrade

# Install Timesketch dependencies
RUN apt-get -y install python-pip python-dev libffi-dev

# Use pip to install Timesketch
# RUN pip install timesketch
# Install from source (master branch of repository) because flask_login is currently broken (https://github.com/google/timesketch/pull/244)
RUN pip install https://github.com/google/timesketch/archive/master.zip

# Copy the Timesketch configuration file into /etc
RUN cp /usr/local/share/timesketch/timesketch.conf /etc
RUN chmod 600 /etc/timesketch.conf

# Copy the entrypoint script into the container
COPY docker-entrypoint.sh / 

# Expose the port used by Timesketch
EXPOSE 5000

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
