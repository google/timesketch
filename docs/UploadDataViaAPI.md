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

