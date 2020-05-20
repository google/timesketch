# Use the latest Timesketch development base image
FROM gcr.io/timesketch-build/dev/timesketch-dev-base:latest

# Install dependencies for Timesketch
COPY requirements.txt /timesketch-requirements.txt
RUN pip3 install -r /timesketch-requirements.txt

# Copy the entrypoint script into the container
COPY docker/dev/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod a+x /docker-entrypoint.sh

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
