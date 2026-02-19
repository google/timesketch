---
hide:
  - footer
---
# Create timeline from JSONL or CSV file

You can ingest timeline data from a JSONL or CSV file. You can have any number of attributes/columns as you wish but there are some mandatory fields that Timesketch needs in order to render the events in the UI.

**Mandatory fields:**

- `message` String with an informative message of the event
- `datetime` ISO8601 format for example: `2015-07-24T19:01:01+00:00`
- `timestamp_desc` String explaining what type of timestamp it is for example `file created`

If one or more of these fields are missing in the CSV/JSONL, you can still submit the file using the functionality **headers mapping**.

## Headers Mapping via UI

This section explains how you can map a missing mandatory header. This functionality allows you to map the mandatory fields with one or more existing headers found in the CSV or in a JSONL file.


In a few words, there are two different manners: using a drop down menu, or using a list of checkboxes.

![MappingFinished](https://user-images.githubusercontent.com/108743205/184672045-ab540bdb-b452-412e-9d49-63ef1d82ae49.png)

* When choosing the mapping from the dropdown menu, you have two options:
    * Map the missing header with an existing field found in the CSV or JSONL, or
    * Instruct the server to create a new column with a default value specified by the user.
For example, in the above figure, we mapped the `datetime` header to the `data_UtcTime` one. For the timestamp_desc field we decided to create a new column. The Server will interpret these mapping in this way: it will rename the CSV or JSONL header data_UtcTime into datetime, and it will create the timestamp_desc column with a default value “sysmon_event”.
* When choosing the mapping from the checkboxes list, you can select multiple CSV headers that the server will combine into a single column named as the mandatory header. The server will not delete the selected columns. For example, in the above figure, we mapped the field `message` to 4 different headers. The server will create a new column named `message` where each row will contain the combination of the values of the selected fields.

## Filename

The filename must end with `.csv / .jsonl` otherwise the import will fail.

## Example CSV file

You should provide the CSV header with the column names as the first line in the file.

    message,timestamp,datetime,timestamp_desc,extra_field_1,extra_field_2
    A message,1331698658276340,2015-07-24T19:01:01+00:00,Write time,foo,bar
    ...

Using the headers mapping functionality, you can still submit a CSV file without the mandatory fields. The uploaded file should have those headers whose semantic meaning is correlated to the ones of `message`, `datetime` and `timestamp_desc`.

## Example JSONL file

Unlike JSON files, imports in JSONL format can be streamed from disk, making them far less memory intensive than regular JSON files.

    {"message": "A message","timestamp": 123456789,"datetime": "2015-07-24T19:01:01+00:00","timestamp_desc": "Write time","extra_field_1": "foo"}
    {"message": "Another message","timestamp": 123456790,"datetime": "2015-07-24T19:01:02+00:00","timestamp_desc": "Write time","extra_field_1": "bar"}
    {"message": "Yet more messages","timestamp": 123456791,"datetime": "2015-07-24T19:01:03+00:00","timestamp_desc": "Write time","extra_field_1": "baz"}

Similar to a CSV file, you can upload the JSONL file even if it does not have the required headers. However, the uploaded file should have those headers whose semantic meaning is correlated to the ones of `message`, `datetime` and `timestamp_desc`.

## Handling Large String Fields

OpenSearch has a hard limit of **32,766 bytes** for "keyword" fields. Keyword fields are used for exact matching, sorting, and aggregations (charts).

If an imported file contains a field that exceeds this limit (e.g., a very long feature vector or a massive blob of text), OpenSearch would normally reject the entire event with a `max_bytes_length_exceeded_exception`.

Timesketch handles this by using a `dynamic_template` with an `ignore_above: 256` setting. This means:
*   Fields longer than 256 characters are still indexed as **text** (and are therefore searchable).
*   However, the **keyword** sub-field is not created for those specific long values.
*   **Impact:** You can search for the content of these large fields, but you cannot use them in aggregations (charts) or sort by them if they exceed the limit.

## Upload the file to Timesketch

To create a new timeline in Timesketch you need to upload it to the server.

[See here for instructions to do so](/guides/user/upload-data/)
