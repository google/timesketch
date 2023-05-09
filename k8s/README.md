<!--- app-name: Timesketch -->
# Timesketch Helm Chart

A Helm chart for Timesketch. Timesketch is an open-source tool for collaborative 
forensic timeline analysis. Using sketches you and your collaborators can easily 
organize your timelines and analyze them all at the same time. Add meaning to 
your raw data with rich annotations, comments, tags and stars.

[Overview of Timesketch](http://www.timesketch.org)

[Chart Source Code](https://github.com/google/osdfir-infrastructure)
## TL;DR

```console
helm install my-release oci://us-docker.pkg.dev/osdfir-registry/osdfir-charts/timesketch
```
> **Tip**: To quickly get started with your own local Kubernetes cluster, see 
install docs for [minikube](https://minikube.sigs.k8s.io/docs/start/).

## Introduction

This chart bootstraps a [Timesketch](https://github.com/google/timesketch/blob/master/docker/release/build/Dockerfile-latest) deployment on a [Kubernetes](https://kubernetes.io) cluster using the [Helm](https://helm.sh) package manager.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.2.0+
- PV provisioner support in the underlying infrastructure

## Installing the Chart

To install the chart with the release name `my-release`:

```console
helm install my-release oci://us-docker.pkg.dev/osdfir-registry/osdfir-charts/timesketch
```

To pull the chart locally:
```console
helm pull oci://us-docker.pkg.dev/osdfir-registry/osdfir-charts/timesketch
```

To install the chart from a local repo with the release name `my-release`:
```console
helm install my-release ../timesketch
```

The install command deploys Timesketch on the Kubernetes cluster in the default 
configuration without any resources defined. This is so we can increase the 
chances our chart runs on environments with little resources, such as Minikube. 
The [Parameters](#parameters) section lists the parameters that can be configured 
during installation or see [Installating for Production](#installing-for-production) 
for a recommended production installation.

> **Tip**:  You can override the default Timesketch configuration by placing a 
`configs/` directory containing the user-provided configs at the root of the 
Helm chart. When choosing this option, pull and install the Helm chart locally.

## Installing for Production

Pull the chart locally and review the `values.production.yaml` file for a list 
of values that will be overridden as part of this installation. 
```console
helm pull oci://us-docker.pkg.dev/osdfir-registry/osdfir-charts/timesketch
```

Install the chart providing both the original values and the production values 
with a release name `my-release`:
```console
helm install my-release ../timesketch -f values.yaml -f values-production.yaml
```

To upgrade an existing release name `my-release` using production values, run:
```console
helm upgrade my-release -f values-production.yaml
```

Installing or upgrading a Timesketch deployment with `values-production.yaml` 
file will override a subset of values in the `values.yaml` file with a recommended
set of resources and replica pods needed for a production Timesketch installation
and deploys a GCP Filestore persistent volume for shared storage. For non GCP 
installations, please update the `persistence.storageClass` value with a 
storageClass supported by your provider.

## Uninstalling the Chart

To uninstall/delete the `my-release` deployment:

```console
helm delete my-release
```
> **Tip**: List all releases using `helm list`

The command removes all the Kubernetes components but PVC's associated with the chart and deletes the release.

To delete the PVC's associated with `my-release`:

```console
kubectl delete pvc -l release=my-release
```

> **Note**: Deleting the PVC's will delete Timesketch data as well. Please be cautious before doing it.

## Parameters

### Global parameters

| Name                  | Description                                                                             | Value |
| --------------------- | --------------------------------------------------------------------------------------- | ----- |
| `global.existingPVC`  | Existing claim for Timesketch persistent volume (overrides `persistent.name`)           | `""`  |
| `global.storageClass` | StorageClass for the Timesketch persistent volume (overrides `persistent.storageClass`) | `""`  |

### Timesketch image configuration

| Name                     | Description                                                   | Value                                                     |
| ------------------------ | ------------------------------------------------------------- | --------------------------------------------------------- |
| `image.repository`       | Timesketch image repository                                   | `us-docker.pkg.dev/osdfir-registry/timesketch/timesketch` |
| `image.pullPolicy`       | Timesketch image pull policy                                  | `IfNotPresent`                                            |
| `image.tag`              | Overrides the image tag whose default is the chart appVersion | `latest`                                                  |
| `image.imagePullSecrets` | Specify secrets if pulling from a private repository          | `[]`                                                      |

### Timesketch Configuration Parameters

| Name                | Description                                                                                                                           | Value       |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| `config.override`   | Overrides the default Timesketch configs to instead use a user specified directory if present on the root directory of the Helm chart | `configs/*` |
| `config.createUser` | Creates a default Timesketch user that can be used to login to Timesketch after deployment                                            | `true`      |

### Timesketch Frontend Configuration

| Name                          | Description                                                                 | Value |
| ----------------------------- | --------------------------------------------------------------------------- | ----- |
| `frontend.podSecurityContext` | Holds pod-level security attributes and common frontend container settings  | `{}`  |
| `frontend.securityContext`    | Holds security configuration that will be applied to the frontend container | `{}`  |
| `frontend.resources.limits`   | The resources limits for the frontend container                             | `{}`  |
| `frontend.resources.requests` | The requested resources for the frontend container                          | `{}`  |
| `frontend.nodeSelector`       | Node labels for Timesketch frontend pods assignment                         | `{}`  |
| `frontend.tolerations`        | Tolerations for Timesketch frontend pods assignment                         | `[]`  |
| `frontend.affinity`           | Affinity for Timesketch frontend pods assignment                            | `{}`  |

### Timesketch Worker Configuration

| Name                               | Description                                                               | Value   |
| ---------------------------------- | ------------------------------------------------------------------------- | ------- |
| `worker.podSecurityContext`        | Holds pod-level security attributes and common worker container settings  | `{}`    |
| `worker.securityContext`           | Holds security configuration that will be applied to the worker container | `{}`    |
| `worker.resources.limits`          | The resources limits for the worker container                             | `{}`    |
| `worker.resources.requests.cpu`    | The requested cpu for the worker container                                | `250m`  |
| `worker.resources.requests.memory` | The requested memory for the worker container                             | `256Mi` |
| `worker.nodeSelector`              | Node labels for Timesketch worker pods assignment                         | `{}`    |
| `worker.tolerations`               | Tolerations for Timesketch worker pods assignment                         | `[]`    |
| `worker.affinity`                  | Affinity for Timesketch worker pods assignment                            | `{}`    |

### Common Parameters

| Name                              | Description                                                                                       | Value               |
| --------------------------------- | ------------------------------------------------------------------------------------------------- | ------------------- |
| `nameOverride`                    | String to partially override names.fullname                                                       | `""`                |
| `fullnameOverride`                | String to fully override names.fullname                                                           | `""`                |
| `serviceAccount.create`           | Specifies whether a service account should be created                                             | `true`              |
| `serviceAccount.annotations`      | Annotations to add to the service account                                                         | `{}`                |
| `serviceAccount.name`             | The name of the service account to use                                                            | `timesketch`        |
| `service.type`                    | Timesketch service type                                                                           | `ClusterIP`         |
| `service.port`                    | Timesketch service port                                                                           | `5000`              |
| `metrics.enabled`                 | Enables metrics scraping                                                                          | `true`              |
| `metrics.port`                    | Port to scrape metrics from                                                                       | `9200`              |
| `persistence.name`                | Timesketch persistent volume name                                                                 | `timesketchvolume`  |
| `persistence.size`                | Timesketch persistent volume size                                                                 | `8Gi`               |
| `persistence.storageClass`        | PVC Storage Class for Timesketch volume                                                           | `""`                |
| `persistence.accessModes`         | PVC Access Mode for Timesketch volume                                                             | `["ReadWriteOnce"]` |
| `ingress.enabled`                 | Enable the Timesketch loadbalancer for external access                                            | `false`             |
| `ingress.host`                    | Domain name Timesketch will be hosted under                                                       | `""`                |
| `ingress.className`               | IngressClass that will be be used to implement the Ingress                                        | `gce`               |
| `ingress.gcp.managedCertificates` | Enables GCP managed certificates for your domain                                                  | `false`             |
| `ingress.gcp.staticIPName`        | Name of the static IP address you reserved in GCP. Required when using "gce" in ingress.className | `""`                |

### Third Party Configuration


### Opensearch Configuration Parameters

| Name                               | Description                                                                                                 | Value                                                                                    |
| ---------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `opensearch.enabled`               | Enables the Opensearch deployment                                                                           | `true`                                                                                   |
| `opensearch.config.opensearch.yml` | Opensearch configuration file. Can be appended for additional configuration options                         | `{"opensearch.yml":"plugins:\n  security:\n    allow_unsafe_democertificates: false\n"}` |
| `opensearch.extraEnvs[0].name`     | Environment variable to disable Opensearch Demo config                                                      | `DISABLE_INSTALL_DEMO_CONFIG`                                                            |
| `opensearch.extraEnvs[0].value`    | Disables Opensearch Demo config                                                                             | `true`                                                                                   |
| `opensearch.extraEnvs[1].name`     | Environment variable to disable Opensearch Security plugin given that                                       | `DISABLE_SECURITY_PLUGIN`                                                                |
| `opensearch.extraEnvs[1].value`    | Disables Opensearch Security plugin                                                                         | `true`                                                                                   |
| `opensearch.replicas`              | Number of Opensearch instances to deploy                                                                    | `1`                                                                                      |
| `opensearch.sysctlInit.enabled`    | Sets optimal sysctl's through privileged initContainer                                                      | `false`                                                                                  |
| `opensearch.opensearchJavaOpts`    | Sets the size of the Opensearch Java heap                                                                   | `-Xmx512M -Xms512M`                                                                      |
| `opensearch.httpPort`              | Opensearch service port                                                                                     | `9200`                                                                                   |
| `opensearch.persistence.size`      | Opensearch Persistent Volume size. A persistent volume would be created for each Opensearch replica running | `8Gi`                                                                                    |
| `opensearch.resources.requests`    | Requested resources for the Opensearch containers                                                           | `{}`                                                                                     |
| `opensearch.nodeSelector`          | Node labels for Opensearch pods assignment                                                                  | `{}`                                                                                     |

### Redis Configuration Parameters

| Name                                | Description                                                                                  | Value       |
| ----------------------------------- | -------------------------------------------------------------------------------------------- | ----------- |
| `redis.enabled`                     | Enables the Redis deployment                                                                 | `true`      |
| `redis.sentinel.enabled`            | Enables Redis Sentinel on Redis pods                                                         | `false`     |
| `redis.master.count`                | Number of Redis master instances to deploy (experimental, requires additional configuration) | `1`         |
| `redis.master.service.type`         | Redis master service type                                                                    | `ClusterIP` |
| `redis.master.service.ports.redis`  | Redis master service port                                                                    | `6379`      |
| `redis.master.persistence.size`     | Redis master Persistent Volume size                                                          | `8Gi`       |
| `redis.master.resources.limits`     | The resources limits for the Redis master containers                                         | `{}`        |
| `redis.master.resources.requests`   | The requested resources for the Redis master containers                                      | `{}`        |
| `redis.replica.replicaCount`        | Number of Redis replicas to deploy                                                           | `0`         |
| `redis.replica.service.type`        | Redis replicas service type                                                                  | `ClusterIP` |
| `redis.replica.service.ports.redis` | Redis replicas service port                                                                  | `6379`      |
| `redis.replica.persistence.size`    | Redis replica Persistent Volume size                                                         | `8Gi`       |
| `redis.replica.resources.limits`    | The resources limits for the Redis replica containers                                        | `{}`        |
| `redis.replica.resources.requests`  | The requested resources for the Redis replica containers                                     | `{}`        |

### Postgresql Configuration Parameters

| Name                                               | Description                                                                 | Value        |
| -------------------------------------------------- | --------------------------------------------------------------------------- | ------------ |
| `postgresql.enabled`                               | Enables the Postgresql deployment                                           | `true`       |
| `postgresql.architecture`                          | PostgreSQL architecture (`standalone` or `replication`)                     | `standalone` |
| `postgresql.auth.username`                         | Name for a custom PostgreSQL user to create                                 | `postgres`   |
| `postgresql.auth.database`                         | Name for a custom PostgreSQL database to create (overrides `auth.database`) | `timesketch` |
| `postgresql.primary.service.type`                  | PostgreSQL primary service type                                             | `ClusterIP`  |
| `postgresql.primary.service.ports.postgresql`      | PostgreSQL primary service port                                             | `5432`       |
| `postgresql.primary.persistence.size`              | PostgreSQL Persistent Volume size                                           | `8Gi`        |
| `postgresql.primary.resources.limits`              | The resources limits for the PostgreSQL primary containers                  | `{}`         |
| `postgresql.primary.resources.requests`            | The requested resources for the PostgreSQL primary containers               | `{}`         |
| `postgresql.readReplicas.replicaCount`             | Number of PostgreSQL read only replicas                                     | `0`          |
| `postgresql.readReplicas.service.type`             | PostgreSQL read replicas service type                                       | `ClusterIP`  |
| `postgresql.readReplicas.service.ports.postgresql` | PostgreSQL read replicas service port                                       | `5432`       |
| `postgresql.readReplicas.persistence.size`         | PostgreSQL Persistent Volume size                                           | `8Gi`        |
| `postgresql.readReplicas.resources.limits`         | The resources limits for the PostgreSQL read only containers                | `{}`         |
| `postgresql.readReplicas.resources.requests`       | The requested resources for the PostgreSQL read only containers             | `{}`         |

Specify each parameter using the --set key=value[,key=value] argument to helm install. For example,

```console
helm install my-release \
    --set metrics.port=9300
    oci://us-docker.pkg.dev/osdfir-registry/osdfir-charts/timesketch
```

The above command updates the Timesketch metrics port to `9300`.


Alternatively, the `values.yaml` file can be directly updated if the Helm chart 
was pulled locally. For example,

```console
helm pull oci://us-docker.pkg.dev/osdfir-registry/osdfir-charts/timesketch --untar
```

Then make changes to the downloaded `values.yaml`. A `configs/` directory containing user-provided Timesketch configs can also be placed at this point to override
the default ones. Once done, install the local chart with the updated values.

```console
helm install my-release ../timesketch
```

Lastly, a YAML file that specifies the values for the parameters can also be provided while installing the chart. For example,

```console
helm install my-release -f newvalues.yaml oci://us-docker.pkg.dev/osdfir-registry/osdfir-charts/timesketch
```
## Persistence

The Timesketch deployment stores data at the `/mnt/timesketchvolume` path of the container and stores configuration files
at the `/etc/timesketch` path of the container. 

Persistent Volume Claims are used to keep the data across deployments. By default the Timesketch deployment attempts to use dynamic persistent volume provisioning to automatically configure storage, but the `persistent.storageClass` value can be updated to a storageClass supported by your provider. See the [Parameters](#parameters) section to configure the PVC or to disable persistence.

To install the Timesketch chart with more storage capacity, run:
```console
helm install my-release \
    --set persistence.size=10T
    oci://us-docker.pkg.dev/osdfir-registry/osdfir-charts/timesketch
```

The above command installs the Timesketch chart with a persistent volume size of 10 Terabytes.

## Upgrading

If you need to upgrade an existing release to update a value in, such as
persistent volume size or upgrading to a new release, you can run 
[helm upgrade](https://helm.sh/docs/helm/helm_upgrade/). For example,
e, to set a new release and upgrade storage capacity, run:
```console
helm upgrade my-release \
    --set image.tag=latest
    --set persistence.size=10T
```

The above command upgrades an existing release named `my-release` updating the
image tag to `latest` and increasing persistent volume size of an existing volume
to 10 Terabytes

## Troubleshooting

There is a known issue causing PostgreSQL authentication to fail. This occurs 
when you `delete` the deployed Helm chart and then redeploy the Chart without
removing the existing PVCs. When redeploying, please ensure to delete the underlying 
PostgreSQL PVC. Refer to [issue 2061](https://github.com/bitnami/charts/issues/2061) 
for more details.

## License

Copyright &copy; 2023 Timesketch

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.