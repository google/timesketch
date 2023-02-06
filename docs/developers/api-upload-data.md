---
hide:
  - footer
---
# Create Timeline From Other Sources

Not all data comes in a good [CSV or JSONL
format](/guides/user/import-from-json-csv/) that can be imported
directly into Timesketch. Your data may lie in a SQL database, Excel sheet, or
even in CSV/JSON but it does not have the correct fields in it. In those cases
it might be beneficial to have a separate importer in Timesketch that can deal
with arbitrary data, for instance if there is already a python library to parse
the data, or the data can be read in another format, such as a [pandas
DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html).

## Disclaimer

A small disclaimer. Timesketch is not a parser, and does not intend to be a
parser. If you need to parse the data, you'll need other tools or libraries.
Parsers can be implemented using [plaso](https://github.com/log2timeline/plaso)
.

## What is the Importer Good For

The Timesketch importer is to be used for data sources that you've already
parsed or have readily available, but they are not in the correct format that
Timesketch requires or you want an automatic way to import the data, or a way to
built an importer into your already existing toolsets.

This is therefore useful for uploading CSV or JSON files, or through other code
that processes data to stream to Timesketch. The importer takes in simple
configuration parameters to make the necessary adjustments to the data so that
it can be ingested by Timesketch. In the future these adjustments will be
configurable using a config file, until then a more manual approach is needed.

## Basics

The importer will take as an input either:

- Pandas DataFrame.
- CSV or JSONL.
- JSON (one JSON per entry)
- Python dict
- Microsoft Excel spreadsheet (XLS or XLSX file).

The best way to use the streamer is to by using the the `with` statement in
Python, which returns back an object. Before you can use the streamer you'll
have to configure it:

- Add a sketch object to it, this will be the sketch used to upload the data
  to.
- Set the name of the imported timeline.
- If the data does not contain a timestamp description you'll need to set the
  `timestamp_desc` field using the `streamer.set_timestamp_description`.
  The content of this string will be used for the `timestamp_desc` field,
  if it doesn't already exist.
- If the data does not contain a column called `message` a format string can
  be supplied to automatically generate one. This is basically a python
  [formatting string](https://pyformat.info/) that uses the name of each column
  as a variable name, eg. `"{src_ip:s} connected to {dst_ip:s}"` means that the
  content in the column name `src_ip` will be formatted as a string and
  replaces the `{src_ip:s}` in the format string. So if you have a row that
  contains the variables: `src_ip = "10.10.10.10", dst_ip = "8.8.8.8"` then the
  message string will look like: `10.10.10.10 connected to 8.8.8.8`.

The reason why the `with` statement is preferred is that it ensures that the
streamer gets properly closed at the end. The streamer can be used without
the `with` statement, however the developer is then required to make sure that
the streamer's `.close()` function is called at the end.

Once the streamer is configured it can be used by calling any of the
`streamer.add_` functions to add data.

Let's look at how to import data using the importer, using each of these data
sources.

## Pandas DataFrame

DataFrames can be generated from multiple sources and methods. This
documentation is in no way, shape or form going to cover that in any sort of
details. There are plenty of guides that can be found online to help you there.

Let's just look at a simple case.

```
In [1]: import pandas as pd

In [2]: frame = pd.read_excel('~/Documents/SomeRandomDocument.xlsx')

In [3]: frame
Out[3]:
Timestamp What  URL Results
0 2019-05-02 23:21:10 Something http://evil.com Nothing to see here
1 2019-05-22 12:12:45 Other http://notevil.com  Move on
2 2019-06-23 02:00:12 Not really That http://totallylegit.com Let's not look,shall we
```

Here we have a data frame that we may want to add to our Timesketch instance.
What is missing here are few of the necessary columns, see
[documentation](/guides/user/import-from-json-csv/). We don't really need to
add them here, we can do that all in our upload stream. Let's start by
connecting to a Timesketch instance.

```python
import pandas as pd

from timesketch_api_client import config
from timesketch_import_client import importer

...
def action():
  frame = pd.read_excel('~/Downloads/SomeRandomDocument.xlsx')

  ts = config.get_client()
  my_sketch = ts.get_sketch(SKETCH_ID)

  with importer.ImportStreamer() as streamer:
    streamer.set_sketch(my_sketch)
    streamer.set_timestamp_description('Web Log')
    streamer.set_timeline_name('excel_import')
    streamer.set_message_format_string(
        '{What:s} resulted in {Results:s}, pointed from {URL:s}')

    streamer.add_data_frame(frame)
```

## Python Dict

Here is an example of how the streamer can be used to add content using the
dictionary approach.

Here we use an external library, scapy, to read a PCAP file and import the data
from the network traffic to Timesketch.

```python
...
from scapy import all as scapy_all
...

packets = scapy_all.rdpcap(~/Downloads/SomeRandomDocument.pcap)

with importer.ImportStreamer() as streamer:
  streamer.set_sketch(my_sketch)
  streamer.set_timestamp_description('Network Log')
  streamer.set_timeline_name('pcap_test_log')
  streamer.set_message_format_string(
      '{src_ip:s}:{src_port:d}->{dst_ip:s}:{dst_port:d} =
      {url:s}')

  for packet in packets:
    # do something here
    ...
    timestamp = datetime.datetime.utcfromtimestamp(packet.time)
    for k, v in iter(data.fields.items()):
      for url in URL_RE.findall(str(v)):
        url = url.strip()
        streamer.add_dict({
            'time': timestamp,
            'src_ip': packet.getlayer('IP').src,
            'dst_ip': packet.getlayer('IP').dst,
            'src_port': layer.sport,
            'dst_port': layer.dport,
            'url': url})
```

The streamer will take as an input to `add_dict` a dictionary that can contain
arbitrary field names. These will then later be transformed into a DataFrame and
then uploaded to Timesketch.

## JSON

Adding a JSON entry is identical to the dict method, except that the each
entry is stored as a separate JSON object (one entry is only a single line).

Let's look at an example:

```
# TODO: Add an example.

```

## A file, CSV, PLASO or JSONL.

Files can also be added using the importer. That is files that are
supported by Timesketch. These would be CSV, JSONL (JSON lines) and
a plaso file.

The function `add_file` in the importer is used to add a file.

Here is an example of how the importer can be used:

```python
from timesketch_api_client import config
from timesketch_import_client import importer

...

with importer.ImportStreamer() as streamer:
  streamer.set_sketch(my_sketch)
  streamer.set_timeline_name('my_file_with_a_timeline')
  streamer.set_timestamp_description('some_description')

  streamer.add_file('/path_to_file/mydump.plaso')
```

If the file that is being imported is either a CSV or a JSONL file the importer
will split the file up if it is large and send it in pieces. Each piece of the
file will be indexed as soon as it is uploaded to the backend.

In the case of a plaso file, it will also be split up into smaller chunks and
uploaded. However indexing does not start until all pieces have been transferred
and the final plaso storage file reassembled.

## Excel Sheet

```python
from timesketch_api_client import config
from timesketch_import_client import importer

...
def action():

  ts = config.get_client()
  my_sketch = ts.get_sketch(SKETCH_ID)

  with importer.ImportStreamer() as streamer:
    streamer.set_sketch(my_sketch)
    streamer.set_timestamp_description('Web Log')
    streamer.set_timeline_name('excel_import')
    streamer.set_message_format_string(
        '{What:s} resulted in {Results:s}, pointed from {URL:s}')

    streamer.add_excel_file('~/Downloads/SomeRandomDocument.xlsx')
```

## Import Data Already Ingested into OpenSearch.

You may have other mechanism to ingest data into OpenSearch, like an ELK stack or
some manual scripts that ingest the data. Since the data is already in OpenSearch
it doesn't need to be re-ingested. In order to make it accessible in Timesketch
the API client can be used.

**disclaimer:** _the data ingested needs to be in a certain format in order to
work with Timesketch. This function does limited checking before making it
available. The timeline may or may not work in Timesketch, depending on
multiple factors._

The data that is ingested needs to have few fields already set before it can be
ingested into Timesketch:

- message
- datetime
- timestamp
- timestamp_desc

The datetime field also needs to be mapped as a date, not a text string.

A sample code on how to ingest data into Timesketch that is already in OpenSearch:

- Method 1 - generate a timeline from a index in OpenSearch
- Method 2 - generate a timeline from a index in OpenSearch, that contains documents
  from multiple timelines filtered by the field `__ts_timeline_filter_id`
  (of which the fieldtype is not text but e.g. keyword, long, etc, due to usage of filter term query)

```python
from timesketch_api_client import config

ts_client = config.get_client()
sketch = ts_client.get_sketch(SKETCH_ID)
 
# Method 1 - Single timeline from a single index
sketch.generate_timeline_from_es_index(
    es_index_name=OPENSEARCH_INDEX_NAME,
    name=TIMELINE_NAME,
    provider='My Custom Ingestion Script',
    context='python my_custom_script.py --ingest',
)

# Method 2 - Multiple timelines from a single index
sketch.generate_timeline_from_es_index(
    es_index_name=OPENSEARCH_INDEX_NAME,
    name=TIMELINE_NAME,
    timeline_filter_id="1",
    provider='My Custom Ingestion Script',
    context='python my_custom_script.py --ingest',
)
```
