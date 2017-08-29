# Enable Plaso upload via HTTP

To enable uploading and processing of Plaso storage files, there are a couple of things to do.

**Install Plaso**

NOTE: Due to changes in the format of the Plaso storage file you need to run the latest version of Plaso (>=1.5.0).

Following the official Plaso documentation:
https://github.com/log2timeline/plaso/wiki/Ubuntu-Packaged-Release

    $ sudo add-apt-repository universe
    $ sudo add-apt-repository ppa:gift/stable
    $ sudo apt-get update
    $ sudo apt-get install python-plaso

**Install Redis**

    $ sudo apt-get install redis-server

**Configure Timesketch** (/etc/timesketch.conf)

    UPLOAD_ENABLED = True
    UPLOAD_FOLDER = u'/path/to/where/timesketch/can/write/files'
    CELERY_BROKER_URL='redis://127.0.0.1:6379',
    CELERY_RESULT_BACKEND='redis://127.0.0.1:6379'

**Run a Celery worker process**

    $ celery -A timesketch.lib.tasks worker --loglevel=info

Read on how to run the Celery worker in the background over at the [official Celery documentation](http://celery.readthedocs.org/en/latest/tutorials/daemonizing.html#daemonizing).
