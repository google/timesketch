# Index Mappings

OpenSearch index mappings define how documents and their fields are stored and
indexed. In Timesketch, these mappings are crucial for ensuring that data from
various sources (like Plaso, CSV, or JSONL) is searchable, filterable, and
correctly typed.

## How Timesketch Uses Mappings

When a new timeline is created (e.g., during a Plaso or CSV import), Timesketch
creates a new OpenSearch index per import type (Plaso or CSV/JSONL). The schema
for this index is defined by mapping files located in the `data/` directory of
the repository.

*   **[plaso.mappings](https://github.com/google/timesketch/blob/master/data/plaso.mappings)**: Used for `.plaso` file imports.
*   **[generic.mappings](https://github.com/google/timesketch/blob/master/data/generic.mappings)**: Used for CSV and JSONL file imports.

These files contain [OpenSearch Index Mappings](https://opensearch.org/docs/latest/field-types/index/)
that tell OpenSearch how to treat specific field names.

## Key Field Types and Tuning

Understanding the difference between field types is essential for tuning your
Timesketch instance.

### Keyword vs. Text
*   **[Keyword](https://opensearch.org/docs/latest/field-types/supported-field-types/keyword/)**: Used for exact matches, sorting, and aggregations (e.g., IDs, usernames, filenames).
*   **[Text](https://opensearch.org/docs/latest/field-types/supported-field-types/text/)**: Used for full-text search. The content is analyzed (tokenized into words) before indexing.
*   **[Wildcard](https://docs.opensearch.org/latest/mappings/supported-field-types/wildcard/)**: Used for substring search.

In Timesketch, many fields are mapped as both `text` (for searching) and `keyword`
(for filtering) using multi-fields.

### The `ignore_above` Limitation
By default, Timesketch (and OpenSearch) sets `ignore_above: 256` for `keyword` sub-fields.

```json
"keyword": {"type": "keyword", "ignore_above": 256}
```

**What this means for a Timesketch user:**
If a field's value exceeds 256 characters, OpenSearch will **not index it as a keyword**.
*   **Impact:** The event will still be searchable via full-text search, but it will **not appear** in filter results or exact match queries targeting the `.keyword` sub-field.
*   **Adjustment:** If you have long fields (e.g., long URLs or command lines) that you need to filter on exactly, you may need to increase this limit in the mapping files. Note that increasing this significantly can increase index size and memory usage.

### Wildcard Matches in Keyword Fields

Historically, `keyword` fields were used in Timesketch to perform wildcard
matches (e.g., `message.keyword:*searchterm*`). While effective for short
strings, this becomes slow and resource-intensive on large datasets or long
strings.

## Native Wildcard Search Mode

Timesketch now includes a dedicated **Wildcard Search Mode** that leverages the
OpenSearch `wildcard` field type.

### How it works
The `plaso.mappings` and `generic.mappings` files now include a `wildcard`
sub-field for string data:

```json
"fields": {
    "keyword": {"type": "keyword", "ignore_above": 256},
    "wildcard": {"type": "wildcard"}
}
```

The [Wildcard Field Type](https://opensearch.org/docs/latest/field-types/supported-field-types/wildcard/)
is optimized for leading and trailing wildcard patterns.

### Enabling Wildcard Search

When using the Timesketch API or the Search UI, you can enable "Wildcard Search
Mode". When active:

1.  Timesketch inspects the index mappings to see which fields support the `wildcard` type.
2.  It translates your query into native OpenSearch `wildcard` queries targeting those sub-fields.
3.  This results in faster and more reliable wildcard matching compared to traditional keyword-based regex searches.

## Applying Changes to Mappings

If you modify `plaso.mappings` or `generic.mappings`:

1.  **New Timelines:** The changes will apply automatically to any timeline created *after* the file was updated.
2.  **Existing Timelines:** Mappings are immutable in OpenSearch. To apply changes to existing data, you must either:
    *   Delete the timeline and re-import it.
    *   Use the OpenSearch [Reindex API](https://opensearch.org/docs/latest/api-reference/document-apis/reindex/) to move data to a new index with the updated schema.

For more advanced configurations, refer to the [official OpenSearch documentation on Mappings](https://opensearch.org/docs/latest/field-types/index/).
