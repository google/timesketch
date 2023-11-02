---
hide:
  - footer
---
The feature extraction analyzer creates attributes out of event data based on regular expressions. Different
features can be specified in the `data/regex_features.yaml` file.

Please be aware that this analyzer does *not* extract ipv4, email-addresses and similar from *all* events, but only those that match the query_string.

### Use case

This analyzer is helpful to built a list of `email_addresses` in a sketch that are used in in `WEBHIST`. To do that, run the analyzer to have the feature extracted. Check the results by running a query: `email_address:*`.

Those results now can be used in an aggregation to plot a table limited to that column.

Another way of extracting that information is via API, querying events that contain `email_address:*` as a pandas dataframe, and work from there.

### Configuration

A feature extraction definition looks like this:

```
name:
       # Define either a query_string or query_dsl.
       query_string: *
       query_dsl:
       # Mandatory fields.
       attribute:
       store_as:
       re:
       # Optional fields.
       re_flags: []
       emojis: []
       tags: []
       create_view: False
       aggregate: False
       overwrite_store_as: True
       overwrite_and_merge_store_as: False
       store_type_list: False
       keep_multimatch: False
```

Each definition needs to define either a query_string or a query_dsl.

`re_flags` is a list of flags as strings from the re module. These include:
- DEBUG
- DOTALL
- IGNORECASE
- LOCALE
- MULTILINE
- TEMPLATE
- UNICODE
- VERBOSE

The fields `tags` and `emojis` are optional.

The field `store_as` defines the name of the attribute the feature is stored as.

The `create_view` is an optional boolean that determines whether a view should be created if there are hits.

The `aggregate` is an optional boolean that determines if we want to create an aggregation of the results and store it (ATM this does nothing, but once aggregations are supported it will).

The `overwrite_store_as` is an optional boolean that determines if we want to overwrite the field `store_as` if it already exists.

The `overwrite_and_merge_store_as` is an optional boolean that determines  if we want to overwrite the field `store_as` and merge the existing values.

The `store_type_list` is an optional boolean that determines if we want to store the extracted data in List type (default is text).

The `keep_multimatch` is an optional boolean that determines if we want to store all matching results (default store first result).

The feature extraction works in the way that the query is run, and the regular expression is run against the attribute to extract a value.
The first value extracted is then stored inside the "store_as" attribute.
If there are emojis or tags defined they are also applied to that event.
In the end, if a view is supposed to be created a view searching for the added tag is added (only if there are results).
