#!/usr/bin/env bash
set -e
set -u

# Generate random passwords for DB and session key
if [ ! -f psql_pw ]; then
  openssl rand -hex 32 > psql_pw
fi
if [ ! -f secret_key ]; then
  openssl rand -hex 32 > secret_key
fi

PSQL_PW="$(cat psql_pw)"
SECRET_KEY="$(cat secret_key)"

# Setup GIFT PPA apt repository
add-apt-repository -y ppa:gift/stable
apt-get update

# Install PostgreSQL
apt-get install -y postgresql
apt-get install -y python-psycopg2

# Create DB user and database if they don't yet exist
echo "create user timesketch with password '${PSQL_PW}';" | sudo -u postgres psql || true
echo "create database timesketch owner timesketch;" | sudo -u postgres psql || true

# Configure PostgreSQL
sudo -u postgres sh -c 'echo "local all timesketch md5" >> /etc/postgresql/9.5/main/pg_hba.conf'

# Install Timesketch
apt-get install -y python-pip python-dev libffi-dev redis-server
pip install --upgrade pip
pip install -e /usr/local/src/timesketch/
pip install gunicorn

# Timesketch development dependencies
pip install pylint nose flask-testing coverage

# Initialize Timesketch
mkdir -p /var/lib/timesketch/
chown ubuntu /var/lib/timesketch
cp /vagrant/timesketch.conf /etc/

# Set session key for Timesketch
sed s/"SECRET_KEY = u'this is just a dev environment'"/"SECRET_KEY = u'${SECRET_KEY}'"/ /etc/timesketch.conf > /etc/timesketch.conf.new
mv /etc/timesketch.conf.new /etc/timesketch.conf

# Configure the DB password
sed s/"timesketch:foobar@localhost"/"timesketch:${PSQL_PW}@localhost"/ /etc/timesketch.conf > /etc/timesketch.conf.new
mv /etc/timesketch.conf.new /etc/timesketch.conf

# Java is needed for Elasticsearch
apt-get install -y openjdk-8-jre-headless

# Install Elasticsearch 5.x
apt-get install -y apt-transport-https
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://artifacts.elastic.co/packages/5.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-5.x.list
apt-get update
apt-get install -y elasticsearch

# Copy groovy scripts
cp /usr/local/src/timesketch/contrib/*.groovy /etc/elasticsearch/scripts/

# Start Elasticsearch automatically
/bin/systemctl daemon-reload
/bin/systemctl enable elasticsearch.service
/bin/systemctl start elasticsearch.service

# Install Plaso
apt-get install -y python-plaso

# Enable Celery task manager (for uploads)
mkdir -p /var/{lib,log,run}/celery
chown ubuntu /var/{lib,log,run}/celery
cp /vagrant/celery.service /etc/systemd/system/
cp /vagrant/celery.conf /etc/
/bin/systemctl daemon-reload
/bin/systemctl enable celery.service
/bin/systemctl start celery.service

# Install Neo4j graph database
wget -O - https://debian.neo4j.org/neotechnology.gpg.key | apt-key add -
echo "deb https://debian.neo4j.org/repo stable/" | tee /etc/apt/sources.list.d/neo4j.list
apt-get update
apt-get install -y neo4j

# Enable cypher-shell
echo "dbms.shell.enabled=true" >> /etc/neo4j/neo4j.conf

# Expose Neo4j to the host, for development purposes
echo "dbms.connectors.default_listen_address=0.0.0.0" >> /etc/neo4j/neo4j.conf

# Start Neo4j automatically
/bin/systemctl daemon-reload
/bin/systemctl enable neo4j
/bin/systemctl start neo4j

# Create test user
sudo -u ubuntu tsctl add_user --username spock --password spock

# Create a test timeline
sudo -u ubuntu psort.py -o timesketch /vagrant/test.plaso --name test-timeline
