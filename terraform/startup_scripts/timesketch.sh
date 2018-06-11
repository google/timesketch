#!/bin/bash

set -e

exec > /var/log/terraform_provision.log
exec 2>&1

until [[ -f /var/lib/cloud/instance/boot-finished ]]; do
  sleep 1
done

# Install Plaso
add-apt-repository -y ppa:gift/stable
apt-get update
apt-get install -y python-plaso plaso-tools

