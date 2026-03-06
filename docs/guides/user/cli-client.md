---
hide:
  - footer
---
Timesketch has a command line client (CLI) that is meant to be used to access the
system from the terminal. It has many of the feature that the Web interface have
including:

- Searching
- Filtering
- Upload timelines
- Running analyzers
- Output in CSV, Table or plain text format

## Installing

The CLI client is available as a package on PyPi. To install, simply:

```
pip3 install timesketch-cli-client
```

## Basic usage

The command line program is called `timesketch`. To see the help menu you can
invoke without any parameters alternatively issue `timesketch --help`.

```
$ timesketch
Usage: timesketch [OPTIONS] COMMAND [ARGS]...

  Timesketch CLI client.

  This tool provides similar features as the web client does. It operates
  within the context of a sketch so you either need to provide an existing
  sketch or create a new one.

  Basic options for editing the sketch is provided, e.g re-naming and changing
  the description as well as archiving and exporting. For other actions not
  available in this CLI client the web client should be used.

  For detailed help on each command, run  <command> --help

Options:
  --version             Show the version and exit.
  --sketch INTEGER      Sketch to work in.
  --output-format TEXT  Set output format [json, text, tabular, csv]
                        (overrides global setting).
  -h, --help            Show this message and exit.

Commands:
  analyze         Analyze timelines.
  config          Configuration for this CLI tool.
  events          Manage event.
  import          Import timeline.
  intelligence    Manage intelligence within a sketch.
  saved-searches  Managed saved searches.
  search          Searches and explores events within a Timesketch sketch.
  sigma           Manage sigma rules.
  sketch          Manage sketch.
  timelines       Manage timelines.
```

## Configure

#### Default sketch

The program need to know what sketch you are working in. You can either specify it
with the `--sketch` flag on all invocations, or you can configure it globally:

```
timesketch config set sketch <ID of your sketch>
```

From now on, every invocation of the command will use the sketch you configured.

#### Output format

You can set the default output format. Choose between `CSV, Tabular and Plain text` output.

Example:

```
timesketch config set output csv
```

The output format can also be set in CLI with the following flag:

```
timesketch --output-format text [YOURCOMMAND]
```

## Search

The main functionality is of course the ability to search your timelines. The `search`
subcommand has the following features:

```
$ timesketch search --help
Usage: timesketch search [OPTIONS]

  Searches and explores events within a Timesketch sketch.

  Executes a search query against a Timesketch sketch, applying various
  filters and formatting the output.
  Supports queries using OpenSearch query string syntax, date/time filtering,
  label filtering, and saved searches.
  The output can be formatted as text, CSV, JSON, JSONL, or tabular,
  depending on the context's 'output_format' setting.

Options:
  -q, --query TEXT        Search query in OpenSearch query string format
  --time TEXT             Datetime filter (e.g. 2020-01-01T12:00)
  --time-range TEXT...    Datetime range filter (e.g: 2020-01-01 2020-02-01)
  --label TEXT            Filter events with label
  --header / --no-header  Toggle header information (default is to show)
  --return-fields TEXT    What event fields to show
  --order TEXT            Order the output (asc/desc) based on the time field
  --limit INTEGER         Limit amount of events to show (default: 40)
  --saved-search INTEGER  Query and filter from saved search
  --describe              Show the query and filter then exit
  --show-internal-columns Show all columns including Timesketch internal ones
  -h, --help              Show this message and exit.

```

#### Simple search

```
timesketch -q "foobar"
```

#### Time filter

```
timesketch search -q "foobar" --time-range 2022-01-01 2022-01-02
```

#### Pipe the output to other unix programs

This example returns the field name `domain` and then do a simple sort and uniq.

```
timesketch search -q "foobar" --return-fields domain | sort | uniq
```

## Saved Searches

### List saved searches

To list all saved searches in the sketch:

```bash
timesketch saved-searches list
```

### Describe a saved search

To see the details of a saved search:

```bash
timesketch saved-searches describe <SEARCH_ID>
```

## Sketch

### List all sketches

To list all sketches you have access to:

```bash
timesketch --output-format text sketch list
 id   name
  2 asdasd
  1   aaaa
```

You can also get a list as JSON if you like to:

