# Intelligence

Each sketch can have Intelligence items associated with it. This comes in the form of simple strings extracted from events,
usually as IOCs. (e.g. a suspicious IP address in a log file that you want to highlight.)

## Addding new intelligence

Timesketch will parse events attributes for potential IOCs to be added as Intelligence (e.g. when Timesketch finds something that looks like a SHA-256 hash, IP address, etc.). This will be surfaced to you by a grey highlight on the corresponding string. You can then click the highlighted string to open and pre-fill the `add local intelligence` dialog. You can optionally change the IOC type before confirming the suggestion.

To add an IOC that isn't highlighted, just select the string you want to add with your cursor. The string will become higlighted, and you will be able to follow the same steps as above to add it.

The currently supported IOC types are:

* `hash_sha256`
* `hash_sha1`
* `hash_md5`
* `ip`

If a string doesn't match any of the aforementioned IOC types, the type will fall back to `other`.

## Searching for local Intelligence in your Sketch

The list of all the IOCs added to a sketch can be seen in the *Intelligence* tab (accessible at `/sketch/{SKECTH_ID}/intelligence`).

By clicking the lens icon next to the IOC, you will be taken to the Explore view with a query for the given value.

![Share dialogue](/assets/images/add_intelligence.gif)

## Delete Intelligence

Deleting IOCs can be done from the *Intelligence* tab by clicking the trash icon at the very end of the row.
