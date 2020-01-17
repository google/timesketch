# Upgrade an existing Timesketch installation

When upgrading Timesketch you might need to migrate the database to use the latest database schema. This is how you do that.

## Backup you database (!)
First you should backup your current database in case something goes wrong in the upgrade process. For PostgreSQL you do the following (Ref: https://www.postgresql.org/docs/9.1/static/backup.html):

    $ sudo -u postgres pg_dump timesketch > ~/timesketch-db.sql
    $ sudo -u postgres pg_dumpall > ~/timesketch-db-all.sql

## Upgrade timesketch

    $ pip3 install timesketch --upgrade

Or, if you are installing from the master branch:

    $ git clone https://github.com/google/timesketch.git
    $ cd timesketch
    $ pip3 install . --upgrade

## Upgrade the database schema
Have you backed up your database..? good. Let's upgrade the schema:

    $ git clone https://github.com/google/timesketch.git
    $ cd timesketch/timesketch
    $ tsctl db upgrade

