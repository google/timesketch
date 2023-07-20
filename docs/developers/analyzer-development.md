---
hide:
  - footer
---
# Write analyzers for Timesketch

## Overview

This guide provides all steps to get you started with building a new Timesketch
analyzer.

## Background

Timesketch analyzers are programs that run when new data is indexed, e.g. when
you upload a new plaso storage file or when adding an existing index to a
sketch. They can also be triggered manaully for a specific timeline from the
Analyzer tab in the UI after the index is finished.
You have access to a simple API that makes searching, commenting, tagging etc
easy. Everything you can do in the UI you can do programmatically.

## Analyzers

An analyzer can be auto-run on every new timeline that is added to a sketch or
manually triggered by the analyst. If you read somewhere about "sketch" and
"index" analyzers, this info is deprecated. There is now only one type of
analyzer.

An analyzer can search, correlate and enrich data in each given timeline. The
following methods to interact with an event in a timeline are available to the
analyzer:

+   Tag events.
+   Star events.
+   Comment on events.
+   Create saved views.
+   Add attributes to events.
+   Tag events with emojis.
+   Create/Add a story based on the analyzer output.
+   (soon) Build a graph.
+   (soon) Build aggregated views.

## Before you start

We have identified three tasks, that came up frequently as individual analyzer
ideas and made them easier. So please check if your analyzer idea matches any
of the following.

### Feature Extraction

If you just want to extract a simple feature, e.g. want to extract a hostname or
IP that is somewhere in the message field, or inside another attribute you don't
have to write a new analyzer, you can take advantage of the feature_extraction
analyzer. All you need to do is to edit the `features.yaml` file found here:
https://github.com/google/timesketch/blob/master/data/features.yaml

An example extraction entry looks like this:

```
name:
      query_string: 'my_secret_attribute:"look here"'
      # Mandatory fields.
      attribute: 'message'
      Store_as: 'secret'
      re: 'not a secret:([^\.]+).'
      # Optional fields.
      emojis: ['camera']
      tags: ['secret-entry']
      create_view: True
      aggregate: False
```

### Sigma Analyzer

