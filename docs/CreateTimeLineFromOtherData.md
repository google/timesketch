# Create Timeline from other data

At a certain point during an investigation, data will be generated that would add value to a timeline but are not formated or covered in [Create timeline from JSON/JSONL/CSV file](docs/CreateTimelineFromJSONorCSV.md).

The idea from timesketch is not to copy parsing logic that is already covered in other tools, so the first look for parsing capabilities should be plaso parsing.

The plaso parsers are listed within the [plaso documentation](https://plaso.readthedocs.io/en/latest/sources/user/Parsers-and-plugins.html)

If there is no plaso parser for your file format yet, please have a look at [how to write a plaso parser](https://plaso.readthedocs.io/en/latest/sources/developer/How-to-write-a-parser.html)
