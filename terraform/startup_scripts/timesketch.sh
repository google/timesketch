#!/bin/bash


# --- BEFORE MAIN (DO NOT EDIT) ---

# Exit on any error
set -e

# Default constants.
readonly BOOT_FINISHED_FILE="/var/lib/cloud/instance/boot-finished"
readonly STARTUP_FINISHED_FILE="/var/lib/cloud/instance/startup-script-finished"

# Redirect stdout and stderr to logfile
#exec > /var/log/terraform_provision.log
#exec 2>&1

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

# Custom constants for this startup script
readonly PLASO_TRACK="stable"

# Generate random passwords for DB and session key
readonly PSQL_PW="$(openssl rand -hex 32)"
readonly SECRET_KEY="$(openssl rand -hex 32)"

# Add extra package repositories
add-apt-repository -y ppa:gift/"$${PLASO_TRACK}"
apt-get update

# Install dependencies
apt-get install -y nginx python-pip gunicorn postgresql python-psycopg2 redis-server python-plaso plaso-tools

# Create PostgreSQL user and database
echo "create user timesketch with password '$${PSQL_PW}';" | sudo -u postgres psql
echo "create database timesketch owner timesketch;" | sudo -u postgres psql

# Configure PostgreSQL
readonly PSQL_CONFIG="$(find /etc/postgresql -name pg_hba.conf)"
echo "local all timesketch md5" >> "$${PSQL_CONFIG}"

# Install Timesketch from PyPi
pip install timesketch

# Create default config
cp /usr/local/share/timesketch/timesketch.conf /etc/

# Set session key
sed -i s/"SECRET_KEY = u'<KEY_GOES_HERE>'"/"SECRET_KEY = u'$${SECRET_KEY}'"/ /etc/timesketch.conf

# Configure the DB password
sed -i s/"<USERNAME>:<PASSWORD>@localhost"/"timesketch:$${PSQL_PW}@localhost"/ /etc/timesketch.conf

# Systemd configuration for Gunicorn
#cat > /etc/systemd/system/gunicorn.service <<EOF
#
#EOF

# Create Gunicorn log dir
if [ ! -d /var/log/gunicorn/ ]; then
    mkdir /var/log/gunicorn/
    chown www-data.www-data /var/log/gunicorn/
fi

# Configure Nginx
cat > /etc/nginx/sites-available/timesketch <<EOF
server {
  listen 80;
  listen [::]:80;

  listen 443 ssl;
  ssl_certificate /etc/nginx/ssl/nginx.crt;
  ssl_certificate_key /etc/nginx/ssl/nginx.key;

  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host \$host;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
  }

  if (\$scheme != "https") {
    return 301 https://\$host\$request_uri;
  }
}
EOF

# Set our nginx config as default
ln -sf /etc/nginx/sites-available/timesketch /etc/nginx/sites-enabled/default

# Create self signed certificate for Nginx
mkdir /etc/nginx/ssl
openssl req -new -newkey rsa:4096 -days 999 -nodes -x509 -subj "/C=US/ST=Example/L=Example/O=DExample/CN=example.com" -keyout /etc/nginx/ssl/nginx.key -out /etc/nginx/ssl/nginx.crt

# Enable and start Gunicorn WSGI server
#/bin/systemctl daemon-reload
#/bin/systemctl enable gunicorn
#/bin/systemctl stop gunicorn
#/bin/systemctl start gunicorn

# Restart Nginx
/bin/systemctl restart nginx

# --- END MAIN ---


# --- AFTER MAIN (DO NOT EDIT)

date > "$${STARTUP_FINISHED_FILE}"

# --- END AFTER MAIN ---
