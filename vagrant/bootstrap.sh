#!/usr/bin/env bash

# Generate random passwords for DB and session key
PSQL_PW="$(openssl rand -hex 32)"
SECRET_KEY="$(openssl rand -hex 32)"

# Setup GIFT PPA apt repository
add-apt-repository -y ppa:gift/stable
apt-get update

# Install PostgreSQL
apt-get install -y postgresql
apt-get install -y python-psycopg2

# Create DB user and database
echo "create user timesketch with password '${PSQL_PW}';" | sudo -u postgres psql
echo "create database timesketch owner timesketch;" | sudo -u postgres psql

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

# Install Elasticsearch 2.x
wget https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.4.4/elasticsearch-2.4.4.deb
echo "27074f49a251bc87795822e803de3ddecb275125 *elasticsearch-2.4.4.deb" | sha1sum -c -
dpkg -i ./elasticsearch-2.4.4.deb

# Install Elasticsearch 5.x
#apt-get install apt-transport-https
#wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
#echo "deb https://artifacts.elastic.co/packages/5.x/apt stable main" | sudo tee -a /etc/apt/sources.list.d/elastic-5.x.list
#apt-get update
#apt-get install elasticsearch

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

# Create test user
sudo -u ubuntu tsctl add_user --username spock --password spock

# Create a test timeline
sudo -u ubuntu psort.py -o timesketch /vagrant/test.plaso --name test-timeline
