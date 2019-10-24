# Create Timeline from other data

At a certain point during an investigation, data will be generated that would add value to a timeline but are not formated or covered in [Create timeline from JSON/JSONL/CSV file](docs/CreateTimelineFromJSONorCSV.md).

In first place you might be triggered to look for:

    raw_data --> timesketch

The idea from timesketch is not to copy parsing logic that is already covered in other tools, so the first look for parsing capabilities should be plaso parsing.

The ideal data-processing flow is

    raw_data --> plaso --> timesketch

The plaso parsers are listed within the [plaso documentation](https://plaso.readthedocs.io/en/latest/sources/user/Parsers-and-plugins.html)

If there is no plaso parser for your file format yet, please have a look at [how to write a plaso parser](https://plaso.readthedocs.io/en/latest/sources/developer/How-to-write-a-parser.html)

Of course the following could work as well

    raw_data --> proprietary_raw_data2csv_parser --> timesketch
    
Where proprietary_raw_data2csv_parser would not end up in timesketch repository.
