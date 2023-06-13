---
hide:
  - footer
---
# Timesketch Notebook

The Timesketch notebook is a docker container that runs a customized version
of [picatrix](https://github.com/google/picatrix), designed to assist analysts
using Timesketch.

## Installation

The notebook is a docker container, so the first step is to make sure that
[docker is installed](https://docs.docker.com/engine/install/).

If you did not install the docker desktop app you may also need to install
`docker-compose-plugin`, please follow the instructions
[here](https://docs.docker.com/compose/install/) (the version that is often
included in your source repo might be too old to properly setup the container).

After installing docker the next step is to create a docker compose file, which
is used to bootstrap the docker commands.

Save the following content to a file called `docker-compose.yml`:

```
version: '3'
services:
  notebook:
    container_name: notebook
    image: us-docker.pkg.dev/osdfir-registry/timesketch/notebook:latest
    ports:
      - 127.0.0.1:8844:8844
    restart: on-failure
    volumes:
      - FOLDER_PATH:/usr/local/src/picadata/
```

Replace the text `FOLDER_PATH` with a folder that can survive reboots. This is
the path to the folder where all notebooks will be saved to. The folder needs
to be readable and writeable by a user with uid/gid 1000:1000 (if this is run
on a Windows system the `FOLDER_PATH` can be set to something like
`C:\My Folder\`)

Once the file has been saved, docker compose can be used to pull and start
the container:

```shell
$ sudo docker compose pull
$ sudo docker compose up -d
```

The docker compose command will download the latest build and deploy the
TS docker container.


## Access the Container

To be able to connect to the notebook connect to
[http://localhost:8844](http://localhost:8844), the password to access
the notebook is `timesketch`.

### Troubleshooting Container

In case there are any issues with the container it can be useful to take
a look at the container logs, which may give you hints into what may
be the issue.

```shell
$ sudo docker container logs notebook
```

**TODO**: Complete this section.

## Upgrade Container

To update the container, use:

```shell
$ sudo docker compose pull
$ sudo docker compose stop
$ sudo docker compose up -d
```

## Docker Desktop

If you are using Docker desktop you can find the docker image, click
on the three dots and select pull.

After manually updating the image the container needs to be recreated (using
the docker compose up command used earlier).

## Credentials

The docker container will have default credentials and configuration to connect
to the development server running in a container on the localhost, using the
user/pass combination of dev/dev.

To connect to a different server, few options are available:

1. Copy ~/.timesketchrc and ~/.timesketch.token to the docker using `docker cp`.
2. Run `ts_client = config.get_client(confirm_choices=True) and change all
values as questions come up.
3. Create a separate session using
```python
ts_client = config.get_client(config_section='myserver')
```
4. The other option is to connect to the docker container:
```shell
$ sudo docker exec -it notebook /bin/bash
```

And manually craft the ~/.timesketchrc file.

## Connect To Colab

In order to connect to the docker container from colab, select the arrow
next to the `Connect` button, select `Connect to local runtime` and type
in the URL `http://localhost:8844/?token=timesketch` into the `Backend URL`
field and hit `CONNECT`.

## Usage

**TODO**: This section needs to be filled in.

However in the meantime these sites can be of an assistance:

+ [Discussion thread about the container](https://github.com/google/timesketch/discussions/1515)
+ [Beginners guide of Jupyter](https://www.dataquest.io/blog/jupyter-notebook-tutorial/)
+ [Test notebook](https://colab.research.google.com/github/google/timesketch/blob/master/notebooks/colab-timesketch-demo.ipynb)
+ [Jupyter tutorial](https://www.datacamp.com/community/tutorials/tutorial-jupyter-notebook)
