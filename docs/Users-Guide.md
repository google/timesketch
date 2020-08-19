## Table of Contents

- [Table of Contents](#table-of-contents)
- [Concepts](#concepts)
  - [Sketches](#sketches)
  - [Adding Timelines](#adding-timelines)
  - [Adding event](#adding-event)
  - [Views](#views)
    - [Hiding events from a view](#hiding-events-from-a-view)
  - [Heatmap](#heatmap)
  - [Stories](#stories)
- [Demo](#demo)
- [tsctl](#tsctl)
  - [Start timesketch](#start-timesketch)
  - [User management](#user-management)
    - [Adding users](#adding-users)
    - [Change user password](#change-user-password)
    - [Removing users](#removing-users)
  - [Group management](#group-management)
    - [Adding groups](#adding-groups)
    - [Removing groups](#removing-groups)
    - [Managing group membership](#managing-group-membership)
  - [add_index](#add_index)
  - [Migrate db](#migrate-db)
  - [Drop database](#drop-database)
  - [Import json to Timesketch](#import-json-to-timesketch)
  - [Purge](#purge)
  - [search_template](#search_template)
  - [import](#import)
  - [similarity_score](#similarity_score)
- [Searching](#searching)
- [Analyzers](#analyzers)
  - [Develop Analyzers](#develop-analyzers)
  - [Analyzer description](#analyzer-description)
    - [Browser Search Analyzer](#browser-search-analyzer)
    - [Browser Timeframe Analyzer](#browser-timeframe-analyzer)
    - [Chain analyzer](#chain-analyzer)
    - [Domain Analyzer](#domain-analyzer)
    - [Windows EVTX Sessionizer](#windows-evtx-sessionizer)
    - [Windows EVTX Gap analyzer](#windows-evtx-gap-analyzer)
    - [Safebrowsing Analyzer](#safebrowsing-analyzer)
    - [Sigma Analyzer](#sigma-analyzer)
    - [YetiIndicators Analyzer](#yetiindicators-analyzer)

## Concepts

Timesketch is built on multiple sketches, where one sketch is usually one case.
Every sketch can consist of multiple timelines with multiple views.

### Sketches

There is a dedicated document to walk you through [Sketches](/docs/SketchOverview.md)
### Adding Timelines

- [Create timeline from JSON/JSONL/CSV file](/docs/CreateTimelineFromJSONorCSV.md)
- [Create timeline from Plaso file](/docs/CreateTimelineFromPlaso.md)
- [Enable Plaso upload via HTTP](/docs/EnablePlasoUpload.md)

### Adding event

*This feature is currently not implemented in the Web UI*

~~To manually add an event, visit the sketch view. Within that screen, there is the possibility to star an event, hide an event as well as add a manual event (marked with a little +).
This event will have the previously selected time pre-filled but can be changed.~~

### Views

#### Hiding events from a view

All about reducing noise in the result views.
Hit the little eye to hide events from the list making it possible to
curate views to emphasize the important things.
The events are still there and can be easily shown for those who want to see them.
Hit the big red button to show/hide the events.

### Heatmap

*This feature is currently not implemented in the Web UI*

~~The heatmap aggregation calculates on which day of the week and at which hour events happened. This can be very useful e.g. when analyzing lateral movement or login events.~~

### Stories

A story is a place where you can capture the narrative of your technical investigation and add detail to your story with raw timeline data.
The editor lets you to write and capture the story behind your investigation and at the same time enable you to share detailed findings without spending hours writing reports.

you can add events from previously saved searches.
Just hit enter to start a new paragraph and choose the saved search from the dropdown menu.

See [Medium article](https://medium.com/timesketch/timesketch-2016-7-db3083e78156)


## Demo

To play with timesketch without any installation visit [demo.timesketch.org](https://demo.timesketch.org)

## tsctl

tsctl is a command line tool to control timesketch.

Parameters:

```shell
--config / -c (optional)
```

Example

```shell
tsctl runserver -c /etc/timesketch/timesketch.conf
```

### Start timesketch

Will start the timesketch server

Command:
```shell
tsctl runserver
```

### User management

#### Adding users

Command:
```
tsctl add_user
```

Parameters:
```
--name / -n
--password / -p (optional)
```

Example
```
tsctl add_user --name foo
```

#### Change user password

To change a user password, the add_user command can be used, as it is checking if the user exists if yes it will update the update.

Command:
```
tsctl add_user
```

Parameters:
```
--username / -u
--password / -p (optional)
```

Example
```
tsctl add_user --username foo
```

#### Removing users

Not yet implemented.

### Group management

#### Adding groups

Command:

```shell
tsctl add_group
```

Parameters:

```shell
--name / -n
```

#### Removing groups

Not yet implemented.

#### Managing group membership

Add or remove a user to a group. To add a user, specify the group and user. To
remove a user, include the -r option.

Command:

```shell
tsctl manage_group
```

Parameters:

```shell
--remove / -r (optional)
--group / -g
--user / -u
```

Example:

```shell
tsctl manage_group -u user_foo -g group_bar
```

### add_index

Create a new Timesketch searchindex.

Command:

```shell
tsctl add_index
```

Parameters:

```shell
--name / -n
--index / -i
--user / -u
```

Example:

```shell
tsctl add_index -u user_foo -i test_index_name -n sample
```

### Migrate db

Command:

```shell
tsctl db
```

### Drop database

Will drop all databases.

Comand:

```shell
tsctl drop_db
```

### Import json to Timesketch

Command:

```shell
tsctl json2ts
```

### Purge

Delete timeline permanently from Timesketch and Elasticsearch. It will alert if a timeline is still in use in a sketch and prompt for confirmation before deletion.

````
 Args:
   index_name: The name of the index in Elasticsearch
````

Comand:

```shell
tsctl purge
```

### search_template

Export/Import search templates to/from file.

Command:

```shell
tsctl search_template
```

Parameters:

```shell
--import / -i
--export / -e
```

import_location: Path to the yaml file to import templates.
export_location: Path to the yaml file to export templates.

### import

Creates a new Timesketch timeline from a file. Supported file formats are: plaso, csv and jsonl.

Command:

```shell
tsctl import
```

Parameters:

```shell
--file / -f
--sketch_id / -s      (optional)
--username / -f       (optional)
--timeline_name / -n  (optional)
```

The sketch id is inferred from the filename if it starts with a number. The timeline name can also be generated from the filename if not specified.

### similarity_score

Command:

```shell
tsctl similarity_score
```

## Searching

There is a dedicated document called [SearchQueryGuide](/docs/SearchQueryGuide.md) to help you create custom searches.

All data within Timesketch is stored in elasticsearch. So the search works similar to ES.

Using the advances search, a JSON can be passed to Timesketch

```json
{
 "query": {
   "bool": {
     "must": [
       {
         "query_string": {
           "query": "*"
         }
       }
     ]
   }
 },
 "sort": {
   "datetime": "asc"
 }
}
```

## Analyzers

With Analyzers you can enrich your data in timelines. The analysers are written in Python.

The systems consist of a set of background workers that can execute Python code on a stream of events. It provides an easy to use API to programmatically do all the actions available in the UI, e.g. tagging events, star and create saved views etc. The idea is to automatically enrich data with encoded analysis knowledge.

The code for Analyzers is located at

```shell
/timesketch/lib/analyzers
```

### Develop Analyzers

There is a dedicated document to walk you through the process of developing [Analyzers](/docs/WriteAnalyzers.md)

### Analyzer description

*Note:* Not all analyzers are explained in this documentation. If you have questions to a particular analyzer, please have a look at the code or file an Issue on Github.

#### Browser Search Analyzer

The browser search analyzer takes URLs usually reserved for browser search queries and extracts the search string.

It will also tell in a story:

- The top 20 most commonly discovered searches
- The domains used to search
- The most common days of search
- And an overview of all the discovered search terms

#### Browser Timeframe Analyzer

The browser time frame analyzer discovers browser events that occurred outside of the typical browsing window of this browser history.

The analyzer determines the activity hours by finding the frequency of browsing events per hour, and then discovering the longest block of most active hours before proceeding with flagging all events outside of that time period. This information can be used by other analyzers or by manually looking for other activity within the inactive time period to find unusual actions.

#### Chain analyzer

Sketch analyzer for chained events

The purpose of the chain analyzer is to chain together events that can be described as linked, either by sharing some common entities, or one event being a derivative of another event. An example of this would be that a browser downloads an executable, which then later gets executed.

The signs of execution could lie in multiple events, from different sources, but they are all linked or chained together. This could help an analyst see the connection between these separate but chained events. Another example could be a document written and then compressed into a ZIP file, which would then be exfilled through some means. If the document and the ZIP file are chained together it could be easier for the analyst to track the meaning of an exfil event involving the compressed file.

#### Domain Analyzer

The Domain Analyzer extracts domain and TLD info from events that have a field with either ```url``` or ```domain```.

It will also add information about:

- Known CDN providers (based on Timesketch config)

#### Windows EVTX Sessionizer

This Analyzer will determine the start and end event for a user session based on EVTX events.

#### Windows EVTX Gap analyzer

It attempts to detect gaps in EVTX files found in an index  using two different methods.

First of all it looks at missing entries in record numbers and secondly it attempts to look at gaps in days with no records.

This may be an indication of someone clearing the logs, yet it may be an indication of something else. At least this should be interpreted as something that warrants a second look.

This will obviously not catch every instance of someone clearing EVTX records, even if that's done in bulk. Therefore it should not be interpreted that if this analyzer does not discover something that the records have not been wiped. Please verify the results given by this analyzer.

#### Safebrowsing Analyzer

This Analyzer checks urls found in a sketch against the [Google Safebrowsing API](https://developers.google.com/safe-browsing/v4/reference/rest).

To use this Analyzer, the following parameter must be set in the ````timesketch.conf````:

````config
SAFEBROWSING_API_KEY = ''
````

This analyzer can be customized by creating an optional file containing URL wildcards to be allow listed called

````config
safebrowsing_allowlist.yaml
````

There are also two additional config parameters, please refer to the [Safe Browsing API reference](https://developers.google.com/safe-browsing/v4/reference/rest).

 
Platforms to be looked at in Safe Browsing (PlatformType).
````SAFEBROWSING_PLATFORMS = ['ANY_PLATFORM']````

Types to be looked at in Safe Browsing (ThreatType).
````SAFEBROWSING_THREATTYPES = ['MALWARE']````

#### Sigma Analyzer

The Sigma Analyzer translates Sigma rules in Elastic Search Queries and adds a tag to every matching event.

It will also create a story with the Top 10 matched Sigma rules.

There is a dedicated document to walk you through the process of using the [Sigma Analyzer](/docs/UseSigmaAnalyzer.md).

#### YetiIndicators Analyzer

This is a Index analyzer for [Yeti](https://yeti-platform.github.io/) threat intel indicators.

To use this Analyzer, the following parameter must be set with corresponding values in the ````timesketch.conf````:

````config
YETI_API_ROOT = ''
YETI_API_KEY = ''
````

