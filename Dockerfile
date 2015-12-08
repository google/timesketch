# A Docker container capable of running timesketch.
FROM ubuntu:trusty
MAINTAINER timesketch-dev@googlegroups.com

ENV DOCKER=true

RUN mkdir -p /usr/local/share/timesketch/contrib
COPY contrib/install_script_ubuntu.sh /usr/local/share/timesketch/contrib
RUN bash /usr/local/share/timesketch/contrib/install_script_ubuntu.sh

COPY contrib/install_script_timesketch.sh /usr/local/share/timesketch/contrib
RUN bash /usr/local/share/timesketch/contrib/install_script_timesketch.sh

COPY contrib/ts_config/timesketch.conf /etc

COPY contrib/docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]

# Port for timesketch WebGUI
EXPOSE 5000

# App config, logs, sqlite db
VOLUME ["/usr/local/share/timesketch"]

CMD ["timesketch"]
