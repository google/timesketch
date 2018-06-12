#!/usr/bin/env bash

# Default constants
readonly BOOT_FINISHED_FILE="/var/lib/cloud/instance/boot-finished"
readonly STARTUP_FINISHED_FILE="/var/lib/cloud/instance/startup-script-finished"

# Custom constants for this startup script
readonly PLASO_TRACK="stable"

# Generate random passwords for DB and session key
readonly PSQL_PW="$(openssl rand -hex 32)"
readonly SECRET_KEY="$(openssl rand -hex 32)"


# --- BEFORE MAIN (DO NOT EDIT) ---

# Exit on all errors.
set -e

# Redirect stdout and stderr to logfile.
exec > /var/log/terraform_provision.log
exec 2>&1

# Exit if the startup script has already been executed successfully.
if [[ -f "${STARTUP_FINISHED_FILE}" ]]; then
  exit 0
fi

# Wait for cloud-init to finish all tasks.
until [[ -f "${BOOT_FINISHED_FILE}" ]]; do
  sleep 1
done

# --- END BEFORE MAIN ---


# --- MAIN ---

# Add extra package repositories
add-apt-repository -y ppa:gift/"${PLASO_TRACK}"
apt-get update

# Install dependencies
apt-get install -y python-pip gunicorn postgresql python-psycopg2 redis-server python-plaso plaso-tools

# Install Timesketch from PyPi
pip install timesketch

# Create PostgreSQL user and database
echo "create user timesketch with password ${PSQL_PW};" | sudo -u postgres psql
echo "create database timesketch owner timesketch;" | sudo -u postgres psql

# Configure PostgreSQL
readonly PSQL_CONFIG="$(find /etc/postgresql -name pg_hba.conf)"
sudo -u postgres sh -c 'echo "local all timesketch md5" >> ${PSQL_CONFIG}'




# --- END MAIN ---


# --- AFTER MAIN (DO NOT EDIT)

date > "${STARTUP_FINISHED_FILE}"

# --- END AFTER MAIN ---
