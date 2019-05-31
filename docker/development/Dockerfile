# Use the latest Timesketch development base image
FROM timesketch/timesketch-dev-base:latest

# Copy the entrypoint script into the container
COPY docker/development/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod a+x /docker-entrypoint.sh

# Load the entrypoint script to be run later
ENTRYPOINT ["/docker-entrypoint.sh"]

# Invoke the entrypoint script
CMD ["timesketch"]
