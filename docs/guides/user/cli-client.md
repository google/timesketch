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
invoke without ay parameters alternatively issue `timesketch --help`.

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
  --version         Show the version and exit.
  --sketch INTEGER  Sketch to work in.
  --output-format TEXT  Set output format [json, text, tabular, csv]
                        (overrides global setting).
  -h, --help        Show this message and exit.

Commands:
  analyze         Analyze timelines.
  config          Configuration for this CLI tool.
  events          Manage events
  import          Import timeline.
  saved-searches  Managed saved searches.
  search          Search and explore.
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

  Search and explore.

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

### Get attributes

Attributes can be to long to show in `sketch describe` which is why there is a
separate command for it:

```timesketch sketch attributes```

Will give back something like this:

```bash
timesketch --output-format text sketch attributes
Name: intelligence: Ontology: intelligence Value: {'data': [{'externalURI': 'google.com', 'ioc': '1.2.3.4', 'tags': ['foo'], 'type': 'ipv4'}, {'externalURI': 'fobar.com', 'ioc': '3.3.3.3', 'tags': ['aaaa'], 'type': 'ipv4'}]}
Name: ticket_id: Ontology: 12345 Value: text
Name: ticket_id2: Ontology: 12345 Value: text
Name: ticket_id3: Ontology: 12345 Value: text
```

Or as JSON

```
timesketch --output-format json sketch attributes
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
timesketch sketch add_attribute
```

For example:

```bash
timesketch sketch add_attribute --name ticket_id3 --ontology text --value 12345
Attribute added:
Name: ticket_id3
Ontology: text
Value: 12345
```

To verify, run `timesketch sketch attributes`.

### Remove an attribute

To remove an attribute from a sketch

```bash
timesketch sketch remove_attribute
```


## Run analyzers

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
timesketch analyze --analyzer domain --timeline 1
Running analyzer [domain] on [timeline 1]:
..
Results
[domain] = 217 domains discovered (150 TLDs) and 1 known CDN networks found.

```

### List analyzer results

It might be useful to see the results of an analyzer for a specific timeline.
That can be done with `timesketch analyzer results`.

It can show only the analyzer results directly:

```
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
Dependent: DONE - None - Feature extraction [rdp_ts_ipv4_addresses] extracted 0 features.
Dependent: DONE - None - Feature extraction [ssh_client_ipv4_addresses] extracted 0 features.
Dependent: DONE - None - Feature extraction [ssh_client_ipv4_addresses_2] extracted 0 features.
Dependent: DONE - None - Feature extraction [ssh_host_ipv4_addresses] extracted 0 features.
Dependent: DONE - None - Feature extraction [ssh_client_password_ipv4_addresses] extracted 0 features.
Dependent: DONE - None - Feature extraction [ssh_disconnected_username] extracted 0 features.
Dependent: DONE - None - Feature extraction [ssh_disconnected_ip_address] extracted 0 features.
Dependent: DONE - None - Feature extraction [ssh_disconnected_port] extracted 0 features.
Dependent: DONE - None - Feature extraction [ssh_failed_ip_address] extracted 0 features.
Dependent: DONE - None - Feature extraction [ssh_failed_port] extracted 0 features.
Dependent: DONE - None - Feature extraction [ssh_failed_method] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_subject_username] extracted 0 features.
Dependent: DONE - None - Feature extraction [email_addresses] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_domain] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_logon_id] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_logon_type] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_logon_process_name] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_workstation_name] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_process_id] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_process_name] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_ip_address] extracted 0 features.
Dependent: DONE - None - Feature extraction [win_login_port] extracted 0 features.
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

```timesketch --output-format json events add --message "foobar-message" --date 2023-03-04T11:31:12 --timestamp-desc "test" 
{'meta': {}, 'objects': [{'color': 'F37991', 'created_at': '2023-03-08T12:46:24.472587', 'datasources': [], 'deleted': None, 'description': 'internal timeline for user-created events', 'id': 19, 'label_string': '', 'name': 'Manual events', 'searchindex': {'created_at': '2023-03-08T12:46:24.047640', 'deleted': None, 'description': 'internal timeline for user-created events', 'id': 9, 'index_name': '49a318b0ba17867fd71b50903774a0c8', 'label_string': '', 'name': 'Manual events', 'status': [{'created_at': '2023-03-17T09:35:03.202520', 'id': 87, 'status': 'ready', 'updated_at': '2023-03-17T09:35:03.202520'}], 'updated_at': '2023-03-08T12:46:24.047640', 'user': {'active': True, 'admin': True, 'groups': [], 'username': 'dev'}}, 'status': [{'created_at': '2023-03-17T09:35:03.233973', 'id': 79, 'status': 'ready', 'updated_at': '2023-03-17T09:35:03.233973'}], 'updated_at': '2023-03-08T12:46:24.472587', 'user': {'active': True, 'admin': True, 'groups': [], 'username': 'dev'}}]}
Event added to sketch: timefocus test
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