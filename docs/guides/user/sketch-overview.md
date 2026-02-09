---
hide:
  - footer
---
# Sketches

Sketches are a way to organize analysis of events across multiple timelines and increase data discoverability via search, targeted views, comments and stories.

## Creating a sketch
To create a new sketch, click “New Sketch” button on the tool’s homepage. After that you will be redirected straight onto Overview page of your new sketch. Here you can click “Edit” icon to give your sketch a name and enter a description.

Now you need to add timelines to your new sketch. To do so, you can click “Import Timeline” and upload a file in Plaso, CSV or JSONL formats. More details about importing timelines are in chapter “Importing timelines”

Alternatively, you can go to “Timelines” tab and select from all available timelines.

![Empty state](../../assets/images/empty_state_sketch.png)

## Navigating a sketch
A sketch consists of 5 tabs: “Overview”, “Explore”, “Stories”, "Attributes", "Intelligence".

![navigation bar](/assets/images/Navigation.png)

**Overview** tab contains summary information about your sketch, such as sketch title, description, as well as shortcuts to saved views and timelines.

**Explore** page allows navigating timelines, using search queries, applying filters, viewing timeline data in chart format and saving your search discoveries as new views.

**Stories** tab allows creating outlines of your Stories can be annotated with selected items from your timelines

**Attributes** tab shows the attributes of the sketch.

**Intelligence** tab shows intelligence values added from the sketch. See [Intelligence](intelligence.md)

## Sharing and access control
After the sketch is created, you can share it with other users in the system. To do so, click ![Share](/assets/images/sharebutton.png) button. You will be presented with the following dialogue:

![Share dialogue](/assets/images/Sharingdialog.png)

You can share the sketch with users, groups of users, make it available to all users in your system, or leave private.

## Explore

**Search** See [Search query guide](search-query-guide.md)

**Views** allows quick access to saved views and creation of new views

**Timerange** allows to control the timerange of shown events.

![Timefilter](../../assets/images/timefilter.png)

**Filter** Add a filter, e.g. to show only starred events

For each event, you can apply the following actions by clicking small icons in each event row:

- Star the event
- Label the event
- Comment the event
- Start a context query to find related events
- Copy an event attributes

**SearchHistory**

Implemented as a tree with support for branching, annotations and intuitive navigation means you will never get lost in your searches again

![Sketch History](/assets/videos/SearchHistory.mp4)

## More

If you click on the "More" Button in the Sketch Overview, you get the following three options.

![Sketch Overview more dialogue](/assets/images/SketchMore.png)

### Delete

Delete the whole sketch. *Note:* this will not delete the Timelines.

### Archive

Archiving a sketch is a way to preserve it in a archived state while freeing up system resources. When a sketch is archived:
- It is hidden from the default list of sketches.
- All its timelines are marked as archived.
- The underlying OpenSearch indices are closed if they are not used by any other active sketches. This reduces memory usage on the OpenSearch cluster.
- You cannot explore data, run analyzers, or make other modifications to an archived sketch.
- The sketch can be unarchived at any time to restore full functionality.

#### When a sketch can be archived:

* The sketch is currently not in an 'archived' state.
* It does not have any labels that are configured to prevent archival (e.g., LABELS_TO_PREVENT_DELETION).
* Crucially, none of its associated timelines are in a 'processing', 'fail', or 'timeout' state. All timelines must be in a **'ready'** state to be archived.

#### What happens when a sketch is archived:

* The sketch's status is updated to 'archived'.
* All timelines within that sketch have their status set to 'archived'.
* For each associated OpenSearch index:
  * Timesketch attempts to close the OpenSearch index.
  * If the index is successfully closed, its database status is also set to 'archived'.
  * If the OpenSearch index is not found, its database status is set to 'fail' (indicating an inconsistency where the DB record exists but the OS index doesn't).
  * If other errors occur during the closing process (e.g., network issues), the database status of the OpenSearch index remains unchanged, allowing administrators to identify these inconsistencies later.

#### When a sketch cannot be archived (and why):

* If the sketch is already archived, the operation will be aborted.
* If the sketch has a label that prevents archival, the operation will be aborted.
* If any of its timelines are in a 'processing', 'fail', or 'timeout' state, the archival process will be aborted. This is a critical check to prevent archiving incomplete or problematic data. The system will explicitly tell the user that these timelines must be resolved (e.g., deleted) before the sketch can be archived.

#### Situations

* Attempt to archive a sketch but at least one timeline is still processing
  * Wait for the timeline to be **ready**
  * If it does not reach the "ready" state, get in contact with the Timesketch admin
      * The administrator can troubleshoot the timeline import by running: `tsctl timeline-status <TIMELINE_ID>`
      * If the timeline is stuck in a processing loop, the administrator can manually set the status to "fail" using: `tsctl timeline-status --action set --status fail <TIMELINE_ID>`
      * A failed timeline must be removed from the sketch before it can be archived. This can be done via tsctl and the API in the future.

### Unarchive

Unarchiving a sketch restores it to a fully active and writable state. This action is the reverse of archiving. When a sketch is unarchived:
- The sketch status is set back to **"ready"**.
- All its timelines are marked as **"ready"**.
- The underlying OpenSearch indices are **reopened**, making the event data available for querying and analysis.
- The sketch will reappear in the default list of sketches and all its functionality will be restored.

#### When a sketch can be unarchived:

* The sketch's current status must be **'archived'**.
* It can be unarchived even if some of its timelines are in a **'processing'** or **'fail'** state, but a warning will be logged, advising the user to resolve these timelines (e.g., by deleting them) before attempting to re-archive the sketch.

#### What happens when a sketch is unarchived:

* Timesketch attempts to **reopen all associated OpenSearch indices** that were previously closed (archived).
* If an OpenSearch index is already open, it's considered a success.
* If all necessary OpenSearch indices are successfully opened (or were already open), the sketch's status is updated to **'ready'**.
* All timelines within that sketch that were **'archived'** have their status set back to **'ready'**.
* The corresponding SearchIndex database objects also have their status updated to **'ready'**.

#### When a sketch cannot be unarchived (and why):

* If the sketch is not currently 'archived' (e.g., it's already **'ready'** or **'deleted'**), the operation will be aborted.
* If there's a critical error opening an OpenSearch index (e.g., the index is genuinely missing or a network error occurs), the entire unarchival process will be aborted, and the sketch will remain in its **'archived'** state.

### Export

Export allows you to download sketch data. In the Web UI, this will export a
comprehensive ZIP file containing:

- Events (starred, tagged, tagged_event_stats, comments, ...)
- Stories as HTML
- Views (as CSV)
- Metadata

This is equivalent to the `--use_sketch_export` option in the [CLI tool](cli-client.md#export-a-sketch).
By default, the CLI tool exports just the events from the sketch.
