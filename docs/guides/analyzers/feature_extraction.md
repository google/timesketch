## Feature extraction analyzer

The feature extraction analyzer creates attributes out of event data based on regex. Different
features can be specified in the `data/features.yaml` file.

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