```
timesketch --output-format json sketch list
[
    {
        "id":2,
        "name":"asdasd"
    },
    {
        "id":1,
        "name":"aaaa"
    }
]
```

### Get description for one sketch

Getting information about a sketch can be helpful in various situations.

```bash
timesketch --output-format text sketch describe
Name: asdasd
Description: None
Status: new
```

You can also get all stored information about a sketch with running:
```bash
timesketch --output-format json sketch describe
```

This will give you something like:

```json
timesketch --output-format json sketch describe
{
    "_archived": null,
    "_sketch_name": "asdasd",
    "api": "<timesketch_api_client.client.TimesketchApi object at 0x7f3375d466e0>",
    "id": 2,
    "resource_data": {
        "meta": {
            "aggregators": {
              ...
```

### Create a sketch

To create a new sketch:

```bash
timesketch sketch create --name "My New Sketch" --description "Analysis of incident X"
```

### Export a sketch

Running `sketch export` will export events from the sketch to a ZIP file.

By default, this command uses the search-based export, which fetches
all events from the sketch and saves them to a ZIP file containing
a CSV of the results and metadata.

If the `--use_sketch_export` flag is provided, it uses the full sketch
export functionality. This creates a comprehensive ZIP file that includes
not only all events but also stories (as HTML), aggregations, views,
and metadata associated with the sketch.

The filename can be just a name (e.g. `my_export.zip` which saves to the
current directory) or a full path.

```bash
timesketch sketch export --filename my_export.zip
```

Options:
- `--stream`: Stream the download. This is useful for large exports to avoid memory issues. Can be used with either export method.
- `--use_sketch_export`: Use the full sketch export functionality (same as Web UI export) instead of just exporting events.

Example of a full, streamed export:
```bash
timesketch sketch export --filename my_large_export.zip --use_sketch_export --stream
```

### Archive Sketch

Running `sketch archive` will set the archive flag to the sketch.

### Unarchive a sketch

Running `sketch unarchive` will set the archive flag to the sketch.

### Delete a sketch

Running `sketch delete` will delete the sketch. By default it is a dry-run. Use `--force_delete` to execute.

```bash
timesketch sketch delete
# Dry run output...

timesketch sketch delete --force_delete
# Actually deletes the sketch
```

### Get attributes

Attributes can be to long to show in `sketch describe` which is why there is a
separate command for it:

```timesketch sketch attributes list```

Will give back something like this:

```bash
timesketch --output-format text sketch attributes list
Name: intelligence: Ontology: intelligence Value: {'data': [{'externalURI': 'google.com', 'ioc': '1.2.3.4', 'tags': ['foo'], 'type': 'ipv4'}, {'externalURI': 'fobar.com', 'ioc': '3.3.3.3', 'tags': ['aaaa'], 'type': 'ipv4'}]}
Name: ticket_id: Ontology: 12345 Value: text
Name: ticket_id2: Ontology: 12345 Value: text
Name: ticket_id3: Ontology: 12345 Value: text
```

Or as JSON

```bash
timesketch --output-format json sketch attributes list
{
    "intelligence": {
        "ontology": "intelligence",
        "value": {
            "data": [
                {
                    "externalURI": "google.com",
                    "ioc": "1.2.3.4",
                    "tags": [
                        "foo"
                    ],
                    "type": "ipv4"
                },
                {
                    "externalURI": "fobar.com",
                    "ioc": "3.3.3.3",
                    "tags": [
                        "aaaa"
                    ],
                    "type": "ipv4"
                }
            ]
        }
    },
    "ticket_id": {
        "ontology": "12345",
        "value": "text"
    },
    "ticket_id2": {
        "ontology": "12345",
        "value": "text"
    },
    "ticket_id3": {
        "ontology": "12345",
        "value": "text"
    }
}
```

### Add a attribute

To add an attribute to a sketch

```bash
timesketch sketch attributes add
```

For example:

```bash
timesketch sketch attributes add --name ticket_id3 --ontology text --value 12345
Attribute added:
Name: ticket_id3
Ontology: text
Value: 12345
```

To verify, run `timesketch sketch attributes list`.

### Remove an attribute

To remove an attribute from a sketch

```bash
timesketch sketch attributes remove
```

### Labels

