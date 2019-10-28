# Create timeline from JSONL or CSV file

You can ingest timeline data from a JSONL or CSV file. You can have any number of attributes/columns as you wish but there are some mandatory fields that Timeksketch needs in order to render the events in the UI.

**Mandatory fields:**
* message
   * String with an informative message of the event
* datetime
   * ISO8601 format
   * Ex: 2015-07-24T19:01:01+00:00
* timestamp_desc
   * String explaining what type of timestamp it is. E.g file created
   * Ex: "Time created"

## Example CSV file
You need to provide the CSV header with the column names as the first line in the file.

    message,timestamp,datetime,timestamp_desc,extra_field_1,extra_field_2
    A message,1331698658276340,2015-07-24T19:01:01+00:00,Write time,foo,bar
    ...


## Example JSONL file
Unlike JSON files, imports in JSONL format can be streamed from disk, making them far less memory intensive than regular JSON files.

    {"message": "A message","timestamp": 123456789,"datetime": "2015-07-24T19:01:01+00:00","timestamp_desc": "Write time","extra_field_1": "foo"}
    {"message": "Another message","timestamp": 123456790,"datetime": "2015-07-24T19:01:02+00:00","timestamp_desc": "Write time","extra_field_1": "bar"}
    {"message": "Yet more messages","timestamp": 123456791,"datetime": "2015-07-24T19:01:03+00:00","timestamp_desc": "Write time","extra_field_1": "baz"}

## Using tsctl To Import Files

The command line tool `tsctl` can be used to import timelines from files. To get access to the help file for the tool use:

```
$ tsctl import -?
usage: tsctl import [-?] --file FILE_PATH [--sketch_id SKETCH_ID]
                    [--username USERNAME] [--timeline_name TIMELINE_NAME]

Create a new Timesketch timeline from a file.

optional arguments:
  -?, --help            show this help message and exit
  --file FILE_PATH, -f FILE_PATH
  --sketch_id SKETCH_ID, -s SKETCH_ID
  --username USERNAME, -u USERNAME
  --timeline_name TIMELINE_NAME, -n TIMELINE_NAME
```

An example command line to import a JSON lines file is:

```
$ tsctl import --sketch_id <SKETCH_ID> --file <FILENAME>.jsonl --timeline_name <NAME_FOR_TIMELINE> --username <USER>

Imported /PATH/FILENAME.jsonl to sketch: SKETCH_ID (<SKETCH_DESCRIPTION>)
```

or an example:

```
$ tsctl import --sketch_id 1 --file foo.jsonl --timeline_name testing --username dev
Imported /tmp/foo.jsonl to sketch: 1 (My very first sketch)
```

or:
```
$ tsctl import --sketch_id 1 --file foo.csv --timeline_name testing_csv --username dev
Imported /tmp/foo.csv to sketch: 1 (My very first sketch)
```
