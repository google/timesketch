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

# What Plaso version to install
readonly PLASO_TRACK="stable"

# Generate random passwords for DB and session key
readonly PSQL_PW="$(openssl rand -hex 32)"
readonly SECRET_KEY="$(openssl rand -hex 32)"

# Add extra package repositories
add-apt-repository -y ppa:gift/"$${PLASO_TRACK}"
apt-get update

# Install dependencies
apt-get install -y python-pip postgresql-client python-psycopg2 python-plaso plaso-tools

# Change the password for the PostgreSQL user
until echo "ALTER USER gcs_importer WITH PASSWORD '$${PSQL_PW}';" | PGPASSWORD=changeme psql -h timesketch -U gcs_importer timesketch; do
  echo "Waiting for postgres server to start..."
  sleep 10
done

# Install Timesketch from PyPi
pip install timesketch

# Create default config
cp /usr/local/share/timesketch/timesketch.conf /etc/

# Set session key
sed -i s/"SECRET_KEY = u'<KEY_GOES_HERE>'"/"SECRET_KEY = u'$${SECRET_KEY}'"/ /etc/timesketch.conf

# Configure the DB password
sed -i s/"<USERNAME>:<PASSWORD>@localhost"/"gcs_importer:$${PSQL_PW}@${postgresql_server}"/ /etc/timesketch.conf

# What Elasticsearch server to use
sed -i s/"ELASTIC_HOST = u'127.0.0.1'"/"ELASTIC_HOST = u'${elasticsearch_node}'"/ /etc/timesketch.conf

# --- END MAIN ---


# --- AFTER MAIN (DO NOT EDIT)

date > "$${STARTUP_FINISHED_FILE}"
echo "Startup script finished successfully"

# --- END AFTER MAIN ---