#### list_labels

Running `sketch list_label` will give you a list of all labels of a sketch.

Example:
```bash
timesketch --sketch 14 --output-format json sketch list_label
['test', 'foobar']
```

#### add label

Running `sketch add_label --label foobar` will add the label `foobar` to the sketch.

Example:
```bash
timesketch --sketch 14 --output-format json sketch add_label --label=foobar
Label added
```

#### Remove label

Running `sketch remove_label --label foobar` will remove the label `foobar` from the sketch.

Example:
```bash
timesketch --sketch 14 --output-format json sketch remove_label --label=foobar
Label removed
```

### Stories

#### create-story

Running `sketch create-story --title "My new story"` will create a new story in the sketch.

Example:
```bash
timesketch --sketch 14 create-story --title="My new story"
Story created: My new story
```

#### list-stories

Running `sketch list-stories` will give you a list of all stories of a sketch.

Example:
```bash
timesketch --sketch 14 --output-format json sketch list-stories
[
    {
        "id": 1,
        "title": "My new story"
    }
]
```

### Export only with annotations

You can export events that have comments, stars, or labels using `sketch export-only-with-annotations`.

```bash
timesketch sketch export-only-with-annotations --filename annotated.csv
```

## Intelligence

Intelligence is always sketch specific. The same can be achieved using 
`timesketch attributes` command, but then the ontology type and data needs 
to be provided in the correct format.

Running `timesketch intelligence list` will show the intelligence added to a 
sketch (if sketch id is set in the config file)

The output format can also be changed as follows

```bash
timesketch --sketch 2 --output-format text intelligence list --columns ioc,externalURI,tags,type
ioc	externalURI	tags	type
1.2.3.4	google.com	foo	ipv4
3.3.3.3	fobar.com	aaaa	ipv4
```

Or as CSV

```bash
timesketch --sketch 2 --output-format csv intelligence list --columns ioc,externalURI,tags,type
ioc,externalURI,tags,type
1.2.3.4,google.com,"foo",ipv4
3.3.3.3,fobar.com,"aaaa",ipv4
aaaa.com,foobar.de,"foo,aaaa",hostname
```

### Adding Intelligence

Adding an indicator works as following

```bash
timesketch --sketch 2 intelligence add --ioc 8.8.4.4 --ioc-type ipv4 --tags foo,bar,ext
```

### Removing all of Intelligence

To remove all intelligence indicators, run:

```bash
timesketch --sketch 2 --output-format text sketch attributes remove --name intelligence --ontology intelligence
Attribute removed: Name: intelligence Ontology: intelligence
```

## Analyzers

### List

List all available analyzers:

```
timesketch analyze list
```

To get information about analyzers available in the Timesketch instance the command `timesketch analyze list` can be used.
If no sketch is defined in the config yet, it can also be passed as an argument, e.g.:

```bash
timesketch --output-format tabular --sketch 1 analyze list 
Name	Display Name	Is Multi
login	Windows logon/logoff events	False
ntfs_timestomp	NTFS timestomp detection	False
chain	Chain linked events	False
tagger	Tagger	True
ssh_sessionizer	SSH sessions	False
sigma	Sigma	False
ssh_bruteforce_sessionizer	SSH bruteforce	False
evtx_gap	EVTX gap	False
hashr_lookup	hashR lookup	False
domain	Domain	False
web_activity_sessionizer	Web activity sessions	False
similarity_scorer	Similarity Scorer	False
sessionizer	Time based sessions	False
safebrowsing	Google Safe Browsing	False
gcp_servicekey	Google Compute Engine actions	False
win_crash	Windows application crashes	False
browser_timeframe	Browser timeframe	False
gcp_logging	Google Cloud Logging Analyzer	False
misp_analyzer	MISP	False
hashlookup_analyzer	Hashlookup	False
feature_extraction	Feature extractor	True
geo_ip_maxmind_db	Geolocate IP addresses (MaxMind Database based)	False
sshbruteforceanalyzer	SSH Brute Force Analyzer	False
phishy_domains	Phishy domains	False
geo_ip_maxmind_web	Geolocate IP addresses (MaxMind Web client based)	False
yetiindicators	Yeti threat intel indicators	False
account_finder	Account finder	False
browser_search	Browser search terms	False
windowsbruteforceanalyser	Windows Login Brute Force Analyzer	False
```

