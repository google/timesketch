# Install Timesketch GKE

This guide will help you install Timesketch to [Google Kubernetes Engine (GKE)](https://cloud.google.com/kubernetes-engine).

It will help you provision a new GKE Cluster, a GCP Filestore instance to centrally store logs and output to, and then deploy Timesketch to the cluster which can be accessed through port-forwarding the service to your local machine.

**You will need**

- A Google Cloud Account and a project to work from
- The ability to create GCP resources

**This guide setup the following services in GKE**

- Timesketch web/api server
- Timesketch importer/analysis worker
- PostgreSQL database
- OpenSearch single-node cluster
- Redis key-value database (for worker processes)
- Optionally deployable ingress for external access

**NOTE**: Given that Timesketch K8s is a relatively new feature, this guide will set up a single node OpenSearch cluster until further testing is done. Please be aware of any performance dips this may cause as you scale out Timesketch.

## Deployment

Please follow these steps to deploy Timesketch to GKE.

### 1. Install Google Cloud SDK

Follow the official installation instructions to [install the gcloud CLI](https://cloud.google.com/sdk/docs/install).

Then make sure to install kubectl as well

```shell
gcloud components install kubectl
```

### 2. Start the installation

We have created a helper script to get you started with all necessary configuration.
Download the script here:

```shell
curl -s -O https://raw.githubusercontent.com/google/timesketch/master/contrib/deploy_timesketch_gke.sh
chmod 755 deploy_timesketch_gke.sh
```

#### Review default cluster values

Once downloaded, review the deployment script's cluster configuration section
and update the default values if necessary based on cluster requirements.

#### Authenticate to GCP project

```shell
gcloud config set project <PROJECT-ID>
```

#### Run the deployment script

```shell
 ./deploy_timesketch_gke.sh
```

**Note this script will create a new GKE cluster and GCP Filestore instance then deploy Timesketch to the cluster.**

Congrats, you have successfully deployed Timesketch into GKE!

#### Optional: using existing cluster or filestore instance

To use a pre existing cluster or filestore instance you can specify the
`--no-cluster` and/or `--no-filestore` flags. Please ensure you have the cluster
or filestore instance created prior and the default cluster values updated to the
correct names.

### Networks listed

The following ports will be exposed as part of deployment:

- 5000 - The Timesketch API and Web UI service
- 9200 - The Opensearch service
- 5432 - The Postgres service
- 6379 - The Redis service

### Connecting to Timesketch

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

#### Interacting with the Timesketch CLI

- Connect to the cluster:

```
gcloud container clusters get-credentials <CLUSTER_NAME> --zone <ZONE> --project <PROJECT_NAME>
```

- Get a list of running pods:

```
kubectl get pods
```

- Identify the pod named `timesketch-web-*` and exec into it via:

```
kubectl exec --stdin --tty [CONTAINER-NAME] -- bash
```

- You may now interact with Timesketch via `tsctl`
