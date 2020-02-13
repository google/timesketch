# Upload Data to Timesketch

There are several different ways to upload data to Timesketch. This document
attempts to explore them all.

These are the different ways to upload data:

1. Directly using the REST API.
2. Using the API client, or the importer library.
3. Using the web UI.
4. Using the importer CLI tool.
5. SCP or transferring a file to an upload folder on the Timesketch server.

Let's explore each of these ways a bit further.

## Using the API client.

The API client defines an importer library that is used to help with
file or data uploads. This is documented further
[here](/docs/UploadDataViaAPI.md)

## Using the Web UI.

```
TODO: add documentation
```
## Using the importer CLI Tool.

If the data that is to be imported is a single file then the importer tool
can be used. It utilizes the API client and the importer library to upload
the file. This is a simple wrapper around that library. The tool comes with
the installation of the timesketch API client.

There are two methods to use the tool:

1. Define all parameters on the command line.
2. Define all configuration in a YAML config file and only provide a path
to the tool (and the config file).

The easiest way to discover the parameters and how to run the tool is to run:

```
$ timesketch_importer.py -h
```

The minimum set of parameters to the run tool are:

```
$ timesketch_importer.py --pwd-prompt -u <USERNAME> --host https://mytimesketch.com path_to_my_file.csv
```

However if the authentication mechanism is OAUTH then `client_id` and
`client_secret` need to be set.

Other parameters suggested to be set are `sketch_id` (if it isn't provided a
new sketch will be created) and `timeline_name` (otherwise a default name
will be chosen).

In order to reduce the amount of parameters to pass to the tool a YAML
configuration file can be used. The format of it is simple:

```
config_option: value
...
```

The configuration options that can be defined in the YAML file are:

| Option | Type | Notes |
| ------ | ---- | ----- |
| username | string | The username to use to authenticate against the Timesketch server |
| password | string | If password is used, it can be provided here (not recommended) |
| pwd_prompt | boolean | If set to True then the tool will prompt the user for a password, only used if password is used to authenticate |
| client_secret | string | If OAUTH is used for authentication then a client secret needs to be defined. |
| client_id | string | If OAUTH is used for authentication a client ID needs to be defined. |
| run_local | boolean | If set to True and OAUTH is used for authentication then an authentication URL is prompted on the screen that the user needs to follow in order to complete the OAUTH dance, this is particularly useful if the tool is run through a remote session, like SSH. |
| host | string | URI that points to the Timesketch instance. |
| format_string | string | Formatting string for the message field if it is not defined in the input data. |
| timeline_name | string | Name that will be used for the timeline as it gets imported into Timesketch. |
| index_name | string | If the data should be imported into a specific timeline the index needs to be defined, otherwise a new index will be generated. |


## SCP/File Transfer to an Upload Folder

```
TODO: add documentation
```

## Using the REST API.

```
TODO: add documentation
```
