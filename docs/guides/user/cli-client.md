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
  --output-format TEXT    Set output format (overrides global setting)
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

## Run analyzers

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

Run a specific analyzer. In this example the `domain` analyzer on timeline 1:

```
timesketch analyze --analyzer domain --timeline 1
Running analyzer [domain] on [timeline 1]:
..
Results
[domain] = 217 domains discovered (150 TLDs) and 1 known CDN networks found.

```

## Events

### Add manual events

This feature allows users to add events to their Timesketch account using the `events add` command. The command takes three arguments: `message, date, timestamp-desc` and an optional field for `attributes`. The message is a short description of the event, the date is the date and time the event occurred, and the attributes are a list of key-value pairs that will be associated with the event.

`timestamp_desc` is a field that is used to describe the timestamp of an event. This field can be helpful for providing context about the event, such as the type of event or the source of the data.

For example, you could use the `timestamp_desc` field to specify that an event is a "Windows Sysmon event" or a "Netflow event." This information can be helpful for quickly identifying and understanding the events in a timeline.

For example, the following command would add an event to the Timesketch `timesketch events add --message "foobar-message" --date 2023-03-04T11:31:12 --timestamp-desc "test" --attributes key=value,key2=value2`:

This new feature makes it easy to add events to Timesketch from the command line, which can be helpful for automating tasks or for quickly adding events when you don't have access to the Timesketch web interface.

It can also be called with a output format `json` like following.

```timesketch events add --message "foobar-message" --date 2023-03-04T11:31:12 --timestamp-desc "test" --output-format json
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