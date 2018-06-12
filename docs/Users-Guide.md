## Table of Contents
1. [Demo](#demo)
2. [tsctl](#tsctl)
   - [Start timesketch](#start-timesketch)
   - [User management](#user-management)
     - [Adding users](#adding-users)
     - [Removing users](#removing-users)
   - [Group Management](#group-management)
     - [Adding groups](#adding-groups)
     - [Removing groups](#removing-groups)
     - [Managing group membership](#managing-group-membership)
   - [Add index](#add_index)
   - [Migrate database](#migrate-db)
   - [Drop database](#drop-database)
   - [Import JSON to timesketch](#import-json-to-timesketch)
   - [Purge](#purge)
   - [Search template](#search_template)
   - [similarity_score](#similarity_score)
3. [Concepts](#concepts)
   - [Adding Timelines](#adding-timelines)
   - [Using Stories](#stories)
   - [Adding event](#adding-event)
4. [Searching](#searching)


## Demo

To play with timesketch without any installation visit [demo.timesketch.org](https://demo.timesketch.org)

## tsctl

tsctl is a command line tool to control timesketch.

Parameters:
```
--config / -c (optional)
```

Example
```
tsctl runserver -c /etc/timesketch.conf
```


### Start timesketch

Will start the timesketch server

Command:
```
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

#### Removing users

Not yet implemented.

### Group management

#### Adding groups

Command:
```
tsctl add_group
```

Parameters:
```
--name / -n
```

#### Removing groups

Not yet implemented

#### Managing group membership

Add or remove a user to a group

Command:
```
tsctl manage_group
```

Parameters:
```
--add / -a
--remove / -r
--group / -g
--user / -u
```

Example:
```
tsctl manage_group -a -u user_foo -g group_bar
```

### add_index

Create a new Timesketch searchindex.

Command:
```
tsctl add_index
```

Parameters:
```
--name / -n
--index / -i
--user / -u
```

Example:
```
tsctl add_index -u user_foo -i test_index_name -n sample
```

### Migrate db

Command:
```
tsctl db
```

### Drop database

Will drop all databases.

Comand:
```
tsctl drop_db
```

### Import json to Timesketch

Command:
```
tsctl json2ts
```

### Purge

Comand:
```
tsctl purge
```

### search_template

Export/Import search templates to/from file.

Command:
```
tsctl search_template
```

Parameters:
```
--import / -i
--export / -e
```

import_location: Path to the yaml file to import templates.
export_location: Path to the yaml file to export templates.

### similarity_score

Command:
```
tsctl similarity_score
```

## Concepts

Timesketch is built on multiple sketches, where one sketch is ussually one case.
Every sketch can consist of multiple timelines with multiple views.

### Sketches

### Adding Timelines

* [Create timeline from JSON/JSONL/CSV file](docs/CreateTimelineFromJSONorCSV.md)
* [Create timeline from Plaso file](docs/CreateTimelineFromPlaso.md)
* [Enable Plaso upload via HTTP](docs/EnablePlasoUpload.md)

### Adding event

To manually adding an event, visit the sketch view. Within that screen, there is the possibility to star an event, hide an event as well as add a manual event (marked with a little +).
This event will have the previously selected time pre-filled but can be changed.

### Views

#### Hiding events from a view

All about reducing noise in the result views.
Hit the little eye to hide events from the list making it possible to
curate views to emphasize the important things.
The events are still there and can be easily shown for those who want to see them.
Hit the big red button to show/hide the events.

### Heatmap

The heatmap aggregation calculates on which day of the week and at which hour events happened. This can be very useful e.g. when analyzing lateral movement or login events.

### Stories

A story is a place where you can capture the narrative of your technical investigation and add detail to your story with raw timeline data.
The editor let you to write and capture the story behind your investigation and at the same time enable you to share detailed findings without spending hours writing reports.

you can add events from previously saved searches.
Just hit enter to start a new paragraph and choose the saved search from the dropdown menu.

See [Medium article](https://medium.com/timesketch/timesketch-2016-7-db3083e78156)

## Searching

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