### Run

Run a specific analyzer. In this example the `domain` analyzer on timeline 1:

```
timesketch analyze run --analyzer domain --timeline 1
Running analyzer [domain] on [timeline 1]:
..
Results
[domain] = 217 domains discovered (150 TLDs) and 1 known CDN networks found.
```

### List analyzer results

It might be useful to see the results of an analyzer for a specific timeline.
That can be done with `timesketch analyze results`.

It can show only the analyzer results directly:

```bash
timesketch --output-format text analyze results --analyzer account_finder --timeline 3
Results for analyzer [account_finder] on [sigma_events]:
SUCCESS - NOTE - Account finder was unable to extract any accounts.
```

Some analyzers might start dependent analyzers, to also show those results use
the flag `--show-dependent`. This will look similar to:

```bash
timesketch --output-format text analyze results --analyzer account_finder --timeline 3 --show-dependent
Results for analyzer [account_finder] on [sigma_events]:
Dependent: DONE - None - Feature extraction [gmail_accounts] extracted 0 features.
Dependent: DONE - None - Feature extraction [github_accounts] extracted 0 features.
Dependent: DONE - None - Feature extraction [linkedin_accounts] extracted 0 features.
...
SUCCESS - NOTE - Account finder was unable to extract any accounts.
Dependent: DONE - None - Feature extraction [rdp_rds_ipv4_addresses] extracted 0 features.
Dependent: DONE - None - Feature extraction [ssh_failed_username] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_subject_domain] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_subject_logon_id] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_username] extracted 0 features.
```

To get a result in `json` that can be piped into other CLI tools run something
like:

```json
timesketch --output-format json analyze results --analyzer account_finder --timeline 3 --show-dependent
[
    {
        "analyzer": "feature_extraction",
        "index": "<timesketch_api_client.index.SearchIndex object at 0x7ff9079a7a60>",
        "results": "Feature extraction [gmail_accounts] extracted 0 features.",
        "session_id": 1,
        "status": "DONE",
        "timeline_id": 3
    },
    {
        "analyzer": "feature_extraction",
        "index": "<timesketch_api_client.index.SearchIndex object at 0x7ff9079a7910>",
        "results": "Feature extraction [github_accounts] extracted 0 features.",
        "session_id": 1,
        "status": "DONE",
        "timeline_id": 3
    }
]
```

## Events

### Add manual events

This feature allows users to add events to their Timesketch account using the `events add` command. The command takes three arguments: `message, date, timestamp-desc` and an optional field for `attributes`. The message is a short description of the event, the date is the date and time the event occurred, and the attributes are a list of key-value pairs that will be associated with the event.

`timestamp_desc` is a field that is used to describe the timestamp of an event. This field can be helpful for providing context about the event, such as the type of event or the source of the data.

For example, you could use the `timestamp_desc` field to specify that an event is a "Windows Sysmon event" or a "Netflow event." This information can be helpful for quickly identifying and understanding the events in a timeline.

For example, the following command would add an event to the Timesketch `timesketch events add --message "foobar-message" --date 2023-03-04T11:31:12 --timestamp-desc "test" --attributes key=value,key2=value2`:

This new feature makes it easy to add events to Timesketch from the command line, which can be helpful for automating tasks or for quickly adding events when you don't have access to the Timesketch web interface.

It can also be called with a output format `json` like following.

```bash
timesketch --output-format json events add --message "foobar-message" --date 2023-03-04T11:31:12 --timestamp-desc "test" 
{'meta': {}, 'objects': [{'color': 'F37991', 'created_at': '2023-03-08T12:46:24.472587', 'datasources': [], 'deleted': None, 'description': 'internal timeline for user-created events', 'id': 19, 'label_string': '', 'name': 'Manual events', 'searchindex': {'created_at': '2023-03-08T12:46:24.047640', 'deleted': None, 'description': 'internal timeline for user-created events', 'id': 9, 'index_name': '49a318b0ba17867fd71b50903774a0c8', 'label_string': '', 'name': 'Manual events', 'status': [{'created_at': '2023-03-17T09:35:03.202520', 'id': 87, 'status': 'ready', 'updated_at': '2023-03-17T09:35:03.202520'}], 'updated_at': '2023-03-08T12:46:24.047640', 'user': {'active': True, 'admin': True, 'groups': [], 'username': 'dev'}}, 'status': [{'created_at': '2023-03-17T09:35:03.233973', 'id': 79, 'status': 'ready', 'updated_at': '2023-03-17T09:35:03.233973'}], 'updated_at': '2023-03-08T12:46:24.472587', 'user': {'active': True, 'admin': True, 'groups': [], 'username': 'dev'}}]}
Event added to sketch: timefocus test
```

