# Upgrade an existing Timesketch installation

When upgrading Timesketch you might need to migrate the database to use the latest database schema. This is how you do that.

## Backup you database (!)
First you should backup your current database in case something goes wrong in the upgrade process. For PostgreSQL you do the following (Ref: https://www.postgresql.org/docs/9.1/static/backup.html):

    $ sudo -u postgres pg_dump timesketch > ~/timesketch-db.sql
    $ sudo -u postgres pg_dumpall > ~/timesketch-db-all.sql


## Change to your Timesketch installation directory
(e.g. /opt/timesketch)

    $ cd /<PATH TO TIMESKETCH INSTALLATION>
## Upgrade the database schema
Have you backed up your database..? good. Let's upgrade the schema. First connect to the timesketch-web container:

    $ docker-compose exec timesketch-web /bin/bash

While connected to the container:
    
    $ root@<CONTAINER_ID>$ git clone https://github.com/google/timesketch.git
    root@<CONTAINER_ID>$ cd timesketch/timesketch
    root@<CONTAINER_ID>$ tsctl db stamp head
    root@<CONTAINER_ID>$ tsctl db upgrade 

## Upgrade timesketch
Exit from the container (CTRL-D), then pull new versions of the docker images and upgrade Timesketch:
    
    $ docker-compose pull
    $ docker-compose down
    $ docker-compose up -d

