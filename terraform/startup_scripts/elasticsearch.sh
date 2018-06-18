#!/bin/bash


# --- BEFORE MAIN (DO NOT EDIT) ---

# Exit on any error
set -e

# Default constants.
readonly BOOT_FINISHED_FILE="/var/lib/cloud/instance/boot-finished"
readonly STARTUP_FINISHED_FILE="/var/lib/cloud/instance/startup-script-finished"

# Redirect stdout and stderr to logfile
exec > /var/log/terraform_provision.log
exec 2>&1

# Exit if the startup script has already been executed successfully
if [[ -f "$${STARTUP_FINISHED_FILE}" ]]; then
  exit 0
fi

# Wait for cloud-init to finish all tasks
until [[ -f "$${BOOT_FINISHED_FILE}" ]]; do
  sleep 1
done

# --- END BEFORE MAIN ---


# --- MAIN ---

# Install Elasticsearch
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://artifacts.elastic.co/packages/6.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-6.x.list
apt-get update
apt-get install -y openjdk-8-jre-headless elasticsearch

# Enable the GCE discovery plugin
echo "y" | /usr/share/elasticsearch/bin/elasticsearch-plugin install discovery-gce

# Export hostname so we can set the node name to it.
echo "export HOSTNAME=\$(hostname -s)" >> /etc/default/elasticsearch

# Configure Elasticsearch
cat >> /etc/elasticsearch/elasticsearch.yml <<EOF
cluster.name: ${es_cluster_name}
node.name: $${HOSTNAME}
cloud.gce.project_id: ${project}
cloud.gce.zone: ${zone}
discovery.zen.hosts_provider: gce
network.host: _gce_
EOF

# Start Elasticsearch and enable at boot
/bin/systemctl enable elasticsearch.service
/etc/init.d/elasticsearch start

# --- END MAIN ---


# --- AFTER MAIN (DO NOT EDIT)

date > "$${STARTUP_FINISHED_FILE}"

# --- END AFTER MAIN ---