### Annotate an event

You can add tags and comments to an event.

```bash
timesketch events annotate --timeline-id <ID> --event-id <ID> --tag "tag1,tag2" --comment "Something interesting"
```

### Remove tag(s)

The command `events remove_tag` takes a list of tags as its argument and removes those tags from the event. For example, the following command would remove the tags "suspicious" and "foobar333" from the event with the ID "k8P1MYcBkeTGnypeeKJL".

```bash
timesketch events remove_tag --timeline-id 4 --event-id k8P1MYcBkeTGnypeeKJL --tag foobar333
200
```

If called without `--tag` parameter, the client will show the current event details to make it easier to find the ones to remove.

It is also possible to provide a comma separated list of tags to remove. The following command will remove both tags `foobar333`and `fooba123`.

```bash
timesketch events remove_tag --timeline-id 4 --event-id k8P1MYcBkeTGnypeeKJL --tag foobar333,fooba123
200
```

## Timelines

### List timelines

To list all timelines in a given sketch use: `timelines list`.

```bash
timesketch --sketch 1 timelines list
1 foobar
2 foobar3
```

It is also possible to get all the output as JSON.

### Describe a timeline

The command `timelines describe` will provide several variables, names and settings for a given timeline.

```
timesketch --sketch 1 --output-format text timelines describe 2
Name: foobar3
Index: 41dde394812d44c1ac1784997d05efed
Status: ready
Event count: 260454
Color: AAAAAA
Name: foobar3
Created: 2024-08-20T14:57:59.047015
Datasources:
	Original filename: win7-x86.plaso
	File on disk: /tmp/4c3c1c5c351b4db285453bff0ecad51e
	Error:
```

### Rename timeline

To rename a single timeline in a sketch, the command `timelines rename` can be used.

```bash
timesketch --sketch 1 timelines rename 1 foobar23
```

### Delete a timeline

The cli client is using the API to delete a timeline.

As of August 2024, the API method to delete a timeline does only mark the reference in the database as deleted, the data will remain in Opensearch.

```bash
timesketch --sketch 1 timelines delete 1
Confirm to mark the timeline deleted:: 1 foobar23? [y/N]: y
Deleted
```

### Change timeline color

The color is an important setting for a timeline when using the WebUI. To change the color using the CLI `timelines color` can be used.

Before:
```bash
timesketch --sketch 1 --output-format text timelines describe 2
Name: foobar3
Index: 41dde394812d44c1ac1784997d05efed
Status: ready
Event count: 260454
Color: AAAAAA
Name: foobar3
Created: 2024-08-20T14:57:59.047015
Datasources:
	Original filename: win7-x86.plaso
	File on disk: /tmp/4c3c1c5c351b4db285453bff0ecad51e
	Error:
```

Using it:

```bash
timesketch --sketch 1 timelines color 2 BBBBBB
```

After:

```bash
timesketch --sketch 1 --output-format text timelines describe 2
Name: foobar3
Index: 41dde394812d44c1ac1784997d05efed
Status: ready
Event count: 260454
Color: BBBBBB
Name: foobar3
Created: 2024-08-20T14:57:59.047015
Datasources:
	Original filename: win7-x86.plaso
	File on disk: /tmp/4c3c1c5c351b4db285453bff0ecad51e
	Error:
```

## Sigma

### List Sigma Rules

To list all sigma rules:

```bash
timesketch sigma list
```

### Describe Sigma Rule

To describe a specific sigma rule:

```bash
timesketch sigma describe --rule-uuid <UUID>
```

## Import

To import a timeline:

```bash
timesketch import --name "My Timeline" /path/to/file.plaso
```
