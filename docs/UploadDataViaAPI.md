# Create Timeline From Other Sources

Not all data comes in a good [CSV or JSONL
format](docs/CreateTimelineFromJSONorCSV.md) that can be imported
directly into Timesketch. In those cases it might be beneficial
to have a separate importer in Timesketch that can deal with arbitrary data, for
instance if there is already a python library to parse the data, or the data can
be read in another format, such as a [pandas
DataFrame](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.html).

Let's look at how to import data using the API client.

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
[documentation]((docs/CreateTimelineFromJSONorCSV.md). We don't really need to
add them here, we can do that all in our upload stream. Let's start by
connecting to a Timesketch instance.

```
import pandas as pd

from timesketch_api_client import client

...
def action():
  frame = pd.read_excel('~/Downloads/SomeRandomDocument.xlsx')

  ts = client.TimesketchApi(SERVER_LOCATION, USERNAME, PASSWORD)
  my_sketch = ts.get_sketch(SKETCH_ID)

  with client.UploadStreamer() as streamer:
    streamer.set_sketch(my_sketch)
    streamer.set_timestamp_description('Web Log')
    streamer.set_timeline_name('excel_import')
    streamer.set_message_format_string(
        '{What:s} resulted in {Results:s}, pointed from {URL:s}')

    streamer.add_data_frame(frame)
```

Let's go over the functionality of the streamer a bit. A streamer is opened
using the `with` statement in Python, which returns back an object. Before you
can use the streamer you'll have to configure it:

 + Add a sketch object to it, this will be the sketch used to upload the data
   to.
 + Set the `timestamp_desc` field using the
   `streamer.set_timestamp_description`. The content of this string will be used
   for the `timestamp_desc` field, if it doesn't already exist.
 + Set the name of the imported timeline.
 + Set a format message string. Timesketch expects one field, called `message`
   to exist. If it does not exist, a format message string needs to be defined
   that can be used to generate the messsage field. This is basically a python
   [formatting string](https://pyformat.info/) that uses the name of each column
   as a variable name, eg. `"{src_ip:s} connected to {dst_ip:s}"` means that the
   content in the column name `src_ip` will be formatted as a string and
   replaces the `{src_ip:s}` in the format string. So if you have a row that
   contains the variables: `src_ip = "10.10.10.10", dst_ip = "8.8.8.8"` then the
   message string will look like: `10.10.10.10 connected to 8.8.8.8`.
 + Call any of the `streamer.add_` functions to add data.

 The data that can be added to the streamer are:

 + Pandas DataFrame.
 + A CSV, JSONL or a Plaso file.
 + A dictionary, one for each row in the dataset.

Let's take another example of how the streamer is used to add content using the
dictionary approach.

```
...
from scapy import all as scapy_all
...

packets = scapy_all.rdpcap(fh)

with client.UploadStreamer() as streamer:
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
