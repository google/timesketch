#!/usr/bin/env bash
set -e
set -u

DEBIAN_FRONTEND=noninteractive
VAGRANT=false
RUN_AS_USER=$USER
TIMESKETCH_PATH="."
VAGRANT_PATH="${TIMESKETCH_PATH}/vagrant"
PLASO_TEST_FILE="${VAGRANT_PATH}/test.plaso"

if [ -z ${1:-} ] || [ $1 == "vagrant" ]; then
  VAGRANT=true
  RUN_AS_USER="vagrant"
  TIMESKETCH_PATH="/usr/local/src/timesketch"
  VAGRANT_PATH="${TIMESKETCH_PATH}/vagrant"
  PLASO_TEST_FILE="${VAGRANT_PATH}/test.plaso"
fi

if [ ! -z ${2:-} ]; then
  PLASO_TEST_FILE="${2}"
fi

# Setup GIFT PPA apt repository
add-apt-repository -y ppa:gift/stable

# Add Elasticsearch 5.x repo
apt-get install -y apt-transport-https
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb https://artifacts.elastic.co/packages/5.x/apt stable main" | tee -a /etc/apt/sources.list.d/elastic-5.x.list

# Add Neo4j repo
wget -O - https://debian.neo4j.org/neotechnology.gpg.key | apt-key add -
echo "deb https://debian.neo4j.org/repo stable/" | tee /etc/apt/sources.list.d/neo4j.list

if [ "$VAGRANT" = true ]; then
  # Add Node.js 8.x repo
  curl -sS https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add -
  VERSION=node_8.x
  DISTRO="$(lsb_release -s -c)"
  echo "deb https://deb.nodesource.com/$VERSION $DISTRO main" | sudo tee /etc/apt/sources.list.d/nodesource.list

  # Add Yarn repo
  curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
  echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
fi

# Install apt dependencies
apt-get update
apt-get install -y \
  neo4j openjdk-8-jre-headless elasticsearch postgresql python-psycopg2 \
  python-pip python-dev libffi-dev redis-server python-plaso plaso-tools jq

# Install python dependencies
pip install --upgrade pip
pip install gunicorn pylint nose flask-testing coverage mock BeautifulSoup

if [ "$VAGRANT" = true ]; then
  # Install yarn and nodejs
  apt-get install -y nodejs yarn
  # Install nodejs dependencies
  HOME=/home/$RUN_AS_USER sudo -u $RUN_AS_USER bash -c 'cd /usr/local/src/timesketch && yarn install'
fi

# Install Timesketch
if [ "$VAGRANT" = true ]; then
  pip install -e "${TIMESKETCH_PATH}"
else
  pip install "${TIMESKETCH_PATH}"
fi

# Generate random passwords for DB and session key
if [ ! -f psql_pw ]; then
  openssl rand -hex 32 > psql_pw
fi
if [ ! -f secret_key ]; then
  openssl rand -hex 32 > secret_key
fi

PSQL_PW="$(cat psql_pw)"
SECRET_KEY="$(cat secret_key)"

# Create DB user and database if they don't yet exist
echo "create user timesketch with password '${PSQL_PW}';" | sudo -u postgres psql || true
echo "create database timesketch owner timesketch;" | sudo -u postgres psql || true

# Configure PostgreSQL
sudo -u postgres sh -c 'echo "local all timesketch md5" >> /etc/postgresql/9.5/main/pg_hba.conf'

# Initialize Timesketch
mkdir -p /var/lib/timesketch/
chown "${RUN_AS_USER}" /var/lib/timesketch
cp "${TIMESKETCH_PATH}"/timesketch.conf /etc/

# Set session key for Timesketch
sed s/"SECRET_KEY = u'<KEY_GOES_HERE>'"/"SECRET_KEY = u'${SECRET_KEY}'"/ /etc/timesketch.conf > /etc/timesketch.conf.new
mv /etc/timesketch.conf.new /etc/timesketch.conf

# Configure the DB password
sed s/"<USERNAME>:<PASSWORD>@localhost"/"timesketch:${PSQL_PW}@localhost"/ /etc/timesketch.conf > /etc/timesketch.conf.new
mv /etc/timesketch.conf.new /etc/timesketch.conf

# Configure the Neo4j password
sed s/"<N4J_PASSWORD>"/"neo4j"/ /etc/timesketch.conf > /etc/timesketch.conf.new
mv /etc/timesketch.conf.new /etc/timesketch.conf

# Copy groovy scripts
cp "${TIMESKETCH_PATH}"/contrib/*.groovy /etc/elasticsearch/scripts/

# Start Elasticsearch automatically
/bin/systemctl daemon-reload
/bin/systemctl enable elasticsearch.service
/bin/systemctl start elasticsearch.service

# Enable Celery task manager (for uploads)
mkdir -p /var/{lib,log,run}/celery
chown $RUN_AS_USER /var/{lib,log,run}/celery
cp "${VAGRANT_PATH}"/celery.service /etc/systemd/system/
cp "${VAGRANT_PATH}"/celery.conf /etc/
/bin/systemctl daemon-reload
/bin/systemctl enable celery.service
/bin/systemctl start celery.service

# Enable cypher-shell
echo "dbms.shell.enabled=true" >> /etc/neo4j/neo4j.conf

if [ "$VAGRANT" = true ]; then
  # Expose Neo4j to the host, for development purposes
  echo "dbms.connectors.default_listen_address=0.0.0.0" >> /etc/neo4j/neo4j.conf
fi

# Start Neo4j automatically
/bin/systemctl daemon-reload
/bin/systemctl enable neo4j
/bin/systemctl start neo4j

if [ "$VAGRANT" = true ]; then
  # Build Timesketch frontend
  HOME=/home/$RUN_AS_USER sudo -u $RUN_AS_USER bash -c 'cd /usr/local/src/timesketch && yarn run build'
fi

# Create test user
sudo -u "${RUN_AS_USER}" tsctl add_user --username spock --password spock

# Wait for Elasticsearch cluster to be ready
CLUSTER_HEALTH=False
RETRY_LIMIT=100
RETRY_DELAY_SEC=3
declare -i RETRIES=0
until [ "${CLUSTER_HEALTH}" == "green" ] || [ "${CLUSTER_HEALTH}" == "yellow" ]; do
  CLUSTER_HEALTH=$(/usr/bin/curl -s -XGET '127.0.0.1:9200/_cluster/health' | jq -r .status)
  echo "Elasticsearch cluster state: ${CLUSTER_HEALTH} (retries: ${RETRIES})"
  if [ $RETRIES -gt $RETRY_LIMIT ]; then
    exit 1
  fi
  sleep "${RETRY_DELAY_SEC}"
  RETRIES+=1
done

# Create a test timeline
sudo -u "${RUN_AS_USER}" psort.py -o timesketch "${PLASO_TEST_FILE}" --name test-timeline
