#!/bin/bash
#
# Script to install Timesketch from scratch on an Ubuntu system.

set -x
set -e

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

# Install dependencies for installing/building timesketch
echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
apt-get update
apt-get -y install python python-dev python-pip libffi-dev wget

apt-get -y install software-properties-common

# Install dependencies for running timesketch too
add-apt-repository ppa:gift/stable
apt-get update
apt-get -y install python-plaso
