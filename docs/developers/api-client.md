---
hide:
  - footer
---
# API Client

The API client is a set of Python libraries that can be used to interact with the REST API of Timesketch from notebooks or scripts. It takes
care of setting up authentication, sending the API calls to the server, error handling, and presentation.

This documentation will give an overview for the most common use cases of the API client. Some available methods will not be covered in this documentation
whereas others will be documented further in a notebook (e.g. [colab-timesketch-demo notebook](/notebooks/colab-timesketch-demo.ipynb)).

## Basic Connections

The API client defines a config library specifically intended to help with setting up all configuration for connecting to Timesketch, including
authentication and server information. The config client will read stored connection information from `~/.timesketchrc`, asking the user questions
if information is missing (and subsequently storing the results of those questions in the RC file for future lookups).

An example use of the config client:

```python
from timesketch_api_client import config

ts_client = config.get_client()
```

If the configuration file has more than a single section you can define which
section to use:

```python
from timesketch_api_client import config

ts_client = config.get_client(config_section='my_section')
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

### Directly passing username / password

Another option to create a connection to the Timesketch server is by creating an `TimesketchApi` object and passing `

```python
from timesketch_api_client import client as timesketch_client
client = timesketch_client.TimesketchApi(host_uri='https://demo.timesketch.org', username='demo', password='demo')
```

> Careful with storing credentials in code that you intend to publish or make available to others. 

## Client Config

In order to make it simpler to connect to the API client a config file
can be generated or created to store information needed to connect.

The file is stored in the user's home directory, in a file called
`$HOME/.timesketchrc`.

The content of the file is:

```
[timesketch]
...
```

An example config file for an API client that uses OAUTH to connect:

```
[timesketch]
client_secret = <redacted secret>
host_uri = https://mytimesketchhost.com
username = myusername@mydomain.com
auth_mode = oauth
client_id = <redacted client ID>
verify = True
```

A config file can have multiple sections to define which host to connect to.
This is useful if you want to be able to connect to more than a single
Timesketch instance, for instance your development instance and a production
one.

An example of that would be:

```
[timesketch]
host_uri = https://myprodtimesketch.corp.com
username = myselfandirene
verify = True
client_id =
client_secret =
auth_mode = userpass
cred_key = <redacted>

[timesketch-dev]
host_uri = http://localhost:5000
username = dev
verify = True
client_id =
client_secret =
auth_mode = userpass
cred_key = <redacted>
token_file_path = /home/myselfandirene/.timesketch.dev.token
```

Each of the additional sections needs to define a separate token file using the
`token_file_path`, otherwise the config will attempt to read the default token
file.


## Using the Timesketch Client

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

## List sketches

There are some ways to list sketches by adjusting the ```scope```.

Following scopes are available:

- recent: Get list of sketches that the user has actively searched in.
- shared: Get sketches that can be accessed
- admin: Get all sketches if the user is an admin
- archived: get archived sketches
- search: pass additional search query

```
ts_client.list_sketches(per_page=1000, scope='user', include_archived=True)
```

Will return all sketches that are owned by the specified user.

```
ts_client.list_sketches(per_page=1000, scope='shared', include_archived=True)
```

Will return all sketches that the account used to connect to the API has access to.

## Connecting to a Sketch

There are two ways of getting a sketch object, either by listing all available sketches or by fetching a specific one.
To fetch a specific one use the `get_sketch` function:

```
sketch = ts_client.get_sketch(SKETCH_ID)
```

All that the function needs is the sketch ID, eg:

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

### Saved Searches

To list all saved searches, use the `list_saved_searches` function of the sketch
object. This functions returns a `search.Search` object for all saved searches.
An example overview would be:

```
for saved_search in sketch.list_saved_searches():
  print('{0:03d} - {1:s} [{2:s}]'.format(saved_search.id, saved_search.name, saved_search.user))
```

To get a particular saved search:

```
saved_search = sketch.get_saved_search(search_id=<SEARCH_ID>)
```

or

```
saved_search = sketch.get_saved_search(search_name=<SEARCH_NAME>)
```

A search object can be used like this:

```
data = saved_search.table
```

The results will be a pandas DataFrame that contains all the records from the
saved search.

### Search Query

To search in the API client a search object is used. It will accept several
parameters or configurations, for instances a free flowing query string
(same as in the UI) or a raw OpenSearch query DSL. It can also support search
chips.

The output can be:
+ A pandas DataFrame.
+ A python dict.
+ Stored in a ZIP file.

