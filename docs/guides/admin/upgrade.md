---
hide:
  - footer
---
# Upgrade an existing installation

When upgrading Timesketch you might need to migrate the database to use the latest database schema. This is how you do that.

## Backup you database (!)
First you should backup your current database in case something goes wrong in the upgrade process. For PostgreSQL you do the following (Ref: https://www.postgresql.org/docs/9.1/static/backup.html):

```shell
$ sudo -u postgres pg_dump timesketch > ~/timesketch-db.sql
$ sudo -u postgres pg_dumpall > ~/timesketch-db-all.sql
```

## Change to your Timesketch installation directory
(e.g. /opt/timesketch)

```shell
$ cd /<PATH TO TIMESKETCH INSTALLATION>
```

## Upgrade the database schema
Have you backed up your database..? good. Let's upgrade the schema. First connect to the timesketch-web container:

```shell
$ docker compose exec timesketch-web /bin/bash
```

While connected to the container:

```shell
root@<CONTAINER_ID>$ git clone https://github.com/google/timesketch.git
root@<CONTAINER_ID>$ cd timesketch/timesketch
root@<CONTAINER_ID>$ tsctl db current
```

If this command returns a value, then you can go ahead and upgrade the database.

In case you don't get any response back from the `db current` command you'll need to first find out revisions and fix a spot to upgrade from.

```shell
root@<CONTAINER_ID>$ tsctl db history
```

Find the last revision number you have upgraded the database too, and then issue

```shell
root@<CONTAINER_ID>$ tsctl db stamp <REVISION_ID>
```

And now you are ready to upgrade.

```shell
root@<CONTAINER_ID>$ tsctl db upgrade
```

## Upgrade timesketch
Exit from the container (CTRL-D), then pull new versions of the docker images and upgrade Timesketch:

```shell
$ docker compose pull
$ docker compose down
$ docker compose up -d
```
