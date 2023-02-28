#!/bin/bash
# Copyright 2023 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -o posix
set -e

# Default Cluster configuration parameters.
CLUSTER_NAME='timesketch-main'
CLUSTER_MIN_NODE_SIZE='1'
CLUSTER_MAX_NODE_SIZE='20'
CLUSTER_MACHINE_TYPE='e2-standard-32'
CLUSTER_MACHINE_SIZE='200'
CLUSTER_ZONE='us-central1-f'
CLUSTER_REGION=='us-central1'
VPC_CONTROL_PANE='172.16.0.0/28'
VPC_NETWORK='default'
FILESTORE_NAME='timesketchvolume'
FILESTORE_CAPACITY='10T'


if [[ "$*" == *--help ||  "$*" == *-h ]] ; then
  echo "Timesketch deployment script for Kubernetes environment"
  echo "Options:"
  echo "--no-cluster                   Do not create the cluster"
  echo "--no-filestore                 Do not deploy Timesketch Filestore"
  echo "--no-node-autoscale            Do not enable Node autoscaling"
  exit 1
fi

# Exit early if gcloud is not installed.
if [[ -z "$( which gcloud )" ]] ; then
  echo "gcloud CLI not found.  Please follow the instructions at "
  echo "https://cloud.google.com/sdk/docs/install to install the gcloud "
  echo "package first."
  exit 1
fi

# Exit early if kubectl is not installed.
if [[ -z "$( which kubectl )" ]] ; then
  echo "kubectl CLI not found.  Please follow the instructions at "
  echo "https://kubernetes.io/docs/tasks/tools/ to install the kubectl "
  echo "package first."
  exit 1
fi

# Exit early if GCP project not set correctly.
if [[ -z "$DEVSHELL_PROJECT_ID" ]] ; then
  DEVSHELL_PROJECT_ID=$(gcloud config get-value project)
  ERRMSG="ERROR: Could not get configured project. Please either restart "
  ERRMSG+="Google Cloudshell, or set configured project with "
  ERRMSG+="'gcloud config set project PROJECT' when running outside of Cloudshell."
  if [[ -z "$DEVSHELL_PROJECT_ID" ]] ; then
    echo $ERRMSG
    exit 1
  fi
  echo "Environment variable \$DEVSHELL_PROJECT_ID was not set at start time "
  echo "so attempting to get project config from gcloud config."
  echo -n "Do you want to use $DEVSHELL_PROJECT_ID as the target project? (y / n) > "
  read response
  if [[ $response != "y" && $response != "Y" ]] ; then
    echo $ERRMSG
    exit 1
  fi
fi

# TODO: Do real check to make sure credentials have adequate roles
if [[ $( gcloud -q --project $DEVSHELL_PROJECT_ID auth list --filter="status:ACTIVE" --format="value(account)" | wc -l ) -eq 0 ]] ; then
  echo "No gcloud credentials found.  Use 'gcloud auth login' and 'gcloud auth application-default login' to log in"
  exit 1
fi

# Exit early if VPC network does not exist.
networks=$(gcloud -q --project $DEVSHELL_PROJECT_ID compute networks list --filter="name=$VPC_NETWORK" |wc -l)
if [[ "${networks}" -lt "2" ]]; then
  echo "ERROR: VPC network $VPC_NETWORK not found, please create this first."
  exit 1
fi