A search object is created from a sketch object.

```
from timesketch_api_client import search
...

search_obj = search.Search(sketch=sketch)
```

From there several options are possible:

+ Restore a saved search using `from_saved(<SEARCH_ID>)`
+ Use the `from_manual` function that provides several parameters
+ Individually set the needed parameters.

The first thing you need to do after creating the object is to configure the
search parameters:

#### Retrieve a Stored Search

To retrieve a stored search used the `from_saved`:

```
search_obj.from_saved(<SEARCH_ID>)
```

#### Configure using the Explore Function

It is also possible to configure the search object using the `from_manual`
function.

```
search_obj.from_manual(
    query_string, query_dsl, query_filter,
    return_fields, max_entries)
```

All of these parameters are optional, but in order for the search object to
be able to query for results you need to provide either `query_string` or
the `query_dsl`.

+ **query_string**: This is the OpenSearch query string, the same one as you would
provide in the UI.
+ **query_dsl**: This is an OpenSearch Query DSL string. Please see the official
documentation about how it is structured.
+ **return_fields**: This is a comma separated string with all the fields you
want to be included in the returned value. If you want all fields returned you
can use the wildcard '\*'.
+ **max_entries**: By default the search object returns 10k records maximum. You
may want to either reduce that or increase it. If the search has the potential
to return more than 10k records a log record will be added indicating how many
records there could be, so that the search can be repeated by increasing the max
entries.

#### Configure Manually

All of the configurations that are present in the `from_manual` function are
also directly available in the object itself, and can be set directly.

```
search_obj.query_string = 'my search'
search_obj.max_entries = 10000000
search_obj.return_fields = 'datetime,timestamp_desc,data_type,message,domain,url'
```

There are also other configurations possible. In Jupyter/Colab notebook you can
always do

```
search_obj.*?
```

To find a list of all the possible configuration options.

#### Chips

Chips are the "+ Time filter" or "+ Add label filter", etc elements you can
see in the UI. There are several chips available:

+ DateIntervalChip
+ DateRangeChip
+ TermChip
+ LabelChip

To add a chip to a search object simply use the `add_chip` function:

```
search_obj.add_chip(label_chip)
```

To view the existing chips:

```
[c.chip for c in search_obj.chips]
```

Or
```
search_obj.query_filter
```

Chips can also be removed using the `search_obj.remove_chip(chip_index)`
function.

Each chip will have their own way of configuring it, let's take an example of a
date range chip.

```
range_chip = search.DateRangeChip()
range_chip.start_time = '2013-09-20T22:20:47'
range_chip.end_time = '2013-09-20T22:59:47'
search_obj.add_chip(range_chip)
```

For an interval chip:

```
interval_chip = search.DateIntervalChip()
interval_chip.date = '2013-09-20T22:39:47'
interval_chip.before = 10
interval_chip.after = 10
interval_chip.unit = 'm'

search_obj.add_chip(interval_chip)
```

Or a label chip:
```
label_chip = search.LabelChip()
label_chip.label = 'foobar'
search_obj.add_chip(label_chip)
```

Label chips can also be used to filter out all starred events, or events with
comments. For that use:

```
label_chip.use_comment_label()
```

or

```
label_chip.use_star_label()
```

#### Get The Results

Once you have constructed your search object, you may want to explore the
results.

To get the results as:
+ a pandas DataFrame use: `search_obj.table`
+ a dict, use `search_obj.dict`
+ a JSON string, use `search_obj.json`

Or if you want to store the results as a file:

```
search_obj.to_file('/tmp/myresults.zip')
```

