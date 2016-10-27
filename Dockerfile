FROM ubuntu:14.04

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y dist-upgrade

RUN apt-get -y install apt-transport-https
RUN apt-get -y install wget

RUN apt-get -y install openjdk-7-jre-headless

RUN wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
RUN echo "deb https://packages.elastic.co/elasticsearch/2.x/debian stable main" | sudo tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list
RUN apt-get update
RUN apt-get -y install elasticsearch
RUN echo "For Elasticsearch 1.x: script.groovy.sandbox.enabled: true" >> /etc/elasticsearch/elasticsearch.yml
RUN echo "For Elasticsearch 2.x: script.inline: on" >> /etc/elasticsearch/elasticsearch.yml
RUN update-rc.d elasticsearch defaults

RUN apt-get -y install postgresql
RUN apt-get -y install python-psycopg2
RUN echo "local   all             timesketch                              md5" >> /etc/postgresql/9.3/main/pg_hba.conf
RUN /etc/init.d/postgresql restart

RUN apt-get -y install python-pip python-dev libffi-dev
RUN pip install timesketch
