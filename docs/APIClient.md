# API Client

The API client is a set of Python libraries that can be used to interact with the REST API of Timesketch from notebooks or scripts. It takes
care of setting up authentication, sending the API calls to the server, error handling, and presentation.

This is not meant to be a full fledged documentation of the API client, but rather a starting point for people on how to use the API client in
a script. The same methods can be used for interactions in a notebook, however those instructions are best left in a notebook (TODO: Create a
notebook and link to it here).

## Basic Connections

The API client defines a config library specifically intended to help with setting up all configuration for connecting to Timesketch, including
authentication and server information. The config client will read stored connection information from `~/.timesketchrc`, asking the user questions
if information is missing (and subsequently storing the results of those questions in the RC file for future lookups).

An example use of the config client:

```
from timesketch_api_client import config

ts_client = config.get_client()
```

To be able to take advantage of the config client, the user needs to be running this from the command line or in a way where questions can be asked
and answered (or the config file to be fully populated). This works both in CLI scripts as well as in a notebook.

By default the client credentials will be stored on disk in a Token file, in an encrypted format, protected by a randomly generated
password that is stored in the RC file. It is highly recommended to protect your credential file using a strong password. The password
for the file can be passed on to the config class using:

```
ts_client = config.get_client(token_password='MY_SUPER_L337_PWD')
```

If the token file does not exist, it will be generated and encrypted using the supplied password.

### Using the Timesketch Client

The TS client only has limited functionality, such as to list open indices, what sketches the user has access to as well as to fetch sketches, indices, etc.
The client object also contains functions to check for OAUTH token status and refresh it, if needed.

Most of the functionality of the API client lies in sketch operations. To list all available sketches the function `list_sketches` can be used:

```
for sketch in ts_client.list_sketches():
  # Do something with the sketches...
```

To print the name and description of all available sketches, something like:

```
for sketch in ts_client.list_sketches():
  print('[{0:d}] {1:s} <{2:s}>'.format(sketch.id, sketch.name, sketch.description))
```

## Connecting to a Sketch

There are two ways of getting a sketch object, either by listing all available sketches or by fetching a specific one.
To fetch a specific one use the `get_sketch` function:

```
sketch = ts_client.get_sketch(SKETCH_ID)
```

All you need is the sketch ID, eg:

```
sketch = ts_client.get_sketch(25)
```

## Overview of a Sketch

A sketch object has few properties that can be used to get a better overview of what it contains:

+ **acl**: A python dict with the current sketch ACL.
+ **labels**: A list of strings, with all the labels that are attached to the sketch.
+ **name**: The name of the sketch.
+ **description**: The description of the sketch.
+ **status**: The status of the sketch.

Each of these properties can be accessed using `sketch.<PROPERTY>`, eg. `sketch.name`, or `sketch.labels`

## Explore Data

The sketch object has several ways to explore data, via aggregations or searches.

### Views

The first is simply to list up all views... the function `list_views` returns back View object for all views. An example overview would be:

```
for view in sketch.list_views():
  print('{0:03d} - {1:s} [{2:s}]'.format(view.id, view.name, view.user))
```

It is also possible to create a new view:

```
view = sketch.create_view(name, query_string='', query_dsl='', query_filter=None)
```

Which can be as simple as:

```
view = sketch.create_view('Google mentions', query_string='google.com')
```

To get a view that has been saved:

```
view = sketch.get_view(view_id=<VIEW_ID>)
```

or 

```
view = sketch.get_view(view_name=<VIEW_NAME>)
```

A view object can be used like this:

```
data = sketch.explore(view=view, as_pandas=True)
```

The results will be a pandas DataFrame that contains all the records from a view.

### Search Query

To search in the API client the function `sketch.explore` is used. It will accept several parameters, such as a view object if that is available
or a free flowing query string (same as in the UI) or a raw Elastic query DSL.

The output can be:
+ A pandas DataFrame if the `as_pandas=True` is set
+ A python dict (default behavior)
+ All output stored to a file if the parameter `file_name='FILEPATH.zip'` is supplied.

There are also other parameters to the explore function that are worth a mention:
+ **query_filter**: possible to customize the query filter, to limit search results, include extra fields in the results, etc
+ **return_fields**: A comma separated string that contains a list of the fields/columns you want returned. By default only
a limited set of columns are returned. To expand on that use this variable to list up the columns you need.
+ **max_entries**: an integer that determines the maximum amount of entries you want returned back. The default value here is 10k
events. There may be a bit more events returned than this number determines, it is a best effort but should be used if you don't want
all the events returned back, only a fraction of them.

An example of a search query:

```
data = sketch.explore('google.com', as_pandas=True)
```

This will return back a pandas DataFrame with the search results.

### Aggregations

Another option to explore the data is via aggregations. To get a list of available aggregators use:

```
sketch.list_available_aggregators()
```

What gets returned back is a pandas DataFrame with all the aggregators and what parameters they need in order to work.

An example aggregation is:

```
params = {
    'field': 'domain',
    'limit': 10,
    'supported_charts': 'hbarchart',
}

aggregation = sketch.run_aggregator(aggregator_name='field_bucket', aggregator_parameters=params)
```

This will return back an aggregation object that can be used to display the data, eg in a pandas DataFrame

```
df = aggregation.table
```

Or as a chart

```
aggregation.chart
```



### Other Options

The sketch object can be used to do several other actions that are not documented in this first document, such as:
+ Create/list/retrieve stories
+ Manually add events to the sketch
+ Add timelines to the sketch
+ Modify the ACL of the sketch
+ Archive the sketch (via the `sketch.archive` function)
+ Comment on an event
+ Delete a sketch
+ Export the sketch data
+ Run analyzers on the sketch.
