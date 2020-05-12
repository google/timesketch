# Upload Data to Timesketch

There are several different ways to upload data to Timesketch. This document
attempts to explore them all.

These are the different ways to upload data:

1. Using the importer CLI tool.
2. Using the web UI.
3. Using the importer library.
4. SCP or transferring a file to an upload folder on the Timesketch server.
5. Directly using the REST API.

Let's explore each of these ways a bit further.

## Using the importer CLI Tool.

If the data that is to be imported is a single file then the importer tool
can be used. It utilizes the importer library and the API client to upload
the file. This is a simple wrapper around the importer library. The tool comes
with the installation of the timesketch importer client.

There are two methods to use the tool:

1. Define all parameters on the command line.
2. Define the parameters in the [~/.timesketchrc](/docs/APIConfigFile.md) file.

The easiest way to discover the parameters and how to run the tool is to run:

```
$ timesketch_importer.py -h
```

The minimum set of parameters to the run tool are:

```
$ timesketch_importer.py path_to_my_file.csv
```

However this requires that the `~/.timesketchrc` file contains all the necessary
configs. If there are configuration items that are missing then the tool will
ask questions to get the remaining parameters.

Remember for OAUTH authentication both `client_id` and `client_secret` need to
be set.

The tool will store the user credentials in an encrypted file as soon as it
runs for the first time. This token file will be used for subsequent uses
of the tool.

Other parameters suggested to be set are `sketch_id` (if it isn't provided a
new sketch will be created) and `timeline_name` (otherwise a default name
will be chosen).

For larger files the importer will split them up into pieces before uploading.

## Using the Web UI.

Click the `+ timeline` button in the UI or click `manage` in the Timeline
section and then add your timeline using the `Choose file` button that
appears below the timelines.

## Using the importer library.

The importer client defines an importer library that is used to help with
file or data uploads. This is documented further
[here](/docs/UploadDataViaAPI.md)

## SCP/File Transfer to an Upload Folder

```
TODO: add documentation
```

## Using the REST API.

This is not recommended, please use other mechanism, such as the importer
library that masks quite a lot of details that are needed to use the API
directly.

