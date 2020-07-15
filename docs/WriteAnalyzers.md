# Write analyzers in Timesketch

## analyzer_run.py

### Purpose

`analyzer_run.py` is a standalone python script made to bootstrap the 
development workflow to a minimum where only a file with events and
a class file with your analyzer code is needed.
You do not have to install Timesketch or any docker for that.

### running it the first time

To be able to run it, you need a python environment with some requirements
installed.

A good guide to install a venv is published by github [here](https://uoa-eresearch.github.io/eresearch-cookbook/recipe/2014/11/26/python-virtual-env/)

```
python3 analyzer_run.py
usage: analyzer_run.py [-h] [--test_file PATH_TO_TEST_FILE] PATH_TO_ANALYZER NAME_OF_ANALYZER_CLASS
analyzer_run.py: error: the following arguments are required: PATH_TO_ANALYZER, NAME_OF_ANALYZER_CLASS
```

### create your sample data

You can create your sample data either in CSV or JSONL with the same format
that Timesketch can ingest. To learn more about that visit [CreateTimelineFromJSONorCSV](CreateTimelineFromJSONorCSV.md) 

### use existing sample data

There is an event file shipped with Timesketch at:

```
timesketch/test_tools/test_events/sigma_events.jsonl
```

### Running it with parameters

The following command
```
PYTHONPATH=. python3 analyzer_run.py --test_file test_events/sigma_events.jsonl ../timesketch/lib/analyzers/sigma_tagger.py RulesSigmaPlugin
```

Will give you that output:
```
--------------------------------------------------------------------------------
                                     sigma
--------------------------------------------------------------------------------
Total number of events: 4
Total number of queries: 1

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  -- Query #01 --
              string: (data_type:("shell\:zsh\:history" OR "bash\:history\:command" OR "apt\:history\:line") AND "*apt\-get\ install\ zmap*")
                 dsl: None
             indices: ['MOCKED_INDEX']
              fields: ['tag', '__ts_emojis', 'human_readable', 'message']

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Sketch updates:
  ADD view
	{'name': '[sigma] Sigma Rule matches', 'query_string': 'tag:"sigma*"', 'query_dsl': None, 'query_filter': {'indices': '_all'}, 'additional_fields': None}
  ADD aggregation
	{'name': 'Top 20 Sigma tags', 'agg_name': 'field_bucket', 'agg_params': {'field': 'tag', 'limit': 20, 'supported_charts': 'table'}, 'description': 'Created by the Sigma analyzer', 'view_id': 1, 'chart_type': 'hbarchart', 'label': ''}
  ADD story
	{'title': 'Sigma Rule hits'}
  STORY_ADD text
	{'text': '\nThis is an automatically generated story that Sigma\nbased analyzers contribute to.\n', 'skip_if_exists': True}
  STORY_ADD text
	{'text': "## Sigma Analyzer.\n\nThe Sigma analyzer takes Events and matches them with Sigma rules.In this timeline the analyzer discovered 1 Sigma tags.\n\nThis is a summary of it's findings.", 'skip_if_exists': False}
  STORY_ADD text
	{'text': 'The top 20 most commonly discovered tags were:', 'skip_if_exists': False}
  STORY_ADD aggregation
	{'agg_id': 1, 'agg_name': 'Top 20 Sigma tags', 'agg_type': 'table', 'agg_params': {'field': 'tag', 'limit': 20, 'supported_charts': 'table'}}
  STORY_ADD text
	{'text': 'And an overview of all the discovered search terms:', 'skip_if_exists': False}
  STORY_ADD view
	{'view_id': 1, 'view_name': '[sigma] Sigma Rule matches'}

++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Event Updates:
  ADD tag
	[4] ['sigma_lnx_susp_zenmap']


++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Result from analyzer run:
  Applied 4 tags
* lnx_susp_zenmap: 4

=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-
```

### Remark

Do not try to run analyzer_run.py in your docker instance of Timesketch
as it will mix certain things with the actual installed Timesketch instance.
