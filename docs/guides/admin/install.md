---
hide:
  - footer
---
# Install Timesketch

The preferred way to install Timesketch is to use the provided Docker images. These docker images are automatically built whenever the main branch is updated or a new release is tagged.

It is possible to install Timesketch without docker but we strongly encourage using docker. This is the only tested and actively maintained installation method.

**You will need**

- Machine with Ubuntu 22.04 installed.
- At least 8GB RAM, but the more the better.
- Optional: Domain name registered and configure for the machine if you want to setup SSL for the webserver.

**This guide setup the following services**

- Timesketch web/api server
- Timesketch importer/analysis worker
- PostgreSQL database
- OpenSearch single-node cluster
- Redis key-value database (for worker processes)
- Nginx webserver

**NOTE**: This guide sets up single node OpenSearch cluster. This is OK for smaller installations but in order to scale and have better performance you need to setup a multi node OpenSearch cluster. This is out of scope for this guide but the official documentation on [installing OpenSearch](https://opensearch.org/docs/latest/opensearch/install/index/) will get you started.

### 1. Install Docker

Follow the official installation instructions to [install Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

### 2. Start the installation

#### Download helper script

We have created a helper script to get you started with all necessary configuration.
Download the script here:

```shell
curl -s -O https://raw.githubusercontent.com/google/timesketch/master/contrib/deploy_timesketch.sh
chmod 755 deploy_timesketch.sh
```

#### Choose location for the installation

You can choose to host the Timesketch data directory anywhere but note that by default it will host OpenSearch and PostgreSQL data in this directory so make sure you have enough disk space available.

Example:

```shell
cd /opt
```

#### Run deployment script

```shell
sudo ./deploy_timesketch.sh
```

#### Configure an OpenSearch index prefix (optional)

By default Timesketch names its OpenSearch indices with a random UUID. If
Timesketch shares an OpenSearch cluster with other applications, you can set a
prefix for all indices that Timesketch creates. This makes it possible to
restrict the OpenSearch service account of Timesketch to an index pattern such
as `timesketch-*`.

Set the prefix in `timesketch/etc/timesketch/timesketch.conf`, ideally **before
you start the system for the first time**:

```python
OPENSEARCH_INDEX_PREFIX = "timesketch-"
```

New indices are then named `timesketch-<32 hex characters>`.

* The prefix must be lowercase, start with a letter or digit, only contain
  `[a-z0-9_-]` and be at most 63 characters long. Timesketch refuses to start
  with an invalid prefix.
* **The prefix only applies to indices that are created after it is set.**
  Timesketch does not rename or migrate existing indices. If you set the prefix
  on an existing instance, the existing indices keep their names and keep
  working, as long as the OpenSearch service account can still access them. If
  you restrict the service account to the prefix (e.g. `timesketch-*`), these
  older indices become inaccessible. The web server logs a warning on startup
  and `tsctl info` warns if search indices without the prefix exist.
* Use a unique prefix for every Timesketch instance that shares an OpenSearch
  cluster.
* Timesketch never adds the prefix to index names that clients explicitly
  supply (e.g. via the API or importer).
* Setting up the OpenSearch permissions (roles, index patterns, index templates
  and policies) is done in OpenSearch and is not managed by Timesketch. Give
  the Timesketch service account full access to indices that match the prefix.
  If OpenSearch denies creating an index, Timesketch logs an error and marks
  the upload as failed, or returns a 403 from the API.

### 3. Start the system

```shell
cd timesketch
sudo docker compose up -d
```

### Create the first user

```shell
sudo docker compose exec timesketch-web tsctl create-user <USERNAME>
```

### 4. Enable TLS (optional)

It is out of scope for the deployment script to setup certificates but here are
pointers on how to use Let's Encrypt in a docker deployment.

1. You need to configure a DNS name for the server. Use your DNS providers
instructions.
2. Update your `timesketch/docker-compose.yaml` file. Update the nginx service
and add the certbot service with the following config:
```
  nginx:
    container_name: nginx
    image: nginx:${NGINX_VERSION}
    restart: always
    ports:
      - ${NGINX_HTTP_PORT}:80
      - ${NGINX_HTTPS_PORT}:443
    volumes:
      - ${NGINX_CONFIG_PATH}:/etc/nginx/nginx.conf
      - ./etc/certbot/www/:/var/www/certbot/:ro
      - ./etc/certbot/conf/:/etc/letsencrypt/:ro

  certbot:
    image: certbot/certbot:latest
    volumes:
      - ./etc/certbot/www/:/var/www/certbot/:rw
      - ./etc/certbot/conf/:/etc/letsencrypt/:rw
```
3. Add the following location to your `timesketch/etc/nginx.conf`:
```
location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
```
4. Run certbot with `--dry-run` first. If all goes well, run it again without
the `--dry-run` flag.
```
docker-compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot/ --dry-run -d <HOSTNAME>
```
5. Edit `timesketch/etc/nginx.conf` (HOSTNAME is the DNS name of your server):

```
events {
    worker_connections 768;
}

http {
    server {
      listen 80;
      listen [::]:80;
      listen 443 ssl;
      ssl_certificate /etc/letsencrypt/live/<HOSTNAME>/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/<HOSTNAME>/privkey.pem;
      client_max_body_size 0m;

      location / {
        proxy_buffer_size       128k;
        proxy_buffers           4 256k;
        proxy_busy_buffers_size 256k;
        proxy_pass http://timesketch-web:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
      }
      if ($scheme != "https") {
        return 301 https://$host$request_uri;
      }
    }
}
```
**If you need to use a non-standard port** you can change the
`proxy_set_header Host $host;` to `proxy_set_header Host $http_host;` instead.

Restart the system:

```shell
sudo docker compose down
sudo docker compose up -d
```

Congratulations, your Timesketch system is operational and ready to use.

### Set up users

After system is set up, look at [here](/guides/admin/admin-cli/) to add users.

### Next Steps

For advanced configuration and performance tuning of your OpenSearch indices,
see the [Index Mappings](/guides/admin/index-mappings/) guide.

# Timesketch K8s Installation

Please refer to
[OSDFIR Infrastructure](https://github.com/google/osdfir-infrastructure)
repository for official installation instructions.
