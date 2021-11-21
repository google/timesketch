# Sizing and limitations

Timesketch is designed to scale.

The minimum system requirements are:

- Machine with Ubuntu 20.04 installed.
- At least 8GB RAM, but more the better.
- Optional: Domain name registered and configure for the machine if you want to setup SSL for the webserver.

These are the limitations:

- Disk size: You can't save larger indexes than the physical hard disk space.

## Elastic indices limitation

In the past, every timeline in a sketch was a dedicated ElasticSearch Index. In larger installations, Timesketch hit the number of maximum open shards Elastic could handle.
Therefor a design [https://github.com/google/timesketch/issues/1567](change) was made to tackle those limitations

- There are maximum number (1500) of shards that can be opened.
- There are limitations with Lucene (which Elastic uses) and then Elastic itself, see https://www.elastic.co/guide/en/app-search/current/limits.html and maximum sizes of HTTP requests, hence when Timesketch uploads files they are split up, to avoid HTTP limitations.

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

### ElasticSearch

The first thing to scale will be your ES cluster.

With a decent Elasticsearch deployment you can have hundreds of millions events across many many investigations without issues.

[This article](https://edward-cernera.medium.com/deploy-a-multi-node-elasticsearch-instance-with-docker-compose-ef63625f246e) will give you a good start to scale the ElasticSearch cluster. Be careful to not expose your Cluster to systems other then the Timesketch node(s).

The config and credentials to the ElasticSearch cluster are stored in https://github.com/google/timesketch/blob/master/data/timesketch.conf. If those calues are changed, the Timesketch Instance needs to be restarted.

### Celery workers

If Celery workers take to long to process, more ressources for the host running the workers might a be a first step to eliminate that bottleneck.
