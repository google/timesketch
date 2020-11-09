# Install Timesketch with Docker

#### Overview
Guide on how to install Timesketch using Docker. Docker images are automatically built whenever the main branch is updated or a new release is tagged.

You will need:
* Machine with Ubuntu 20.04 installed.
* At least 8GB RAM, but more the better.
* Domain name registered and configure for the machine (for SSL)

This guide setup the following services:
* Timesketch server
* Timesketch importer/analysis worker
* PostgreSQL
* Elasticsearch
* Redis
* Nginx

NOTE: This guide sets up  single node Elasticsearch cluster. This is OK for smaller installations but in order to scale and have better performance you need to setup a multi node Elasticsearch cluster. This is out of scope for this guide but the official documentation will get you started:
https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html  

#### 1. Install Docker

Follow the official installation instructions for Docker on Ubuntu:
https://docs.docker.com/engine/install/ubuntu/ 

#### 2. Install docker-compose
    
```shell
    $ sudo apt-get install docker-compose
```

#### 3. Download deployment helper script
We have created a helper script to get you started with all necessary configuration.
Download the script here:

```shell
    $ curl -s -O https://raw.githubusercontent.com/google/timesketch/master/contrib/deploy_timesketch.sh
    $ chmod 755 deploy_timesketch.sh
```

#### 4. Choose location for Timesketch data
You can choose to host the Timeksetch data directory anywhere but note that by default it will host Elasticsearch and PostgreSQL data in this directory so make sure you have enough disk space available.

Example:

```shell    
    $ cd /opt
```

#### 5. Run deployment script

```shell
    $ sudo ~/deploy_timesketch.sh
```    
    
Example output:

    * Setting vm.max_map_count for Elasticsearch
    * Setting default config parameters..OK
    * Setting Elasticsearch memory allocation to 8GB
    * Fetching configuration files..OK
    * Edit configuration files..OK
    * Installation done.

#### 6. Start the system

```shell
    $ cd timesketch
    $ sudo docker-compose up -d
```

#### 7. Create the first user

```shell
    $ sudo docker-compose exec timesketch-web tsctl add_user --username <USERNAME>
```

#### 8. Enable TLS
It is out of scope for the deployment script to setup certificates but here are pointers on how to use Let's Encrypt.

1. You need to configure a DNS name for the server. Use your DNS provider instructions.
2. Make sure your webserver is reachable on port 80.
3. Follow the official guide to install and run Let's Encrypt on Ubuntu:
https://certbot.eff.org/lets-encrypt/ubuntufocal-other

When Let's Encrypt has been installed and you have generated certificates (located in /etc/letsencrypt) it is time to reconfigure Nginx.

Edit timesketch/etc/nginx.conf (HOSTNAME is the DNS name of your server):

```
    events {
            worker_connections 768;
    }
    
    http {
        server {
          listen 80;
          listen [::]:80;
          listen 443 ssl;
          ssl_certificate /etc/letsencrypt/live/<HOSTNAME>>/fullchain.pem;
          ssl_certificate_key /etc/letsencrypt/live/<HOSTNAME>>/privkey.pem;
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

Make the certificate and key available to the Nginx Docker container. Edit timesketch/docker-compose.yml and mount /etc/letsencrypt:

```
    ...

    nginx:
      image: nginx:${NGINX_VERSION}
      restart: always
      ports:
        - "80:80"
        - "443:443"
      volumes:
        - ./etc/nginx.conf:/etc/nginx/nginx.conf
        - /etc/letsencrypt:/etc/letsencrypt/
```

Restart the system:

```shell
    # docker-compose down
    # docker-compose up -d
 ```
 
Congratulations, your Timesketch system is operational and ready to use. 

    https://<HOSTNAME>
