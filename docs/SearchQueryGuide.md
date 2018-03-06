# Search within timeline
## Search queries

Timesketch allows full text search within timelines. Good way to get started is by selecting one of pre-set search templates and adjusting them to the data in your timeline.

Simple search queries relies on[ Query String Query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-query-string-query.html) mini-language, but it is also possible to use the full potential of Elasticsearch query language in Advanced queries.

### Common fields

Data fields will vary depending on the source being uploaded, but here are some that are mandatory, and therefore will be present in any timeline.



<table>
  <tr>
   <td>Field
   </td>
   <td>Description
   </td>
   <td>Example query
   </td>
  </tr>
  <tr>
   <td><code>message</code>
   </td>
   <td>String with information about event
   </td>
   <td><code>message:"This is a message"</code>
   </td>
  </tr>
  <tr>
   <td><code>timestamp</code>
   </td>
   <td>Timestamp as microseconds since Unix epoch
   </td>
   <td><code>timestamp:"363420000"</code>
   </td>
  </tr>
  <tr>
   <td><code>datetime</code>
   </td>
   <td>Date and time in ISO8601 format
   </td>
   <td><code>datetime:"2016-03-31T22:56:32+00:00"</code>
   </td>
  </tr>
  <tr>
   <td><code>timestamp_desc</code>
   </td>
   <td>String explaining what type of timestamp it is
   </td>
   <td><code>timestamp_desc:"Content Modification Time"</code>
   </td>
  </tr>
</table>

Additional fields come from the imported Plaso file  and depend on source type. You can see which additional fields are available in your timeline by clicking on any event and seeing the detailed list of all fields and their values.
<table>
  <tr>
   <td>Field
   </td>
   <td>Description
   </td>
   <td>Example query
   </td>
  </tr>
  <tr>
   <td>data_type
   </td>
   <td>Data types present in timeline (depends on source)
   </td>
   <td>data_type:"windows:registry:key_value" 
   </td>
  </tr>
  <tr>
   <td>filename
   </td>
   <td>Search for particular filetypes
   </td>
   <td>filename:*.exe
   </td>
  </tr>
  <tr>
   <td>strings:
   </td>
   <td>Search for a particular string
   </td>
   <td>strings:"PsExec" 
   </td>
  </tr>
</table>


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
   <td><code>Match any character</code>
   </td>
   <td> For *"aaabbb"*:
<p>
<code>ab...   # match 
<p>
a.c.e   # match </code>
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
## Views
## Search templates
