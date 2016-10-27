# Pull and use the official Docker Hub Ubuntu 14.04 base image
FROM ubuntu:14.04

# Update the base image
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y dist-upgrade

# Install Timesketch dependencies
RUN apt-get -y install python-pip python-dev libffi-dev

# Use pip to install Timesketch
RUN pip install timesketch

# Copy the Timesketch configuration file into /etc
RUN cp /usr/local/share/timesketch/timesketch.conf /etc/
RUN chmod 600 /etc/timesketch.conf

# Copy the entrypoint script into the container
COPY docker-entrypoint.sh /usr/local/bin/

# Run the entrypoint script on container start
ENTRYPOINT ["docker-entrypoint.sh"]

# Use a Docker volume to make data persistent across container restarts
VOLUME ["/usr/local/share/timesketch"]

# Expose the port used by Timesketch
EXPOSE 5000

# Run Timesketch on container start
CMD ["timesketch"]
