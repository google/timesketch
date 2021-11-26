## Troubleshooting playbook

- Is it only affecting one user?
- Is it only affecting one sketch / timeline?
- Can the issue be reproduced on demo.timesketch.org?
- Can the issue be reproduced on a different device / clear caches from browser?
- Any errors in Chrome console for any javascript errors or failed HTTP requests
- Any errors in nginx / webserver logs?
- Any errors in Timesketch / celery worker logs
- Any errors in ES logs?
- Any errors in postgres logs?

## Frontend issues

To troubleshoot web frontend issues, the first look should go to the Chrome developer console and look for any output / errors.

To raise issues related to the web frontend, please provide the following:

- Copy out the full error message(s) from Chrome Console
- The URL (without your local IP or Domain)
- What was clicked before it happend
- Any entries in the server side logs (see below)?
- Share a screenshot if possible
- If possible details about the event / sketch
  - Was it an imported Plaso file or CSV or JSONL?
  - Was the data imported via Web or API client?

## Docker

To list all your running Docker containers, run:

```shell
docker container list
```

Which will show something like

```shell
b756f334d281   us-docker.pkg.dev/osdfir-registry/timesketch/dev:latest        "/docker-entrypoint.…"   8 days ago   Up 2 days   127.0.0.1:5000->5000/tcp             timesketch-dev
7768635b4798   us-docker.pkg.dev/osdfir-registry/timesketch/notebook:latest   "jupyter notebook"       8 days ago   Up 2 days   127.0.0.1:8844->8844/tcp, 8899/tcp   notebook
51a576407ad2   docker.elastic.co/elasticsearch/elasticsearch-oss:7.10.2       "/tini -- /usr/local…"   8 days ago   Up 2 days   9200/tcp, 9300/tcp                   elasticsearch
bf85b40ed003   redis:6.0.10-alpine                                            "docker-entrypoint.s…"   8 days ago   Up 2 days   6379/tcp                             redis
f78f8b1f13d1   postgres:13.1-alpine                                           "docker-entrypoint.s…"   8 days ago   Up 2 days   5432/tcp                             postgres
```

If one of these is not up, you might need to troubleshoot docker.

## Troubleshooting Database Schema Changes

See [docs/learn/server-admin](docs/learn/server-admin#troubleshooting-database-schema-changes)

## Import issues

- Is the celery worker running?
- Have a look at the celery logs.
- Is it a specific file that causes problems?
- What is the WebUI status of the import?
- Try switching from WebUI to the `import_client.py` to upload the same file
- Try to upload one of the [sample files](https://github.com/google/timesketch/blob/master/test_tools/test_events/sigma_events.csv)
- If you open a Github issue for an import issue, please indicate, what type of file you try to upload and what error message / stacktrace you have

### Issues importing a CSV file

- What are the headers of the CSV files
- Have the headers of the CSV file the minimum headers
- Is there an encoding issue in the CSV file
- If you tried to upload via web, try the import client and the other way around
- Check the celery logs
- Try to upload [This sample](https://github.com/google/timesketch/blob/master/test_tools/test_events/sigma_events.csv)
- If you open a Github issue, provide at least the header of your CSV and a few lines of content (please scramble PII) so it can be reproduced.

### Issues importing Plaso file

- Which Plaso version is installed on the Timesketch server?
- Which Plaso version was used to create the Plaso file?
- Is the issue for both web upload and `import_client`?
- If you open a Github Issue, please indicate the Plaso version used to generate the file.

Try to run the following in the Docker container after the file was uploaded (but not successfully imported):

```shell
pinfo.py $FILENAME
```

Should give the following error message:

```shell
2020-08-19 14:40:48,912 [ERROR] (MainProcess) PID:568 <pinfo_tool> Format of storage file: $FILENAME not supported
```

## Logs

All of those are subject to change depending on your operating system.

### Nginx / webserver

```shell
/var/log/nginx/access
```

Good starter is to run the following grep:

```shell
grep "http_code:500" /var/log/nginx/access.log  # to get all Error 500
```

If you started the webserver with docker, look in the console where you started:

```shell
docker exec -it $CONTAINER_ID gunicorn --reload -b 0.0.0.0:5000 --log-file --timeout 600 timesketch.wsgi:application
```

Or run the following where `$CONTAINER_ID` is the ID from your `timesketch-dev` or `timesketch` Docker container.

```shell
docker logs $CONTAINER_ID
```

### Timesketch / Celery worker

See your console output if you started the workers with:

```shell
docker exec -it $CONTAINER_ID celery -A timesketch.lib.tasks worker --loglevel=debug
```

It is possible to see current running jobs with:

```shell
docker exec -it $CONTAINER_ID celery -A timesketch.lib.tasks inspect active
```

Which will give a list of tasks, individual tasks that are running can be then checked with
```shell
docker exec -it $CONTAINER_ID celery -A timesketch.lib.tasks inspect query_task $TASKID
```

Where $TASKID is the id that was shown in the previous step.

### Elasticsearch

```shell
/var/log/elasticsearch
```

Or run the following where `$CONTAINER_ID` is the ID from your `elasticsearch` Docker container.

```shell
docker logs $CONTAINER_ID
```

### Postgress

```shell
/var/log/postgresql/
```

Or run the following where `$CONTAINER_ID` is the ID from your `postgres` Docker container.

```shell
docker logs $CONTAINER_ID
```

## CSRF token expire

You can edit `/etc/timesketch/timesketch.conf` and add:

```
WTF_CSRF_TIME_LIMIT = 1234 # seconds or "None" to never expire.
```

The default is 3600s.

Restart the webserver and the new value is used.
