## Table of Contents
- [Table of Contents](#table-of-contents)
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
- [Concepts](#concepts)
  - [Sketches](#sketches)
  - [Adding Timelines](#adding-timelines)
  - [Adding event](#adding-event)
  - [Views](#views)
    - [Hiding events from a view](#hiding-events-from-a-view)
  - [Heatmap](#heatmap)
  - [Stories](#stories)
- [Searching](#searching)


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
tsctl runserver -c /etc/timesketch/timesketch.conf
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
```
tsctl add_group
```

Parameters:
```
--name / -n
```

#### Removing groups

Not yet implemented.

#### Managing group membership

Add or remove a user to a group. To add a user, specify the group and user. To
remove a user, include the -r option.

Command:
```
tsctl manage_group
```

Parameters:
```
--remove / -r (optional)
--group / -g
--user / -u
```

Example:
```
tsctl manage_group -u user_foo -g group_bar
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

Delete timeline permanently from Timesketch and Elasticsearch. It will alert if a timeline is still in use in a sketch and promt for confirmation before deletion.

	Args:
		index_name: The name of the index in Elasticsearch

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

### import

Creates a new Timesketch timeline from a file. Supported file formats are: plaso, csv and jsonl.

Command:
```
tsctl import
```

Parameters:
```
--file / -f
--sketch_id / -s      (optional)
--username / -f       (optional)
--timeline_name / -n  (optional)
```

The sketch id is inferred from the filename if it starts with a number. The timeline name can also be generated from the filename if not specified.


### similarity_score

Command:
```
tsctl similarity_score
```

## Concepts

Timesketch is built on multiple sketches, where one sketch is usually one case.
Every sketch can consist of multiple timelines with multiple views.

### Sketches

There is a dedicated document to walk you through [Sketches](/docs/SketchOverview.md)

### Adding Timelines

* [Create timeline from JSON/JSONL/CSV file](/docs/CreateTimelineFromJSONorCSV.md)
* [Create timeline from Plaso file](/docs/CreateTimelineFromPlaso.md)
* [Enable Plaso upload via HTTP](/docs/EnablePlasoUpload.md)

### Adding event

*This feature is currently not implemented in the Web UI*

~~To manually adding an event, visit the sketch view. Within that screen, there is the possibility to star an event, hide an event as well as add a manual event (marked with a little +).
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
The editor let you to write and capture the story behind your investigation and at the same time enable you to share detailed findings without spending hours writing reports.

you can add events from previously saved searches.
Just hit enter to start a new paragraph and choose the saved search from the dropdown menu.

See [Medium article](https://medium.com/timesketch/timesketch-2016-7-db3083e78156)

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
