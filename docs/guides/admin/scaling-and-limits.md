---
hide:
  - footer
---
# Sizing and limitations

Timesketch is designed to scale.

The minimum system requirements are:

- Machine with Ubuntu 20.04 installed.
- At least 8GB RAM, but more the better.
- Optional: Domain name registered and configure for the machine if you want to setup SSL for the webserver.

These are the limitations:

- Disk size: You can't save larger indexes than the physical hard disk space.

## OpenSearch indices limitation

In the past, every timeline in a sketch was a dedicated OpenSearch Index. In larger installations, Timesketch hit the number of maximum open shards OpenSearch could handle.
Therefore a design [https://github.com/google/timesketch/issues/1567](change) was made to tackle those limitations

- There are maximum number (1500) of shards that can be opened.
- There are limitations with Lucene (which OpenSearch uses) and then OpenSearch itself, see https://www.elastic.co/guide/en/app-search/current/limits.html and maximum sizes of HTTP requests, hence when Timesketch uploads files they are split up, to avoid HTTP limitations.

Using the `timesketch_importer` the system can be forced to create a dedicated index:

```bash
timesketch_importer.py path_to_my_file.plaso --data_label foobar
```

For the first and

```bash
timesketch_importer.py path_to_my_file2.plaso --data_label foobar2
```

For the second one will create two different ES indices.

Be careful if number of indices in a Timeline is >150, searches across that Sketch will be impossible due to a to the resulting large HTTP response.

To learn more about those limitations: https://www.elastic.co/de/blog/how-many-shards-should-i-have-in-my-elasticsearch-cluster

## Scaling

### Hardware

The following points are important to increase the performance of a Timesketch system

- Fast local storage
- Memory, the more the better

### OpenSearch

The first thing to scale will be your OpenSearch cluster.

With a decent OpenSearch deployment you can have hundreds of millions events across many many investigations without issues.

[This article](https://edward-cernera.medium.com/deploy-a-multi-node-elasticsearch-instance-with-docker-compose-ef63625f246e) will give you a good start to scale the OpenSearch cluster. Be careful to not expose your Cluster to systems other then the Timesketch node(s).

The config and credentials to the OpenSearch cluster are stored in https://github.com/google/timesketch/blob/master/data/timesketch.conf. If those calues are changed, the Timesketch Instance needs to be restarted.

### Celery workers

If Celery workers take to long to process, more resources for the host running the workers might a be a first step to eliminate that bottleneck.

### Multi node setup

It is possible to spread a Timesketch installation over multiple nodes. This is mostly to improve reliability and data security then speed, but it might also speed up.

A potential 3 node (dedicated machines) setup could look like the following:

```
timesketch-1:
OpenSearch
Redis
PostgreSQL 11.x
Docker: Timesketch Web
Docker: Timesketch Worker

timesketch-2:
OpenSearch
Docker: Timesketch Worker

timesketch-3:
OpenSearch
Docker: Timesketch Worker
```

All nodes need connections to each other and the Docker containers need permission to also use network.
