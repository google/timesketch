---
hide:
  - footer
---
# Search within timeline

## Search queries

Timesketch allows full text search within timelines. Good way to get started is by selecting one of pre-set search templates and adjusting them to the data in your timeline.

Simple search queries relies on[ Query String Query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html) mini-language, but it is also possible to use the full potential of OpenSearch query language in Advanced queries.

### Common fields

Data fields will vary depending on the source being uploaded, but here are some that are mandatory, and therefore will be present in any timeline.

| Field            | Description                                    | Example query                                |
| ---------------- | ---------------------------------------------- | -------------------------------------------- |
| `message`        | String with information about event            | `message:”This is a message”`                |
| `timestamp`      | Timestamp as microseconds since Unix epoch     | `timestamp:”363420000”`                      |
| `datetime`       | Date and time in ISO8601 format                | `datetime:”2016-03-31T22:56:32+00:00”`       |
| `timestamp_desc` | String explaining what type of timestamp it is | `timestamp_desc:”Content Modification Time”` |

Additional fields come from the imported Plaso file and depend on source type. You can see which additional fields are available in your timeline by clicking on any event and seeing the detailed list of all fields and their values.

| Field       | Description                                        | Example query                            |
| ----------- | -------------------------------------------------- | ---------------------------------------- |
| `data_type` | Data types present in timeline (depends on source) | `data_type:"windows:registry:key_value"` |
| `filename`  | Search for particular filetypes                    | `filename:*.exe`                         |
| `strings:`  | Search for a particular string                     | `strings:"PsExec"`                       |

### Search operators

Query String supports boolean search operators AND, OR and NOT.

### Wildcards and regular expressions

Wildcards can be run on individual search terms using <code>?</code> for a single character and <code>\*</code> for zero or more characters. Be aware that wildcards can use a lot of memory.

Regular expression patterns can be embedded in the query string by wrapping them in forward-slashes ("/"):

#### Syntax:

Some characters are reserved for regular expressions and must be escaped in the pattern

```
. ? + * | { } [ ] ( ) " \
```

Below are syntax elements and example regular expressions

<table>
  <tr>
   <td>Sign
   </td>
   <td>Meaning
   </td>
   <td>Example
   </td>
  </tr>
  <tr>
   <td><code>"."</code>
   </td>
   <td>Match any character
   </td>
    <td>For <b>"aaabbb"</b>:
<p>
<code>ab...   # match </code><br />
<code>a.c.e   # match </code>
   </td>
  </tr>
  <tr>
   <td><code>"+"</code>
   </td>
   <td>One or more
   </td>
   <td>For <b>"aaabbb"</b>:
<p>
<code>a+b+        # match </code><br />
<code>aa+bb+      # match  </code><br />
<code>a+.+        # match  </code><br />
<code>aa+bbb+     # match </code>
   </td>
  </tr>
  <tr>
   <td><code>"*" </code>
   </td>
   <td>Zero-or-more
   </td>
   <td>For <b>"aaabbb"</b>:
<p>
<code>a*b*        # match </code><br />
<code>a*b*c*      # match </code><br />
<code>.*bbb.*     # match </code><br />
<code>aaa*bbb*    # match</code>
   </td>
  </tr>
  <tr>
   <td><code>"?"</code>
   </td>
   <td>Zero-or-one
   </td>
    <td>For <b>"aaabbb"</b>:
<p>
<code>aaa?bbb?    # match </code><br />
<code>aaaa?bbbb?  # match </code><br />
<code>.....?.?    # match </code><br />
<code>aa?bb?      # no match</code>
   </td>
  </tr>
  <tr>
   <td><code>"{}"</code>
   </td>
   <td>Min-to-max repetitions
   </td>
   <td>For <b>"aaabbb"</b>:
<p>
<code>a{3}b{3}        # match </code><br />
<code>a{2,4}b{2,4}    # match </code><br />
<code>a{2,}b{2,}      # match </code><br />
<code>.{3}.{3}        # match </code><br />
<code>a{4}b{4}        # no match </code><br />
<code>a{4,6}b{4,6}    # no match </code><br />
<code>a{4,}b{4,}      # no match</code>
   </td>
  </tr>
  <tr>
   <td><code>"()"</code>
   </td>
   <td>Forms sub-patterns
   </td>
    <td><b>For "ababab"</b>
<p>
<code>(ab)+       # match </code><br />
<code>ab(ab)+     # match </code><br />
<code>ab(ab)+     # match </code><br />
<code>(..)+       # match </code><br />
<code>(...)+      # no match </code><br />
<code>(ab)*       # match </code><br />
<code>abab(ab)?   # match </code><br/>
<code>ab(ab)?     # no match </code><br />
<code>(ab){3}     # match </code><br />
<code>(ab){1,2}   # no match</code>
   </td>
  </tr>
  <tr>
   <td><code>"|"</code>
   </td>
   <td>Acts as "OR" operator
   </td>
   <td><b>For "aabb"</b>