# Create the GKE cluster
if [[ "$*" != *--no-cluster* ]] ; then
  echo "Enabling Container API"
  gcloud -q --project $DEVSHELL_PROJECT_ID services enable container.googleapis.com
  if [[ "$*" != *--no-node-autoscale* ]] ; then
    echo "Creating cluster $CLUSTER_NAME with a minimum node size of $CLUSTER_MIN_NODE_SIZE to scale up to a maximum node size of $CLUSTER_MAX_NODE_SIZE. Each node will be configured with a machine type $CLUSTER_MACHINE_TYPE and disk size of $CLUSTER_MACHINE_SIZE"
    gcloud -q --project $DEVSHELL_PROJECT_ID container clusters create $CLUSTER_NAME --machine-type $CLUSTER_MACHINE_TYPE --disk-size $CLUSTER_MACHINE_SIZE --num-nodes $CLUSTER_MIN_NODE_SIZE --master-ipv4-cidr $VPC_CONTROL_PANE --network $VPC_NETWORK --zone $CLUSTER_ZONE --shielded-secure-boot --shielded-integrity-monitoring --no-enable-master-authorized-networks --enable-private-nodes --enable-ip-alias --scopes "https://www.googleapis.com/auth/cloud-platform" --labels "timesketch-infra=true" --workload-pool=$DEVSHELL_PROJECT_ID.svc.id.goog --default-max-pods-per-node=20 --enable-autoscaling --min-nodes=$CLUSTER_MIN_NODE_SIZE --max-nodes=$CLUSTER_MAX_NODE_SIZE
  else
    echo "--no-node-autoscale specified. Node size will remain constant at $CLUSTER_MIN_NODE_SIZE node(s)"
    echo "Creating cluster $CLUSTER_NAME with a node size of $CLUSTER_MIN_NODE_SIZE. Each node will be configured with a machine type $CLUSTER_MACHINE_TYPE and disk size of $CLUSTER_MACHINE_SIZE"
    gcloud -q --project $DEVSHELL_PROJECT_ID container clusters create $CLUSTER_NAME --machine-type $CLUSTER_MACHINE_TYPE --disk-size $CLUSTER_MACHINE_SIZE --num-nodes $CLUSTER_MIN_NODE_SIZE --master-ipv4-cidr $VPC_CONTROL_PANE --network $VPC_NETWORK --zone $CLUSTER_ZONE --shielded-secure-boot --shielded-integrity-monitoring --no-enable-master-authorized-networks --enable-private-nodes --enable-ip-alias --scopes "https://www.googleapis.com/auth/cloud-platform" --labels "timesketch-infra=true" --workload-pool=$DEVSHELL_PROJECT_ID.svc.id.goog --default-max-pods-per-node=20
  fi
else
  echo "--no-cluster specified. Authenticating to pre-existing cluster $CLUSTER_NAME"
fi

# Authenticate to cluster
gcloud -q --project $DEVSHELL_PROJECT_ID container clusters get-credentials $CLUSTER_NAME --zone $CLUSTER_ZONE

# Create the filestore instance.
if [[ "$*" != *--no-filestore* ]] ; then  
  echo "Enabling GCP Filestore API"
  gcloud -q --project $DEVSHELL_PROJECT_ID services enable file.googleapis.com
  echo "Creating Filestore instance $FILESTORE_NAME with capacity $FILESTORE_CAPACITY"
  gcloud -q --project $DEVSHELL_PROJECT_ID filestore instances create $FILESTORE_NAME --file-share=name=$FILESTORE_NAME,capacity=$FILESTORE_CAPACITY --zone=$CLUSTER_ZONE --network=name=$VPC_NETWORK
else
  echo "Using pre existing Filestore instance $FILESTORE_NAME with capacity $FILESTORE_CAPACITY"
fi

# Grab Filestore IP
FILESTORE_IP=$(gcloud -q --project $DEVSHELL_PROJECT_ID filestore instances describe $FILESTORE_NAME --zone=$CLUSTER_ZONE --format='value(networks.ipAddresses)' --flatten="networks[].ipAddresses[]")

# Timesketch configuration
#echo -n "* Setting default config parameters.."
POSTGRES_USER="timesketch"
POSTGRES_PASSWORD="$(echo $RANDOM | md5sum | head -c 32; echo;)"
POSTGRES_ADDRESS="postgres.default.svc.cluster.local"
POSTGRES_PORT=5432
SECRET_KEY="$(echo $RANDOM | md5sum | head -c 32; echo;)"
OPENSEARCH_ADDRESS="opensearch.default.svc.cluster.local"
OPENSEARCH_PORT=9200
REDIS_ADDRESS="redis.default.svc.cluster.local"
REDIS_PORT=6379
GITHUB_BASE_URL="https://raw.githubusercontent.com/google/timesketch/master"

# Create k8s dir
mkdir -p k8s

