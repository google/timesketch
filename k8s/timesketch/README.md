<!--- app-name: Timesketch -->
# Timesketch

A Helm chart for Timesketch. Timesketch is an open-source tool for collaborative forensic timeline analysis. Using sketches you and your collaborators can easily organize your timelines and analyze them all at the same time. Add meaning to your raw data with rich annotations, comments, tags and stars.

[Overview of Timesketch](http://www.timesketch.org)

## TL;DR

```console
helm install my-release oci://us-docker.pkg.dev/osdfir-registry/osdfir-charts/timesketch
```

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
helm pull my-release oci://us-docker.pkg.dev/osdfir-registry/osdfir-charts/timesketch
```

To install the chart from a local repo with the release name `my-release`:
```console
helm install my-release ../timesketch
```

The install command deploys Timesketch on the Kubernetes cluster in the default configuration. The [Parameters](#parameters) section lists the parameters that can be configured during installation.

> **Tip**:  You can override the default Timesketch configuration by placing a `configs/` directory containing the user-provided configs at the root of the Helm chart. When choosing this option, be sure to pull and install the Helm chart locally.

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

### Timesketch image configuration

| Name                     | Description                                                   | Value                                                     |
| ------------------------ | ------------------------------------------------------------- | --------------------------------------------------------- |
| `image.repository`       | Timesketch image repository                                   | `us-docker.pkg.dev/osdfir-registry/timesketch/timesketch` |
| `image.pullPolicy`       | Timesketch image pull policy                                  | `IfNotPresent`                                            |
| `image.tag`              | Overrides the image tag whose default is the chart appVersion | `latest`                                                  |
| `image.imagePullSecrets` | Specify secrets if pulling from a private repository          | `[]`                                                      |

### Timesketch Configuration Parameters

| Name              | Description                                                                                                                           | Value       |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| `config.override` | Overrides the default Timesketch configs to instead use a user specified directory if present on the root directory of the Helm chart | `configs/*` |

### Timesketch Frontend Configuration

| Name                                 | Description                                                                 | Value     |
| ------------------------------------ | --------------------------------------------------------------------------- | --------- |
| `frontend.podSecurityContext`        | Holds pod-level security attributes and common frontend container settings  | `{}`      |
| `frontend.securityContext`           | Holds security configuration that will be applied to the frontend container | `{}`      |
| `frontend.resources.requests.cpu`    | Requested cpu for the frontend container                                    | `2000m`   |
| `frontend.resources.requests.memory` | Requested memory for the frontend container                                 | `4000Mi`  |
| `frontend.resources.limits.cpu`      | Resource cpu limits for the frontend container                              | `8000m`   |
| `frontend.resources.limits.memory`   | Resource memory limits for the frontend container                           | `16000Mi` |
| `frontend.nodeSelector`              | Node labels for Timesketch frontend pods assignment                         | `{}`      |
| `frontend.tolerations`               | Tolerations for Timesketch frontend pods assignment                         | `[]`      |
| `frontend.affinity`                  | Affinity for Timesketch frontend pods assignment                            | `{}`      |

### Timesketch Worker Configuration

| Name                               | Description                                                               | Value     |
| ---------------------------------- | ------------------------------------------------------------------------- | --------- |
| `worker.podSecurityContext`        | Holds pod-level security attributes and common worker container settings  | `{}`      |
| `worker.securityContext`           | Holds security configuration that will be applied to the worker container | `{}`      |
| `worker.resources.requests.cpu`    | Requested cpu for the worker container                                    | `2000m`   |
| `worker.resources.requests.memory` | Requested memory for the worker container                                 | `4000Mi`  |
| `worker.resources.limits.cpu`      | Resource cpu limits for the worker container                              | `8000m`   |
| `worker.resources.limits.memory`   | Resource memory limits for the worker container                           | `16000Mi` |
| `worker.nodeSelector`              | Node labels for Timesketch worker pods assignment                         | `{}`      |
| `worker.tolerations`               | Tolerations for Timesketch worker pods assignment                         | `[]`      |
| `worker.affinity`                  | Affinity for Timesketch worker pods assignment                            | `{}`      |

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
| `persistence.size`                | Timesketch persistent volume size                                                                 | `1T`                |
| `persistence.storageClass`        | PVC Storage Class for Timesketch volume                                                           | `standard-rwx`      |
| `persistence.accessModes`         | PVC Access Mode for Timesketch volume                                                             | `["ReadWriteMany"]` |
| `ingress.enabled`                 | Enable the Timesketch loadbalancer for external access                                            | `false`             |
| `ingress.host`                    | Domain name Timesketch will be hosted under                                                       | `""`                |
| `ingress.className`               | IngressClass that will be be used to implement the Ingress                                        | `gce`               |
| `ingress.gcp.managedCertificates` | Enables GCP managed certificates for your domain                                                  | `false`             |
| `ingress.gcp.staticIPName`        | Name of the static IP address you reserved in GCP. Required when using "gce" in ingress.className | `""`                |

### Third Party Configuration


### Opensearch Configuration Parameters

| Name                                   | Description                                                                                                 | Value                                                                                    |
| -------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `opensearch.enabled`                   | Enables the Opensearch deployment                                                                           | `true`                                                                                   |
| `opensearch.config.opensearch.yml`     | Opensearch configuration file. Can be appended for additional configuration options                         | `{"opensearch.yml":"plugins:\n  security:\n    allow_unsafe_democertificates: false\n"}` |
| `opensearch.extraEnvs[0].name`         | Environment variable to disable Opensearch Demo config                                                      | `DISABLE_INSTALL_DEMO_CONFIG`                                                            |
| `opensearch.extraEnvs[0].value`        | Disables Opensearch Demo config                                                                             | `true`                                                                                   |
| `opensearch.extraEnvs[1].name`         | Environment variable to disable Opensearch Security plugin given that                                       | `DISABLE_SECURITY_PLUGIN`                                                                |
| `opensearch.extraEnvs[1].value`        | Disables Opensearch Security plugin                                                                         | `true`                                                                                   |
| `opensearch.replicas`                  | Number of Opensearch instances to deploy                                                                    | `3`                                                                                      |
| `opensearch.sysctlInit.enabled`        | Sets optimal sysctl's through privileged initContainer                                                      | `true`                                                                                   |
| `opensearch.opensearchJavaOpts`        | Sets the size of the Opensearch Java heap                                                                   | `-Xms32g -Xmx32g`                                                                        |
| `opensearch.httpPort`                  | Opensearch service port                                                                                     | `9200`                                                                                   |
| `opensearch.persistence.size`          | Opensearch Persistent Volume size. A persistent volume would be created for each Opensearch replica running | `1Ti`                                                                                    |
| `opensearch.resources.requests.cpu`    | Requested cpu for the Opensearch containers                                                                 | `8000m`                                                                                  |
| `opensearch.resources.requests.memory` | Requested memory for the Opensearch containers                                                              | `32Gi`                                                                                   |
| `opensearch.nodeSelector`              | Node labels for Opensearch pods assignment                                                                  | `{}`                                                                                     |

### Redis Configuration Parameters

| Name                                      | Description                                                                                  | Value       |
| ----------------------------------------- | -------------------------------------------------------------------------------------------- | ----------- |
| `redis.enabled`                           | Enables the Redis deployment                                                                 | `true`      |
| `redis.sentinel.enabled`                  | Enables Redis Sentinel on Redis pods                                                         | `false`     |
| `redis.master.count`                      | Number of Redis master instances to deploy (experimental, requires additional configuration) | `1`         |
| `redis.master.service.type`               | Redis master service type                                                                    | `ClusterIP` |
| `redis.master.service.ports.redis`        | Redis master service port                                                                    | `6379`      |
| `redis.master.persistence.size`           | Redis master Persistent Volume size                                                          | `8Gi`       |
| `redis.master.resources.requests.cpu`     | Requested cpu for the Redis master containers                                                | `4000m`     |
| `redis.master.resources.requests.memory`  | Requested memory for the Redis master containers                                             | `8Gi`       |
| `redis.master.resources.limits.cpu`       | Resource cpu limits for the Redis master containers                                          | `8000m`     |
| `redis.master.resources.limits.memory`    | Resource memory limits for the Redis master containers                                       | `16Gi`      |
| `redis.replica.replicaCount`              | Number of Redis replicas to deploy                                                           | `3`         |
| `redis.replica.service.type`              | Redis replicas service type                                                                  | `ClusterIP` |
| `redis.replica.service.ports.redis`       | Redis replicas service port                                                                  | `6379`      |
| `redis.replica.persistence.size`          | Redis replica Persistent Volume size                                                         | `8Gi`       |
| `redis.replica.resources.requests.cpu`    | Requested cpu for the Redis replica containers                                               | `4000m`     |
| `redis.replica.resources.requests.memory` | Requested memory for the Redis replica containers                                            | `8Gi`       |
| `redis.replica.resources.limits.cpu`      | Resource cpu limits for the Redis replica containers                                         | `8000m`     |
| `redis.replica.resources.limits.memory`   | Resource memory limits for the Redis replica containers                                      | `16Gi`      |

### Postgresql Configuration Parameters

| Name                                                | Description                                                                 | Value        |
| --------------------------------------------------- | --------------------------------------------------------------------------- | ------------ |
| `postgresql.enabled`                                | Enables the Postgresql deployment                                           | `true`       |
| `postgresql.architecture`                           | PostgreSQL architecture (`standalone` or `replication`)                     | `standalone` |
| `postgresql.auth.username`                          | Name for a custom PostgreSQL user to create                                 | `postgres`   |
| `postgresql.auth.database`                          | Name for a custom PostgreSQL database to create (overrides `auth.database`) | `timesketch` |
| `postgresql.primary.service.type`                   | PostgreSQL primary service type                                             | `ClusterIP`  |
| `postgresql.primary.service.ports.postgresql`       | PostgreSQL primary service port                                             | `5432`       |
| `postgresql.primary.persistence.size`               | PostgreSQL Persistent Volume size                                           | `8Gi`        |
| `postgresql.primary.resources.requests.cpu`         | Requested cpu for the PostgreSQL Primary containers                         | `250m`       |
| `postgresql.primary.resources.requests.memory`      | Requested memory for the PostgreSQL Primary containers                      | `256Mi`      |
| `postgresql.primary.resources.limits`               | Resource limits for the PostgreSQL Primary containers                       | `{}`         |
| `postgresql.readReplicas.replicaCount`              | Number of PostgreSQL read only replicas                                     | `1`          |
| `postgresql.readReplicas.service.type`              | PostgreSQL read replicas service type                                       | `ClusterIP`  |
| `postgresql.readReplicas.service.ports.postgresql`  | PostgreSQL read replicas service port                                       | `5432`       |
| `postgresql.readReplicas.persistence.size`          | PostgreSQL Persistent Volume size                                           | `8Gi`        |
| `postgresql.readReplicas.resources.requests.cpu`    | Requested cpu for the PostgreSQL read only containers                       | `250m`       |
| `postgresql.readReplicas.resources.requests.memory` | Requested memory for the PostgreSQL read only containers                    | `256Mi`      |
| `postgresql.readReplicas.resources.limits`          | Resource limits for the PostgreSQL read only containers                     | `{}`         |
