# Create timeline from JSON/JSONL/CSV file

You can ingest timeline data from a JSON, JSONL or CSV file. You can have any number of attributes/columns as you wish but there are some mandatory fields that Timeksketch needs in order to render the events in the UI.

**Mandatory fields:**
* message
 - String with an informative message of the event
* timestamp
 - Timestamp as microseconds since Unix epoch
 - Ex: 1331698658276340
* datetime
 - ISO8601 format
 - Ex: 2015-07-24T19:01:01+00:00
* timestamp_desc
 - String explaining what type of timestamp it is. E.g file created
 - Ex: "Time created"

## Example CSV file
You need to provide the CSV header with the column names as the first line in the file.

    message,timestamp,datetime,timestamp_desc,extra_field_1,extra_field_2
    A message,1331698658276340,2015-07-24T19:01:01+00:00,Write time,foo,bar
    ...


## Example JSON file
NOTE: In order to import a file in JSON format we must read in the whole file in memory. This is not optimal if the file to be imported is big. In that case you should convert it to a CSV file and import that.

    [
     {
      "message": "A message",
      "timestamp": 123456789,
      "datetime": "2015-07-24T19:01:01+00:00",
      "timestamp_desc": "Write time",
      "extra_field_1": "foo",
      "extra_field_2": "bar",
     },
     ...
    ]

## Example JSONL file
Unlike JSON files, imports in JSONL format can be streamed from disk, making them far less memory intensive than regular JSON files.

    {"message": "A message","timestamp": 123456789,"datetime": "2015-07-24T19:01:01+00:00","timestamp_desc": "Write time","extra_field_1": "foo"}
    {"message": "Another message","timestamp": 123456790,"datetime": "2015-07-24T19:01:02+00:00","timestamp_desc": "Write time","extra_field_1": "bar"}
    {"message": "Yet more messages","timestamp": 123456791,"datetime": "2015-07-24T19:01:03+00:00","timestamp_desc": "Write time","extra_field_1": "baz"}

Then you can create a new Timesketch timeline from the file:

    $ tsctl csv2ts --name my_timeline --file timeline.csv
    $ tsctl json2ts --name my_timeline --file timeline.json
    $ tsctl jsonl2ts --name my_timeline --file timeline.jsonl
