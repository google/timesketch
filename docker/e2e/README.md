# Docker for e2e tests

Timesketch has support for Docker. This is a convenient way of getting up and running.
NOTE: Windows based host systems are not supported at this time.

## Install Docker

Follow the official instructions [here](https://www.docker.com/community-edition)

## Install Docker Compose

Follow the official instructions [here](https://docs.docker.com/compose/install/)

## Clone Timesketch

```shell
git clone https://github.com/google/timesketch.git
cd timesketch
```

## Verify the Kernel Settings

Follow the official instructions [here](https://www.elastic.co/guide/en/elasticsearch/reference/6.4/docker.html#docker-cli-run-prod-mode)

## Build and Start Containers

```shell
cd docker/e2e
sudo docker compose up
```

## Access Timesketch

* Retrieve the randomly generated password from startup logs: `TIMESKETCH_PASSWORD set randomly to: xxx`
* Go to: http://127.0.0.1/
* Login with username: admin and the retrieved random password

## Test your installation

1. You can now create your first sketch by pressing the green button on the middle of the page
2. Add the test timeline under the [Timeline](http://127.0.0.1:5000/sketch/1/timelines/) tab in your new sketch
3. Go to http://127.0.0.1:5000/explore/ and have fun exploring!

## Running Browser UI End-to-End Tests

Browser UI E2E tests (`end_to_end_tests/ui_test.py`) run in an opt-in Playwright
Python sidecar container (`--profile ui`) against the compiled `frontend-ng` SPA
served on port 80 by the `timesketch` container:

```shell
docker compose -f docker/e2e/docker-compose.yml up -d timesketch
docker compose -f docker/e2e/docker-compose.yml --profile ui run --rm -i=false -T ui-e2e \
  python3 /usr/local/src/timesketch/end_to_end_tests/tools/run_in_container.py ui_test
```

For fast ~15-second local UI iteration (running reachability, login, sketch creation,
and the 4-row `sigma_events.csv` upload + live SPA auto-poll + Explore search while
skipping slow Plaso `psort.py` ingestion), pass `-e UI_E2E_SKIP_PLASO=1`:

```shell
docker compose -f docker/e2e/docker-compose.yml --profile ui \
  run --rm -i=false -T -e UI_E2E_SKIP_PLASO=1 ui-e2e \
  python3 /usr/local/src/timesketch/end_to_end_tests/tools/run_in_container.py ui_test
```

Milestone step screenshots and a static HTML storyboard (`/tmp/timesketch-ui-artifacts/steps/index.html`)
are written on every run, and full-page failure screenshots plus Playwright trace
bundles (`.zip`) are saved to `/tmp/timesketch-ui-artifacts` if any assertion fails.

## Where is my data stored?

The timesketch docker config is set to write all data to the host filesystem, not the containers.  This is accomplished with docker [volumes](https://docs.docker.com/engine/admin/volumes/volumes/) that map to the following locations:

* elasticsearch: /var/lib/elasticsearch
* postgres: /var/lib/postgresql
* redis: /var/lib/redis

### Mac

On mac, you can set up the shares as following

```shell
sudo mkdir -p /var/lib/elasticsearch
sudo chown `whoami` /var/lib/elasticsearch
sudo mkdir -p /var/lib/postgresql/data
sudo chown `whoami` /var/lib/postgresql/data
sudo mkdir -p /var/lib/redis
sudo chown `whoami` /var/lib/redis
```

These locations on the host filesystem can be backed with any storage mechanism to persist sketch data beyond the container lifetimes.
