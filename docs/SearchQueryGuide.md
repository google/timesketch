# Search within timeline
## Search queries

Timesketch allows full text search within timelines. Good way to get started is by selecting one of pre-set search templates and adjusting them to the data in your timeline.

Simple search queries relies on[ Query String Query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html) mini-language, but it is also possible to use the full potential of Elasticsearch query language in Advanced queries.

### Common fields

Data fields will vary depending on the source being uploaded, but here are some that are mandatory, and therefore will be present in any timeline.

| Field | Description |Example query|
|-------|-------------|-------------|
| `message`|String with information about event| `message:”This is a message”`|
| `timestamp`|Timestamp as microseconds since Unix epoch|`timestamp:”363420000”`|
| `datetime`|Date and time in ISO8601 format| `datetime:”2016-03-31T22:56:32+00:00”`
| `timestamp_desc`|String explaining what type of timestamp it is|`timestamp_desc:”Content Modification Time”`|




Additional fields come from the imported Plaso file  and depend on source type. You can see which additional fields are available in your timeline by clicking on any event and seeing the detailed list of all fields and their values.

|Field|	Description|	Example query|
|-----|------------|---------------|
|`data_type`|	Data types present in timeline (depends on source)|	`data_type:"windows:registry:key_value"`
|`filename`|	Search for particular filetypes|	`filename:*.exe`|
|`strings:`|	Search for a particular string|	`strings:"PsExec"`|


### Search operators
Query String supports boolean search operators AND, OR and NOT.

### Wildcards and regular expressions
Wildcards can be run on individual search terms using <code>?</code> for a single character and <code>*</code> for zero or more characters. Be aware that wildcards can use a lot of memory.

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
<code>a.c.e   # match</code>
   </td>
  </tr>
  <tr>
   <td><code>"+"</code>
   </td>
   <td><code>One or more</code>
   </td>
   <td><code>For "aaabbb":</code>
<p>
<code>a+b+        # match \
aa+bb+      # match \
a+.+        # match \
aa+bbb+     # match</code>
   </td>
  </tr>
  <tr>
   <td><code>"*" </code>
   </td>
   <td><code>Zero-or-more</code>
   </td>
   <td><code>For "aaabbb":</code>
<p>
<code>a*b*        # match \
a*b*c*      # match \
.*bbb.*     # match \
aaa*bbb*    # match</code>
   </td>
  </tr>
  <tr>
   <td><code>"?"</code> 
   </td>
   <td><code>Zero-or-one</code>
   </td>
   <td><code>For "aaabbb":</code>
<p>
<code>aaa?bbb?    # match \
aaaa?bbbb?  # match \
.....?.?    # match \
aa?bb?      # no match</code>
   </td>
  </tr>
  <tr>
   <td><code>"{}"</code>
   </td>
   <td><code>Min-to-max repetitions</code>
   </td>
   <td><code>For "aaabbb":</code>
<p>
<code>a{3}b{3}        # match \
a{2,4}b{2,4}    # match \
a{2,}b{2,}      # match \
.{3}.{3}        # match \
a{4}b{4}        # no match \
a{4,6}b{4,6}    # no match \
a{4,}b{4,}      # no match</code>
   </td>
  </tr>
  <tr>
   <td><code>"()"</code>
   </td>
   <td><code>Is used to form sub-patterns</code>
   </td>
   <td><code>For "ababab"</code>
<p>
<code>(ab)+       # match \
ab(ab)+     # match \
(..)+       # match \
(...)+      # no match \
(ab)*       # match \
abab(ab)?   # match \
ab(ab)?     # no match \
(ab){3}     # match \
(ab){1,2}   # no match</code>
   </td>
  </tr>
  <tr>
   <td><code>"|"</code>
   </td>
   <td><code>Acts as "OR operator"</code>
   </td>
   <td><code>For "aabb"</code>
<p>
<code>aabb|bbaa   # match \
aacc|bb     # no match \
aa(cc|bb)   # match \
a+|b+       # no match \
a+b+|b+a+   # match \
a+(b|c)+    # match</code>
   </td>
  </tr>
  <tr>
   <td><code>"[]"</code>.
   </td>
   <td><code>Sets range of potential characters</code>
   </td>
   <td><code>For "abcd":</code>
<p>
<code>ab[cd]+     # match \
[a-d]+      # match \
[^a-d]+     # no match</code>
   </td>
  </tr>
</table>







### Advanced search

Advanced search queries are in JSON format,  and let you use the full power of Elasticsearch. You can view your existing Query String query as an advanced Elasticsearch query by clicking "Advanced" button below the query entry field.

[Full Elasticsearch guide](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl.html)

## Views

Views are saved results of your search queries, for easier access later. 

To save search results as a view, run your search query, apply filters if needed, and click the “Save view” button under the query field. Now you can access this view from Overview page, from the “Views” tab, and from “Saved views” drop-down menu on Explore page of your sketch.

You can further refine the data in your views by manually hiding certain events. To do it, click a small eye icon next to the icon. If you have hidden events in your view, they can be un-hidden by clicking red button “Show hidden events” in the upper right corner of your timeline.

You can save changes to your views by clicking “Update View” button


## Search templates
Search templates allow quick creation of most commonly used views.
You can browse available templates in the “Search templates” drop-down menu below search query window on “Explore page”

On “Views” page, you can quickly generate and add a view from a template to your sketch. To do so, just scroll down to the template you want to use, and click “Quick add”

