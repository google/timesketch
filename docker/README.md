# Docker

Timesketch has support for Docker. This is a convenient way of getting up and running.

### Install Docker
Follow the official instructions [here](https://www.docker.com/community-edition)

### Install Docker Compose
Follow the official instructions [here](https://docs.docker.com/compose/install/)

### Clone Timesketch

```shell
git clone https://github.com/google/timesketch.git
cd timesketch
```
### Build and Start Containers

```shell
cd docker
sudo docker-compose up
```

### Access Timesketch
* Retrieve the randomly generated password from startup logs: `TIMESKETCH_PASSWORD set randomly to: xxx`
* Go to: http://127.0.0.1/
* Login with username: admin and the retrieved random password

### Test your installation
1. You can now create your first sketch by pressing the green button on the middle of the page
2. Add the test timeline under the [Timeline](http://127.0.0.1:5000/sketch/1/timelines/) tab in your new sketch
3. Go to http://127.0.0.1:5000/explore/ and have fun exploring!

### Where is my data stored?
The timesketch docker config is set to write all data to the host filesystem, not the containers.  This is accomplished with docker [volumes](https://docs.docker.com/engine/admin/volumes/volumes/) that map to the following locations:

- elasticsearch: /var/lib/elasticsearch
- neo4j: /var/lib/neo4j/data
- postgres: /var/lib/postgresql
- redis: /var/lib/redis

These locations on the host filesystem can be backed with any storage mechanism to persist sketch data beyond the container lifetimes.
