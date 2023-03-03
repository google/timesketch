# Install Timesketch GKE

## Introduction

In this guide, you will learn how to deploy Timesketch using
[Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine).

At the end of this guide, you will have a newly provisioned GKE cluster, a GCP
Filestore instance to store logs and output, and lastly Timesketch locally
running within the cluster.

### Prerequisites

- A Google Cloud Account and a project to work from
- The ability to create GCP resources
- `gcloud` and `kubectl` locally installed

### This guide will setup the following services in GKE

- Timesketch web/api server
- Timesketch importer/analysis worker
- PostgreSQL database
- OpenSearch single-node cluster
- Redis key-value database (for worker processes)
- Optionally deployable ingress for external access

## Deployment

This section covers the steps for deploying a Timesketch GKE environment.

### 1. Download the helper script

We have created a helper script to get you started with all necessary configuration.
Download the script here:

```shell
curl -s -O https://raw.githubusercontent.com/google/timesketch/master/contrib/deploy_timesketch_gke.sh
chmod 755 deploy_timesketch_gke.sh
```

#### Review default cluster values

Once downloaded, review the deployment script's cluster configuration section
and update the default values if necessary based on cluster requirements.

### 2. Authenticate to GCP project

```shell
gcloud config set project <PROJECT-ID>
```

### 3. Run the deployment script

```shell
 ./deploy_timesketch_gke.sh
```

**Note this script will create a new GKE cluster and GCP Filestore instance then deploy Timesketch to the cluster.**

#### Using existing cluster or filestore instance

To use a pre existing cluster or filestore instance you can specify the
`--no-cluster` and/or `--no-filestore` flags. Please ensure you have the cluster
or filestore instance created prior and the default cluster values updated to the
correct names.

Congrats, you have successfully deployed Timesketch into GKE!

### Networks listed

The following ports will be exposed as part of deployment:

- 5000 - Timesketch API and Web UI
- 9200 - Opensearch
- 5432 - Postgres
- 6379 - Redis

## Connecting to Timesketch

- Connect to the cluster:

```
gcloud container clusters get-credentials <CLUSTER_NAME> --zone <ZONE> --project <PROJECT_NAME>
```

- Forward the Timesketch service port locally to your machine:

```
kubectl port-forward service/timesketch-web 5000:5000
```

- You can access the Timesketch Web UI via:

```
http://localhost:5000
```
