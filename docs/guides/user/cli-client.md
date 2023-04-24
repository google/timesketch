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
  -h, --help        Show this message and exit.

Commands:
  analyze         Analyze timelines.
  config          Configuration for this CLI tool.
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

Run a specific analyzer. In this example the `domain` analyzer on timeline 1:

```
timesketch analyze --analyzer domain --timeline 1
Running analyzer [domain] on [timeline 1]:
..
Results
[domain] = 217 domains discovered (150 TLDs) and 1 known CDN networks found.

```
