# Use the official Docker Hub Ubuntu 18.04 base image
FROM ubuntu:18.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    software-properties-common \
    apt-transport-https \
    apt-utils \
    curl \
    git \
    python3-dev \
    python3-pip \
    python3-psycopg2 \
  && rm -rf /var/lib/apt/lists/*

# Install Plaso
RUN add-apt-repository -y ppa:gift/stable
RUN apt-get update && apt-get install -y --no-install-recommends \
    python-plaso \
    plaso-tools \
  && rm -rf /var/lib/apt/lists/*

# Install NodeJS and Yarn to build the frontend
RUN curl -sS https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN VERSION=node_8.x && \
    DISTRO="$(lsb_release -s -c)" && \
    echo "deb https://deb.nodesource.com/$VERSION $DISTRO main" > /etc/apt/sources.list.d/nodesource.list
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" > /etc/apt/sources.list.d/yarn.list
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    yarn \
  && rm -rf /var/lib/apt/lists/*