<p>
<code>aabb|bbaa   # match </code><br />
<code>aacc|bb     # no match </code><br />
<code>aa(cc|bb)   # match </code><br />
<code>a+|b+       # no match </code><br />
<code>a+b+|b+a+   # match </code><br />
<code>a+(b|c)+    # match</code>
   </td>
  </tr>
  <tr>
   <td><code>"[]"</code>.
   </td>
   <td>Sets range of potential characters
   </td>
   <td><b>For "abcd":</b>
<p>
<code>ab[cd]+     # match </code><br />
<code>[a-d]+      # match </code><br />
<code>[^a-d]+     # no match</code>
   </td>
  </tr>
</table>

### Wildcard Search Mode

Timesketch includes a dedicated **Wildcard Search Mode** (introduced starting
with version `20260617`) designed for case-insensitive substring searching.
Under the hood, this mode leverages the
[OpenSearch wildcard field type](https://opensearch.org/docs/latest/field-types/supported-field-types/wildcard/),
making queries with leading/trailing wildcards (e.g., `*malicious*`)
significantly faster and more reliable compared to the classic query string
search.

To use Wildcard Search Mode:
* **In the Web UI:** Select the **WC** (Wildcard) mode from the toggle button
at the left of the query bar (which otherwise defaults to **QS** for Query
String).
* **In Settings:** You can choose to enable **"Use Wildcard Search by default"**
under your user settings.

#### Query Syntax & Examples

Wildcard mode tokenizes queries by space and parentheses, supporting standard
Boolean logic and parenthetical groupings:

* **Global substring search:** `*evil*` searches case-insensitively across all
fields mapped with wildcard properties (string based fields by default).
* **Field-specific search:** `message:*evil*` searches only within the
`message` field.
* **Logical operators:** `*evil* AND *good*` or `*evil* OR *good*`. The
operators `AND`, `OR`, and `NOT` must be capitalized.
* **Implicit AND:** Multiple terms separated by a space (e.g., `*evil* *good*`)
are implicitly combined with `AND`.
* **Exact values with colons:** If your query contains colons (such as paths,
MAC addresses, or URLs), you **must** wrap it in double quotes (e.g.,
`url:"http://google.com/"` or `"*count: 1*"`), otherwise the colon is
interpreted as a field separator.
* **No Escaping Required:** You do not need to escape special characters like
`.` or `-` with backslashes. Matches are literal, and escaping them (e.g.
`*\.com*`) will actually search for a literal backslash.

*Note: Wildcard Search Mode requires timeline indices to have
[wildcard mapping enabled](../admin/index-mappings.md). Older timelines
imported before this feature was introduced do not support it and will default
back to Query String mode.*

### Date Related Searches

| Description            | Example Query                                            |
| ---------------------- | -------------------------------------------------------- |
| Date Ranges            | datetime:[2021-08-29 TO 2021-08-31]                      |
| Date prior to          | datetime:[* TO 2021-08-29]                               |
| Dates after            | datetime:[2021-08-31 TO *]                               |
| Either side of a range | datetime:[* TO 2021-08-29] OR datetime:[2021-08-31 TO *] |

Now that we can handle dates in the query bar, we can start building more complex queries.
This query will find all the potential Remote Desktop event log entries in the given date range.

`data_type:"windows:evtx:record" AND event_identifier:4624 AND xml_string:"/LogonType\"\>3/" AND datetime:[2021-08-29 TO 2021-08-31]`

### Advanced search

Advanced search queries are in JSON format, and let you use the full power of OpenSearch. You can view your existing Query String query as an advanced OpenSearch query by clicking "Advanced" button below the query entry field.

[Full query DSL guide](https://opensearch.org/docs/latest/opensearch/query-dsl/index/)

## Saved Searches

Saved Searches are saved results of your search queries, for easier access later. A saved Search does not only include the query but also specifics like displayed columns.

To save search results, run your search query, apply filters if needed, and click the “Save” button under the query field. Now you can access this Search from “Saved Searches” drop-down menu on Explore page of your sketch.

You can further refine the data in your views by manually hiding certain events. To do it, click a small eye icon next to the icon. If you have hidden events in your view, they can be un-hidden by clicking red button “Show hidden events” in the upper right corner of your timeline.

You can save changes to your views by clicking “Save Changes” button

## Search templates

Search templates allow quick creation of most commonly used views.
You can browse available templates in the “Search templates” drop-down menu below search query window on “Explore page”

On “Views” page, you can quickly generate and add a view from a template to your sketch. To do so, just scroll down to the template you want to use, and click “Quick add”

## Examples

Here are some common searches:

| Description                  | Example Query                                                    |Comment    |
| ---------------------------- | ---------------------------------------------------------------- |------------|
| EventId 4624 and LogonType 5 | event_identifier:4624 AND "LogonType\">5</Data>"                 | |
| Windows File path            | "C:\\Users\\foobar\\Download\\folder\ whitespace\\filename.jpeg" ||
| Events that have a value in a field that contains the name `*comm*`           | `_exists_:"*comm*"` | Can be very expensive search |

## Common questions

There is a frequent question around Windows Event logs and how they are represented in Timesketch when imported from Plaso. For that we recommend reading up on [Common misconception about Windows EventLogs](https://osdfir.blogspot.com/2021/10/common-misconceptions-about-windows.html)

## PPL and SQL

Query String and Wildcard search return events.
[PPL](https://docs.opensearch.org/latest/sql-and-ppl/ppl/index/) and
[SQL](https://docs.opensearch.org/latest/sql-and-ppl/sql/index/) are sent to
OpenSearch directly, so they can also aggregate: count events per host, group
events by `data_type`, or rank field values by how often they occur. Use them
for questions about totals and distributions, and use Query String when you
want to read the events themselves.

Both languages need OpenSearch 3.7.0 or later with the SQL plugin installed. If
`PPL` and `SQL` are missing from the search mode menu, the cluster does not
provide them. Timesketch re-checks the cluster periodically, so the modes appear
on their own after an upgrade.

### Selecting a search mode

The button on the left of the query bar selects the language:

| Mode  | Language                              |
| ----- | ------------------------------------- |
| `QS`  | Query String (Lucene), the default    |
| `WC`  | [Wildcard](#wildcard-search-mode)     |
| `PPL` | OpenSearch Piped Processing Language  |
| `SQL` | OpenSearch SQL                        |

### Indexes and query scope

PPL and SQL run their searches directly against the OpenSearch indexes that hold
a sketch's events. In both languages an index takes the place of a table, and
Timesketch's own structure does not exist at that level: one index can hold
several timelines, and some of them may belong to other sketches.

Timesketch closes that gap for you. It names the sketch's indexes in the query
and adds a filter for the timelines the sketch contains, so results never reach
events from outside it. Leave both out of what you type:

* In PPL, begin with the first command, for example `stats count() by data_type`.
  Do not write `source=` and do not begin with a pipe.
* In SQL, begin with `SELECT` and write no `FROM` clause.

A query naming any other index is rejected. SQL is limited to `SELECT`, `SHOW`
and `DESCRIBE`, so nothing can be modified through this interface.

### PPL

| Description                     | Example query                                             |
| ------------------------------- | --------------------------------------------------------- |
| First 100 events                | `head 100`                                                |
| Filter on message text          | `where message like 'Failed%' \| head 100`                |
| Count events per data type      | `stats count() as cnt by data_type \| sort - cnt`         |
| Ten most common hostnames       | `stats count() as cnt by hostname \| sort - cnt \| head 10` |
| One event per value of a field  | `dedup source_short \| head 50`                           |
| Newest events first             | `sort - datetime \| head 100`                             |

`sort` takes field names and aliases, never function calls. Name the
aggregation with `as` and sort on that name:

```
stats count() by hostname | sort - count()           <- rejected
stats count() as cnt by hostname | sort - cnt        <- works
```

Inside `stats`, the aggregation comes before `by`, as in
`stats count() as cnt by hostname`. Row limits use `head N`; PPL has no `LIMIT`.

OpenSearch documents every command and its options in
[PPL commands](https://docs.opensearch.org/latest/sql-and-ppl/ppl/commands/index/).

### SQL

| Description                | Example query                                                                          |
| -------------------------- | -------------------------------------------------------------------------------------- |
| First 100 events           | `SELECT datetime, message, timestamp_desc LIMIT 100`                                   |
| Filter on message text     | `SELECT datetime, message WHERE message LIKE 'Failed%' LIMIT 100`                       |
| Count events per data type | `SELECT data_type, COUNT(*) AS cnt GROUP BY data_type ORDER BY cnt DESC LIMIT 20`      |

Always give `ORDER BY` a `LIMIT`. Without one, OpenSearch sorts the whole result
set in memory and may return nothing.

The supported clauses and their order of execution are documented in
[Basic SQL queries](https://docs.opensearch.org/latest/sql-and-ppl/sql/basic/).

### Field types

`datetime` is the only date field, and date detection is switched off, so a
field holding a formatted timestamp is text rather than a date.

Every string value is indexed as `text`, with a `keyword` sub-field for exact
matches and a `wildcard` sub-field for substring matches. The `keyword`
sub-field is skipped for values longer than 256 characters, so very long values
cannot be matched exactly or aggregated on.

Numeric-looking fields are often not numeric. `plaso.mappings` maps several of
them as text on purpose, among them `file_size`, `offset`, `sequence_number`,
`source_port`, `exit_status`, `severity`, `version` and `http_response_bytes`.
Comparing one of these against a bare number matches nothing, because a text
field holds the digits as characters:

```
file_size = 4096        <- no rows, file_size is text
file_size = '4096'      <- works
```

Fields absent from `plaso.mappings` and `generic.mappings` are typed from the
first value indexed, so their type follows the data rather than a fixed schema.
If a comparison against a number returns no rows, quote the value and run it
again. [Index Mappings](../admin/index-mappings.md) describes the mapping files
in full.

### Filtering by time

Use the time-range picker above the query bar rather than comparing `datetime`
inside the query. The picker builds the range filter itself, and it applies to
PPL and SQL exactly as it does to Query String.

A range written in the query is easy to get wrong: an unquoted timestamp is
parsed as arithmetic, and a quoted one is compared against whatever type the
field turned out to be. When a range does belong in the query text, Query String
mode handles it predictably with `datetime:[2024-01-01 TO 2024-01-31]`.

### Matching text with LIKE

`LIKE 'Failed%'` matches values starting with `Failed`. OpenSearch can use the
index to find them, because the pattern begins with a literal.

A pattern beginning with `%` gives OpenSearch nothing to start from, so it reads
every value in the field instead. On a large timeline that is slow.

| Pattern           | Matches                            | Uses the index |
| ----------------- | ---------------------------------- | -------------- |
| `'Failed%'`       | values starting with `Failed`      | yes            |
| `'%@example.com'` | values ending with `@example.com`  | no             |
| `'%failed%'`      | values containing `failed`         | no             |

Anchor the beginning of the pattern whenever the data allows it. If you cannot,
anchor the end instead: `'%@example.com'` still scans the field, but far fewer
values match it than `'%@example%'`.

### Grouping on a field that not every event has

A sketch usually holds timelines from several sources, and a field one source
populates is missing from the others. Grouping on that field collects every
event lacking it into a single bucket. That bucket is frequently the largest, so
it sorts to the top and pushes the values you wanted out of view.

No event actually holds that bucket's label as a value, so searching for it in
Query String mode returns nothing. Its count says only how many events had no
value for the field.

Narrow the query to the source that populates the field, then group:

```
where data_type = 'windows:evtx:record' | stats count() as cnt by event_identifier | sort - cnt
```

If a count looks wrong, search for the same value in Query String mode. That
confirms the number and shows whether the value is one you can search for at
all.

### Warnings shown next to the query

The query bar flags the mistakes above before the query runs, and explains what
to change. A warning does not block anything, so a query with an unaliased sort
or an unlimited `ORDER BY` can still be submitted.

A query OpenSearch rejects is reported in the results panel as a query error.
Failing to reach the cluster is reported as a separate kind of error, so a typo
in the query is distinguishable from OpenSearch being unavailable.

### Reading the results

Results appear as a table of the columns the query selected, rather than the
event list used by Query String search.

Select a cell to search for that value in Query String mode. This is how you get
from a count back to the events behind it. Values too long for the `keyword`
sub-field cannot be searched this way.

The panel can also show the execution plan, which is the query as OpenSearch
resolved it and therefore includes the index and timeline filters Timesketch
added. Compare it with what you typed when a result is not what you expected.
[Explain API](https://docs.opensearch.org/latest/sql-and-ppl/sql-and-ppl-api/index/#explain-api)
describes the plan formats.

### Exporting results

Export writes rows to a file as they arrive instead of holding them in memory,
so an export can be far larger than the table on screen.

Use SQL for large exports. The SQL plugin pages with a
[cursor](https://docs.opensearch.org/latest/sql-and-ppl/sql-and-ppl-api/index/#paginating-results),
and every page costs roughly the same. Cursors are a SQL-only feature, so a PPL
export pages by re-running the query with a larger offset each time; the pages
grow slower as the export continues, and on a large timeline the later ones can
time out and end the export early.

An export that stopped early ends with a JSON object containing
`"incomplete": true`, the number of rows written and the offset reached. Check
the last line before treating a file as complete.

### Limits

| Limit                        | Value                                      |
| ---------------------------- | ------------------------------------------ |
| Rows returned by a SQL query | 1000 by default, 10000 at most             |
| Rows returned by a PPL query | the SQL plugin's own row limit             |
| Query and explain timeout    | 30 seconds                                 |
| Export page size             | 10000 rows                                 |
| Export page timeout          | 60 seconds for SQL, 120 seconds for PPL    |

An aggregation reaching the row limit is truncated rather than wrong, but the
tail of the distribution is missing. Add a `where` stage or a `WHERE` clause to
bring the number of groups down.
