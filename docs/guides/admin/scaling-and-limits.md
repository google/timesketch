# Sizing and limitations

Timesketch is designed to scale.

The minimum system requirements are:

- Machine with Ubuntu 20.04 installed.
- At least 8GB RAM, but more the better.
- Optional: Domain name registered and configure for the machine if you want to setup SSL for the webserver.

These are the limitations:

- Disk size: You can't save larger indexes than the physical hard disk space.
- There are maximum number (1500) of shards that can be opened.
- There are limitations with Lucene (which Elastic uses) and then Elastic itself, see https://www.elastic.co/guide/en/app-search/current/limits.html and maximum sizes of HTTP requests, hence when Timesketch uploads files they are split up, to avoid HTTP limitations.

With a decent Elasticsearch deployment you can have hundreds of millions events across many many investigations without issues.
