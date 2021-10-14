# Intelligence

This is a feature per Sketch. It can store key value pairs.

## Add new information

To add new information to the Intelligence part, go to the Sketch, find the event that contains the piece of information you want to highlight and mark it with the mouse. Then in the popup select the piece of information you have marked. This can be one of:

* hash sha256
* hash sha1
* hash md5
* ip

The key value pair then will be added to the Intelligence Tab as well as the Attributes tab, technically, Intelligence is an per sketch attribute.

For some attributes, Timesketch will try to find and suggest Intelligence. This will be surfaced to the you by highlighting the value with grey, e.g. when Timesketch finds something that looks like a sha256 hash. YOu then simply need to klick the suggestion and it will pre-fill the suggested type where you can simply confirm the suggestion.

## Searching for local Intelligence in your Sketch

After you added Intelligence for your Sketch, you can go over to `/sketch/{SKECTH_ID}/intelligence` and you see all the Intelligence.

By clicking the lense icon next to the Indicator, an search will be executed for the given value.

![Share dialogue](/assets/images/add_intelligence.gif) 

## Delete Intelligence

Deleting Intelligence can be done from the Intelligence Tab by clicking the trash icon at the very end of the row.