The Sigma analyzer uses sigma rules from the community
[sigma project](https://github.com/SigmaHQ/sigma) and internally
developed/adjusted rules to detect and tag events in a timeline. It allows for
easy management of rules by modifying an existing rule or creating a new rule
from scratch directly in the Timesketch web UI. Write a sigma rule instead of a
new analyzer if you have a specific search query or an existing community rule
and want to tag all those events.

Check the
[sigma analyzer docs](https://github.com/google/timesketch/blob/master/docs/guides/analyzers/sigma_analyzer.md)
for more information.

### Tagger Analyzer

If your query requires a more advanced search query like dynamically tagging
based on values derived from event attributes, you should make use of the tagger
analyzer. This also allows you to tag all events based on a generic search query
and regex searches. See the
[tagger doc](https://github.com/google/timesketch/blob/master/docs/guides/analyzers/tagger.md)
for more information.

TIP: If your detection idea can be implemented with a Sigma rule use that
instead of the tagger analyzer!

To use it, just add a new tagger entry in the `tags.yaml` file:
https://github.com/google/timesketch/blob/master/data/tags.yaml

An example tagger entry looks like this:

```
test_tagger:
    query_string: 'test'
    tags: ['test-tag']
    emojis: ['FISHING_POLE']
    save_search: true
    search_name: 'TEST the tag'
```

## Build the analyzer

Ok, let’s get started!

### 1) Set Up your development environment

Follow the instructions in
[Timesketch development - Getting started](https://timesketch.org/developers/getting-started/)
to get everything up and running.

### 2) Generate the necessary analyzer templates

The first thing we are going to do is installing and running the l2t scaffolder
to generate the necessary files.

**Install the scaffolder**

Follow these instructions to install `l2tscaffolder` from source in a
virtualenv:
https://l2tscaffolder.readthedocs.io/en/latest/sources/user/Installation.html#install-from-sources

**Run the scaffolder to generate a sketch analyzer**

```shell
$ cd ~/timesketch/
$ l2t_scaffolder.py
```

TIP: If running `l2t_scaffolder.py` does not work, use
`$HOME/.local/bin/l2t_scaffolder.py`

1.  When you run the tool it will first ask you what system you want to generate
    templates for. Choose `timesketch`.
2.  Next you need to enter the path to the local Timesketch source repository.
3.  Name your new analyzer `best_analyzer`.
4.  Select `sketch_analyzer` to continue.

This should look like this:

```shell
$ cd ~/timesketch/
$ l2t_scaffolder.py
   == Starting the scaffolder ==
Gathering required information.

Available definitions:
  [0] plaso
  [1] timesketch
  [2] turbinia
Definition choice: 1
timesketch chosen.

Path to the project root: .
Path [.] set as the project path.

Name of the module to be generated. This can be something like "foobar sqlite"
or "event analytics".

This will be used for class name generation and file name prefixes.
Module Name: best_analyzer
About to create a new feature branch to store newly generated code.
Creating feature branch: best_analyzer inside .
Switching to feature branch best_analyzer

Available scaffolders for timesketch:
  [0] index_analyzer
  [1] sketch_analyzer
Scaffolder choice: 1
Ready to generate files? [Y/n]: Y
File: ./timesketch/lib/analyzers/best_analyzer.py written to disk.
File: ./timesketch/lib/analyzers/BEST_ANALYZER_test.py written to disk.
File: ./timesketch/lib/analyzers/__init__.py written to disk.
```

The scaffolder will create a new branch for you as well, so don't worry about
messing with the master branch.

```shell
$ git branch
  master
* best_analyzer
```

Three files will be edited/created.

```shell
$ git diff master --stat
 timesketch/lib/analyzers/__init__.py        |  1 +
 timesketch/lib/analyzers/best_analyzer.py      | 55 +++++++++++++++++++++
 timesketch/lib/analyzers/BEST_ANALYZER_test.py | 24 ++++++++++++++
 3 files changed, 80 insertions(+)
```

*\_\_init\_\_.py*

In this file the scaffolder has added the importing of the new analyzer here in
order to register it. You do not need to edit anything in this file as it is
automatically edited by the scaffolder.

```shell
# Register all analyzers here by importing them.
from timesketch.lib.analyzers import best_analyzer
from timesketch.lib.analyzers import similarity_scorer
```

*best_analyzer_test.py*

Test for the analyzer. This is out of scope for this guide and remains as an
exercise for the reader. To be able to run your tests you'll need to setup few
extra packages:

```shell
$ sudo apt-get install pylint python3.9-venv
```

And then to setup your virtualenv

```shell
$ python3 -m venv timesketch_dev
$ source timesketch_dev/bin/activate
$ cd ~/timesketch
$ pip install -r requirements.txt
$ pip install -r test_requirements.txt
```

Now you can run the tests: `$ ~/timesketch/run_tests.py`

*best_analyzer.py*

This is your new analyzer and it is here where all the logic goes. The entry
point for the analyzer is the `run()` method. You can choose to add all logic
here or create new methods etc.

There are six TODOs in the file and we are going to walk through all of them to
get a working analyzer. Out of the box the run() method looks like this:

```python
  NAME = 'best_analyzer'
  DISPLAY_NAME = 'best_analyzer'
  DESCRIPTION = '# TODO: best_analyzer description'

  [...]

def run(self):
   """Entry point for the analyzer.

   Returns:
       String with summary of the analyzer result
   """
   # TODO: Add Opensearch query to get the events you need.
   query = ''

   # TODO: Specify what returned fields you need for your analyzer.
   return_fields = ['message']

   # Generator of events based on your query.
   events = self.event_stream(
       query_string=query, return_fields=return_fields)

   # TODO: Add analyzer logic below.
   # Methods available to use for sketch analyzers:
   # sketch.get_all_indices()
   # (If you add a view, please make sure the analyzer has results before
   # adding the view.)
   # view = self.sketch.add_view(
   #     view_name=name, analyzer_name=self.NAME,
   #     query_string=query_string, query_filter={})
   # event.add_attributes({'foo': 'bar'})
   # event.add_tags(['tag_name'])
   # event.add_label('label')
   # event.add_star()
   # event.add_comment('comment')
   # event.add_emojis([my_emoji])
   # event.add_human_readable('human readable text', self.NAME)
   # Remember you'll need to add event.commit() once all changes to the
   # event have been completed.
   # You can also add a story.
   # story = self.sketch.add_story(title='Story from analyzer')
   # story.add_text('## This is a markdown title')
   # story.add_view(view)
   # story.add_text('This is another paragraph')

   for event in events:
       pass

   # TODO: Return a summary from the analyzer.
   return 'String to be returned'
```

### 3) Addressing the TODOs

It’s time to address the TODOs in the analyzer file.

### Metadata

Add a `DISPLAY_NAME` and `DESCRIPTION` for your analyzer in the top of the
class. This information will be used to list the analyzer on the "Analyzer"
tab in Timesketch. Make sure it describes what the analyzer does and should be
used for, since this is the information that analysts have at hand to decide
which analyzer to run on their timeline.

### The search query

The analyzer works on the results of a query that needs to be defined in
the `best_analyzer.py` file.

```python
   # TODO: Add Opensearch query to get the events you need.
   query = ''
```

The more specific a query is the faster can the analyzer iterate through the
results. So it is recommended to upload some test data in a new sketch and tweak
 the search query to find an optimal result that will be used in the analyzer.

### Return field

When you get results from Opensearch you can control what fields you need
returned. The fewer fields returned means less data in the response and less
overhead so a tip is to specify exactly the fields you will need for your
analyzer.

### Analyzer logic

The analyzer template provides a list with available functions to interact with
the sketch. Per default it will run the search query and get all resulting
events that can be iterated.

```python
   for event in events:
       # Analyzer logic starts here
```

At this point you can use everything that python offers to work with the
event data.

### Return message

The `BaseAnalyzer` class provides an `output` object that should be used to
define what the analyzer will display as a result in the UI.
The template provides an overview of output fields that are available.

#### Required fields

The following three fields need to be set by the analyzer author.

* `self.output.result_status (str): [SUCCESS, ERROR]`
    * Analyzer result status. Use `SUCCESS` when your analyzer ran without problems.
    Use `ERROR` when there are problems that prevent the analyzer from running,
    but not worth raising an exception. In the case of `ERROR` provide actionable
    feedback in the `result_summary` attribute!
* `self.output.result_priority (str): [NOTE, LOW, MEDIUM, HIGH]`
    * Priority of the result based on your analysis findings. `NOTE` is the default
    value and should be used for everything that is not actionable (e.g. enhancing
    data). The priority will be used to sort the analyzer results in the UI to
    highlight the most actionable (e.g. `HIGH`) at the top.
* `self.output.result_summary (str)`
    * A summary statement of the analyzer finding. A result summary must exist
    even if there is no finding. Use this field to explain the user what your
    analyzer found or did.
* All other required fields are set by the Analyzer framework automatically.

#### Optional fields

There are also some optional fields that can be set to further enhance the results
of your analyzer.

* `self.output.result_markdown (str)`
    * A detailed information about the analyzer results in a markdown format. Use
    this field if the result is not enough for its own story, but too much for
    the normal `result_summary`.
* `self.output.references (List[str])`
    * A list of references (URLs) about the analyzer or the issue the analyzer
    attempts to address. Use this to tell users where they can read more about
    how to interpret your analyzer results.
* Other optional fields like `saved_views`, `saved_stories` or `created_tags` are
set automatically when you use the BaseAnalyzer functions like `event.add_view()`
or `event.add_tags()`.

The analyzer `run()` method will then return `str(self.output)` which will verify
the output format and if everything is fine it will store a json string in the
database that will be interpreted by the new Timesketch UI.

## Multi Analyzer

When you develop an analyzer that would benefit from creating smaller sub-jobs,
you should use a Multi Analyzer.

For example The Sigma analyzer is such a Multi Analyzer. That means, the Sigma
analyzer is calling `get_kwargs()` from [sigma_tagger.py](https://github.com/google/timesketch/blob/master/timesketch/lib/analyzers/sigma_tagger.py).
That will return a list of all Sigma rules installed on the instance. The Main
celery job then spawns one celery job per Sigma rule that can run in parallel
or serial depending on the celery config and sizing of the Timesketch instance.

## Community contributed analyzers

This is currently an experiment and subject to rapid change!

`timesketch/lib/analyzers/contrib` hosts community contributed analyzers.
They are not maintained
by the core Timesketch development team.

Please read `timesketch/lib/analyzers/contrib/README.md` for more information.