(use the ZIP ending, since the resulting file will be a ZIP file with both the
results as a CSV file and a METADATA file.


#### Store a Search

If you want to store the search query in the datastore, to make it accessible
later on, or visible in the UI you can use the `save` function. First create a
name and a description and then save the object.

```
search_obj.name = 'My First Saved Search'
search_obj.description = 'This saves all my work'
search_obj.save()
```

After you save it, each time you make a change to the search the change gets
updated in the datastore. You can also call `save()` or `commit()` on the object
to make sure it was saved.

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
    'chart_title': 'Top 10 Domains Visited',
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

And if you want to save that aggregation for future use.

```
aggregation.name = 'TopDomains'
aggregation.save()
```

### Sigma rules

### Get a single rule

To get a Sigma rule that is stored on the server via uuid of the rule:

```python
rule = ts.get_sigmarule("5266a592-b793-11ea-b3de-0242ac130004")
```

Returns an object, where you can do something like that:

```python
rule.data()
```

To get this:

```JSON
{
  'title': 'Suspicious Installation of ZMap',
  'id': '5266a592-b793-11ea-b3de-0242ac130004',
  'description': 'Detects suspicious installation of ZMap',
  'references': ['https://rmusser.net/docs/ATT&CK-Stuff/ATT&CK/Discovery.html'],
  'author': 'Alexander Jaeger',
  'date': '2020/06/26',
  'modified': '2020/06/26',
  'logsource': {
    'product': 'linux',
    'service': 'shell'
  },
  'detection': {
    'keywords': ['*apt-get install zmap*'],
    'condition': 'keywords'
  },
  'falsepositives': ['Unknown'],
  'level': 'high',
  'search_query': '(data_type:("shell\\:zsh\\:history" OR "bash\\:history\\:command" OR "apt\\:history\\:line" OR "selinux\\:line") AND "*apt\\-get\\ install\\ zmap*")', 'file_name': 'lnx_susp_zmap'
}
```

### Get a list of rules

Another option to explore Sigma rules is via the `list_sigma_rules` function.
To get a list of available Sigma rules use:

```python
ts.list_sigma_rules()
```

The output can be:
+ A pandas DataFrame if the `as_pandas=True` is set
+ A python dict (default behavior)


## Add data

#### Manually add events to the sketch

Fill in your event data, you need at least these fields: message, date and timestamp description


```python

message = "foobar"
date = "2020-08-06T12:48:06.994188Z"
timestamp_desc = "Test_description"

# Attributes: A dict of extra attributes to add to the event.
attributes = {"a": "alpha", "o": "omega", "g": "gamma"}

# Tags: A list of strings to include as tags.
tags = ["not", "important"]

sketch.add_event(message, date, timestamp_desc, attributes, tags)

```

### Add Tags to events

To add tags to multiple events:

```python
# first search for the events that you want to search for
events = sketch.explore('foobarsearchterm', as_dict=True)
events['objects']
for event in events['objects']:
 print(event.get('_id'))
 events2 = [{
               '_id': event.get('_id'),
               '_index': event.get('_index'),
               '_type': 'generic_event'
               }]
 tags = ['foobartag']
 sketch.tag_events(events2, tags)
```

Of if you want to tag a single event:

```python
# Or if you want to do single ones:
events2 = [{
               '_id': 'g-abcdErfededed',
               '_index': 'asd23r23dk19b398abe405cbf33f',
               '_type': 'generic_event'
               }]
tags = ['foobartag']
sketch.tag_events(events2, tags)
```

Both will give you something like:

```python

{'events_processed_by_api': 1,
 'number_of_events_passed_to_api': 1,
 'number_of_events_with_added_tags': 1,
 'tags_applied': 1,
 'total_number_of_events_sent_by_client': 1}
```
### Remove tags from Events

`untag_event`and `untag_events` in the context of a sketch.

`untag_event(self, event_id: str, index, tag: str):` - Untags the specified tag from the event with the specified ID.
`untag_events(self, events, tags_to_remove: list):` - Untags the specified tag from all of the events with the specified IDs.

Example code:

```python

import timesketch_api_client

Create a client
client = timesketch_api_client.TimesketchAPIClient()
sketch = client.get_sketch(1)

# Get the event ID
event_id = "k8P1MYcBkeTGnypeeKJL"

# Untag the event
sketch.untag_event(event_id, "foobar")
```

> Note the maximum of events passed via API is 500. The maximum number of tags to be removed in one API call is also 500.

### Add Attributes to Events

To add new attributes to event an event:

```python
# event_id and searchindex_id can be found by searching for the target event.

event = [
  {
    '_id': event_id,
    '_index': searchindex_id,
    '_type': '_doc',
    'attributes': [
      {
        'attr_name': 'an_attribute_name',
        'attr_value': 'A new attribute value'
      }
    ]
  }
]
sketch.add_event_attributes(events)
```


## Other Options

The sketch object can be used to do several other actions that are not documented in this first document, such as:

+ Create/list/retrieve stories
+ Add timelines to the sketch
+ Modify the ACL of the sketch
+ Archive the sketch (via the `sketch.archive` function)
+ Comment on an event
+ Delete a sketch
+ Export the sketch data
+ Run analyzers on the sketch.

## Examples

There are several examples using the API client in the [notebooks folder](https://github.com/google/timesketch/notebooks) in the Github repository.
