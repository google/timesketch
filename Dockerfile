# Pull and use the official Docker Hub Ubuntu 14.04 base image
FROM ubuntu:14.04

# Update the base image
RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y dist-upgrade

# Install dependencies for commands below
RUN apt-get -y install apt-transport-https
RUN apt-get -y install wget

# Install Java
RUN apt-get -y install openjdk-7-jre-headless

# Add the Elastic repostitory to the sources list
RUN wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
RUN echo "deb https://packages.elastic.co/elasticsearch/2.x/debian stable main" | sudo tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list

# Install Elastic
RUN apt-get update
RUN apt-get -y install elasticsearch

# Configure Elastic
RUN echo "For Elasticsearch 1.x: script.groovy.sandbox.enabled: true" >> /etc/elasticsearch/elasticsearch.yml
RUN echo "For Elasticsearch 2.x: script.inline: on" >> /etc/elasticsearch/elasticsearch.yml

# Run Elastic on container start
RUN update-rc.d elasticsearch defaults

# Install Postgres
RUN apt-get -y install postgresql
RUN apt-get -y install python-psycopg2

# Allow the `timesketch` user to use Postgres
RUN echo "local   all             timesketch                              md5" >> /etc/postgresql/9.3/main/pg_hba.conf

# Run Postgres on container start
RUN /etc/init.d/postgresql restart

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
