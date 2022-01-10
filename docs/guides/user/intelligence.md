# Intelligence

Each sketch can have Intelligence items associated with it. This comes in the form of simple strings extracted from events,
usually as IOCs. (e.g. a suspicious IP address in a log file that you want to highlight.)


Intelligence entries have the following, simple format;

```json
{
  "externalURI" :"yeti/127.0.0.1"
  "ioc" :"127.0.0.1"
  "tags": ["evil", "c2", "random"]
  "type": "ip"
}
```

## Addding new intelligence

Timesketch will parse events attributes for potential IOCs to be added as Intelligence (e.g. when Timesketch finds something that looks like a SHA-256 hash, IP address, etc.). This will be surfaced to you by a grey highlight on the corresponding string. You can then click the highlighted string to open and pre-fill the `add local intelligence` dialog. You can optionally change the IOC type before confirming the suggestion.

To add an IOC that isn't highlighted, just select the string you want to add with your cursor. The string will become higlighted, and you will be able to follow the same steps as above to add it.

The currently supported IOC types are:

* `fs_path`
* `hash_sha256`
* `hash_sha1`
* `hash_md5`
* `hostname`
* `ipv4`

If a string doesn't match any of the aforementioned IOC types, the type will fall back to `other`.

## Intelligence view

The list of all the IOCs added to a sketch can be seen in the *Intelligence* tab (accessible at `/sketch/{SKECTH_ID}/intelligence`).

![Intelligence view demo](/assets/images/inteldemo.png)

### IOC table

From the IOC table section, one can:

* Copy IOC to clipboard.
* Search a sketch for a given IOC.
* Open the external reference in a new browser tab, if it looks like a link.
* Edit IOCs that have been added.
* Delete IOCs.

By clicking the lens icon next to the IOC, you will be taken to the Explore view with a query for the given value.

### Tags

IOCs that have been added to the sketch can be tagged with lightweight context tags. These tags are not currently
being reused elsewhere in the Timesketch.

The `Tag list` card in the intelligence view contains a table of tags that have been thusly associated with IOCs.
Clicking on the lens icon will take you to the Explore view, searching for *IOC values* that have this tag.

### Event tags

The `Event tags` card contains a list of all tags that can be found in a sketch. Contrary to the `Tag list`, these
are not tags associated to IOCs but tags that have been applied to timeline events. Clicking on the lens icon will
take you to the Explore view, searching for all events that have the corresponding tag.#