# TODO(wyassine): Once merged remove copy files locally to pull from github repo
cp ../k8s/* ./k8s

# Fetch Timesketch k8s deployment files
# echo -n "* Fetching k8s deployment files.."
# curl -s $GITHUB_BASE_URL/k8s/opensearch.yaml > k8s/opensearch.yaml
# curl -s $GITHUB_BASE_URL/k8s/postgres.yaml > k8s/postgres.yaml
# curl -s $GITHUB_BASE_URL/k8s/redis.yaml > k8s/redis.yaml
# curl -s $GITHUB_BASE_URL/k8s/opensearch.yaml > k8s/opensearch.yaml
# curl -s $GITHUB_BASE_URL/k8s/timesketch-ingress.yaml > k8s/timesketch-ingress.yaml
# curl -s $GITHUB_BASE_URL/k8s/timesketch-service-account.yaml > k8s/timesketch-service-account.yaml
# curl -s $GITHUB_BASE_URL/k8s/timesketch-volume-filestore.yaml > k8s/timesketch-volume-filestore.yaml
# curl -s $GITHUB_BASE_URL/k8s/timesketch-web-v2.yaml > k8s/timesketch-web-v2.yaml
# curl -s $GITHUB_BASE_URL/k8s/timesketch-web.yaml > k8s/timesketch-web.yaml
# curl -s $GITHUB_BASE_URL/k8s/timesketch-worker.yaml > k8s/timesketch-worker.yaml
# echo "OK"

# Create config dir
mkdir -p timesketch

# Fetch default Timesketch config files
echo -n "* Fetching configuration files.."
curl -s $GITHUB_BASE_URL/data/timesketch.conf > timesketch/timesketch.conf
curl -s $GITHUB_BASE_URL/data/tags.yaml > timesketch/tags.yaml
curl -s $GITHUB_BASE_URL/data/plaso.mappings > timesketch/plaso.mappings
curl -s $GITHUB_BASE_URL/data/generic.mappings > timesketch/generic.mappings
curl -s $GITHUB_BASE_URL/data/features.yaml > timesketch/features.yaml
curl -s $GITHUB_BASE_URL/data/ontology.yaml > timesketch/ontology.yaml
curl -s $GITHUB_BASE_URL/data/sigma_rule_status.csv > timesketch/sigma_rule_status.csv
curl -s $GITHUB_BASE_URL/data/tags.yaml > timesketch/tags.yaml
curl -s $GITHUB_BASE_URL/data/intelligence_tag_metadata.yaml > timesketch/intelligence_tag_metadata.yaml
curl -s $GITHUB_BASE_URL/data/sigma_config.yaml > timesketch/sigma_config.yaml
curl -s $GITHUB_BASE_URL/data/sigma_rule_status.csv > timesketch/sigma_rule_status.csv
curl -s $GITHUB_BASE_URL/data/sigma/rules/lnx_susp_zmap.yml > timesketch/lnx_susp_zmap.yml
echo "OK"

sed -i 's#SECRET_KEY = \x27\x3CKEY_GOES_HERE\x3E\x27#SECRET_KEY = \x27'$SECRET_KEY'\x27#' timesketch/timesketch.conf

# Set up the Elastic connection
sed -i 's#^OPENSEARCH_HOST = \x27127.0.0.1\x27#OPENSEARCH_HOST = \x27'$OPENSEARCH_ADDRESS'\x27#' timesketch/timesketch.conf

# Set up the Redis connection
sed -i 's#^UPLOAD_ENABLED = False#UPLOAD_ENABLED = True#' timesketch/timesketch.conf
sed -i 's#^UPLOAD_FOLDER = \x27/tmp\x27#UPLOAD_FOLDER = \x27/mnt/'$FILESTORE_NAME'/upload\x27#' timesketch/timesketch.conf

sed -i 's#^CELERY_BROKER_URL =.*#CELERY_BROKER_URL = \x27redis://'$REDIS_ADDRESS':'$REDIS_PORT'\x27#' timesketch/timesketch.conf
sed -i 's#^CELERY_RESULT_BACKEND =.*#CELERY_RESULT_BACKEND = \x27redis://'$REDIS_ADDRESS':'$REDIS_PORT'\x27#' timesketch/timesketch.conf

# Set up the Postgres connection
sed -i 's#postgresql://<USERNAME>:<PASSWORD>@localhost#postgresql://'$POSTGRES_USER':'$POSTGRES_PASSWORD'@'$POSTGRES_ADDRESS':'$POSTGRES_PORT'#' timesketch/timesketch.conf

echo "OK"

echo "* Timesketch deployment complete."