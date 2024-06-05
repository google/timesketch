---
hide:
  - footer
---
## Concepts

Timesketch is built on multiple sketches, where one sketch is usually one case.
Every sketch can consist of multiple timelines with multiple views.

We highly recommend to read two blog post to understand limitations of time and timeline analysis:

- [Lets talk about time](https://osdfir.blogspot.com/2021/06/lets-talk-about-time.html)
- [pearls and pitfalls of timeline analysis](https://osdfir.blogspot.com/2021/10/pearls-and-pitfalls-of-timeline-analysis.html) before starting your first timeline analysis.

This should avoid wrong expectations and help analysts asking the right questions when looking at timelines in Timesketch.

## Sketches

There is a dedicated document to walk you through [Sketches](sketch-overview.md)

## Adding Timelines

- [Create timeline from JSON/JSONL/CSV file](/guides/user/import-from-json-csv/)
- [Uploading data](/guides/user/upload-data/)
- [Upload data via the API](/developers/api-upload-data/)

## Adding event

This feature is currently not implemented in the Web UI. But you can add events using the [API client](/developers/api-client.md).

## Add a comment

You can comment events in your sketch. The comments are saved in your sketch, that means if you add a timeline to multiple sketches, the comments are only shown in the one sketch you made the comments.

## Star an event

Click the little star symbol in the Event List to star an event. Stared events can be used to filter on them and or to add all starred events in your story.

## Tag / Label in context of an Event.

An event can have a list of tags. Those can be added via API, API client, CLI client or the Web UI.
The tags are stored in the opensearch object in the field `tag`. This also means a data source, e.g. plaso could add tag(s) when parsing / processing data to be handed to Timesketch.

In contrast to a tag, in older versions of Timesketch there was a label that could be added to an event. An event could have one or more labels at a time. Those labels where stored in the database, not in the opensearch object. The concept of labels in events is slowly being deprecated and removed from UI.

> There might be many more places where tags can be added to instances, e.g. a Sigma rule might have one or more tags.

## Views

Views are saved search queries. Those can either be created by the User, by API or via Analyzers.

To create a view from the Web Ui, click the _Save as view_ button on the top right of the Search fields in the Explore Tab of a sketch.

## Insights / Aggregations

The _Insights_ functionality in a sketch gives the opportunity to run aggregations on the events in a sketch.

There are currently two aggregators available:

- Terms aggregation
- Filtered terms aggregation

### Terms aggregation

The term aggregation can be used for example to get a table view of the present data types in the sketch.

You can choose between the following chart types:

- circlechart
- table
- barchart
- hbchart
- linechart

The next value to provide is the field you want to aggregate on, for example the data_type.

The last value is the number of results to return.

Once the aggregation is completed, you can save the aggregation by clicking the _save_ button on the top right corner of the aggregation result, for example to add it to a story.

### Filtered terms aggregation

The filtered terms aggregation works the same way the terms aggregation works with one additional input field the filter query. This can be used for example to aggregate over data_types only for events that contain a certain string.

## Customize columns

In the Explore view of a sketch the message is the only column visible. To add more columns, click the _customize_ columns\* button on the top right of the events list.

The list of available columns is pre-populated from the columns in your timeline.

## Stories

A story is a place where you can capture the narrative of your technical investigation and add detail to your story with raw timeline data and aggregated data.
The editor lets you to write and capture the story behind your investigation and at the same time enable you to share detailed findings without spending hours writing reports.

You can add events from previously saved searches.
Just hit enter to start a new paragraph and choose the saved search from the dropdown menu.

See [Medium article](https://medium.com/timesketch/timesketch-2016-7-db3083e78156)

You can add saved views, aggregations and text in markdown format to a story.

Some analyzers automatically generate stories to either highlight possible events of interest or to document their runtime.

If you want to export a story, export the whole Sketch. The zip file will contain each story. A story can also be exported using the [API Client](/developers/api-client/).

## Demo

To play with timesketch without any installation visit [demo.timesketch.org](https://demo.timesketch.org) as `demo/demo`.

## Searching

All data within Timesketch is stored in OpenSearch. There is a dedicated document called [search query guide](search-query-guide.md) to help you create custom searches.

Using the advances search, a JSON can be passed to Timesketch

```json
{
  "query": {
    "bool": {
      "must": [
        {
          "query_string": {
            "query": "*"
          }
        }
      ]
    }
  },
  "sort": {
    "datetime": "asc"
  }
}
```

## Analyzers

With Analyzers you can enrich your data in timelines. The analyzers are written in Python.

The system consist of a set of background workers that can execute Python code on a stream of events. It provides an easy to use API to programmatically do all the actions available in the UI, e.g. tagging events, star and create saved views etc. The idea is to automatically enrich data with encoded analysis knowledge.

The code for Analyzers is located at

```shell
/timesketch/lib/analyzers
```

### Analyzer description

_Note:_ Not all analyzers are explained in this documentation. If you have questions to a particular analyzer, please have a look at the code or file an [Issue on Github](https://github.com/google/timesketch/issues/new).

#### Browser Search Analyzer

The browser search analyzer takes URLs usually reserved for browser search queries and extracts the search string.

It will also tell in a story:

- The top 20 most commonly discovered searches
- The domains used to search
- The most common days of search
- And an overview of all the discovered search terms

#### Browser Timeframe Analyzer

The browser time frame analyzer discovers browser events that occurred outside of the typical browsing window of this browser history.

The analyzer determines the activity hours by finding the frequency of browsing events per hour, and then discovering the longest block of most active hours before proceeding with flagging all events outside of that time period. This information can be used by other analyzers or by manually looking for other activity within the inactive time period to find unusual actions.

#### BigQuery Matcher Analyzer

The BigQuery Matcher allows tagging events that match indicators in a BigQuery table.

An example could be tagging events that have a `sha256_hash` field that matches indicators stored in a BigQuery table. You can configure this by adding the following matcher into `bigquery_matcher.yaml`:

```
sha256_matcher:
    event_field_name: sha256_hash
    bq_project: 'my_google_project'
    bq_query: 'SELECT DISTINCT hash FROM project.dataset.table_with_hashes WHERE hash IN UNNEST(@sha256_hash)'
    tags: ['bigquery-sha256-match']
    emojis: ['SKULL']
```

Any Timesketch event that has a `sha256_hash` field that matches the `hash` column value in the BigQuery table `table_with_hashes` will be tagged with `bigquery-sha256-match` and a skull emoji is added to the event.

Note that Timesketch must be able to authenticate to BigQuery and have access to the tables. You can read more about setting up authentication in the relevant [Google Cloud documentation](https://cloud.google.com/docs/authentication/production).

#### Chain analyzer

Sketch analyzer for chained events

The purpose of the chain analyzer is to chain together events that can be described as linked, either by sharing some common entities, or one event being a derivative of another event. An example of this would be that a browser downloads an executable, which then later gets executed.

The signs of execution could lie in multiple events, from different sources, but they are all linked or chained together. This could help an analyst see the connection between these separate but chained events. Another example could be a document written and then compressed into a ZIP file, which would then be exfilled through some means. If the document and the ZIP file are chained together it could be easier for the analyst to track the meaning of an exfil event involving the compressed file.

#### Domain Analyzer

The Domain Analyzer extracts domain and Top Level Domain (TLD) info from events that have a field with either `url` or `domain`.

It will also add information about:

- Known CDN providers (based on Timesketch config)

#### Windows EVTX Sessionizer

This Analyzer will determine the start and end event for a user session based on EVTX events.

#### Windows EVTX Gap analyzer

It attempts to detect gaps in EVTX files found in an index using two different methods.

First of all it looks at missing entries in record numbers and secondly it attempts to look at gaps in days with no records.

This may be an indication of someone clearing the logs, yet it may be an indication of something else. At least this should be interpreted as something that warrants a second look.

This will obviously not catch every instance of someone clearing EVTX records, even if that's done in bulk. Therefore it should not be interpreted that if this analyzer does not discover something that the records have not been wiped. Please verify the results given by this analyzer.

The results of this analyzer will be a story, that details the findings.

#### Safebrowsing Analyzer

This Analyzer checks urls found in a sketch against the [Google Safebrowsing API](https://developers.google.com/safe-browsing/v4/reference/rest).

To use this Analyzer, the following parameter must be set in the `timesketch.conf`:

```config
SAFEBROWSING_API_KEY = ''
```

This analyzer can be customized by creating an optional file containing URL wildcards to be allow listed called

```config
safebrowsing_allowlist.yaml
```

There are also two additional config parameters, please refer to the [Safe Browsing API reference](https://developers.google.com/safe-browsing/v4/reference/rest).

Platforms to be looked at in Safe Browsing (PlatformType).
`SAFEBROWSING_PLATFORMS = ['ANY_PLATFORM']`

Types to be looked at in Safe Browsing (ThreatType).
`SAFEBROWSING_THREATTYPES = ['MALWARE']`

#### Sigma Analyzer

The Sigma Analyzer translates Sigma rules in OpenSearch Search Queries and adds a tag to every matching event.

It will also create a story with the Top 10 matched Sigma rules.

There is a dedicated document to walk you through the process of using the [Sigma Analyzer](sigma.md).

#### YetiIndicators Analyzer

This is a Index analyzer for [Yeti](https://yeti-platform.github.io/) threat intel indicators.

To use this Analyzer, the following parameter must be set with corresponding values in the `timesketch.conf`:

```config
YETI_API_ROOT = ''
YETI_API_KEY = ''
```
