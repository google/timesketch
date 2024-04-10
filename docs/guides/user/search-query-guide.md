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
