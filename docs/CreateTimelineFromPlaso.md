# Create timeline from Plaso file

You need to run version >= 1.5.0 Plaso on your Timesketch server. See the [official Plaso documentation](https://plaso.readthedocs.io/en/latest/sources/user/Users-Guide.html#installing-the-packaged-release) for installing Plaso and it's dependencies. If you haven't installed Timesketch yet, take a look at the [installation instructions](Installation.md).

When you have working installations of Timesketch and Plaso you can, from the command line, do:

    $ psort.py -o timesketch -h
    Optional arguments for output modules:
      --name NAME           The name of the timeline in Timesketch. Default:
                            hostname if present in the storage file. If no
                            hostname is found then manual input is used.
      --index INDEX         The name of the Elasticsearch index. Default: Generate
                            a random UUID
      --flush_interval FLUSH_INTERVAL
                            The number of events to queue up before sent in bulk
                            to Elasticsearch. Default: 1000

All of the above arguments are optional. If you don't provide a name for your timeline the module will try to extract the hostname from the Plaso storage file and if this fails it will prompt you to enter a name.

So all that is needed is:

    $ psort.py -o timesketch dump.plaso
    [INFO] Timeline name: machine1
    [INFO] Index: 206a36873cc140c1958a7d20fcd14dba
    [INFO] Starting new HTTP connection (1): 192.168.34.19
    [INFO] Adding events to Timesketch..
    ...
    [INFO] Output processing is done.
    [INFO]
    *********************************** Counter ************************************
    [INFO]             Stored Events : 9022
    [INFO]           Events Included : 9022
    [INFO]        Duplicate Removals : 1
