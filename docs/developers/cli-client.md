---
hide:
  - footer
---
# CLI Client

The CLI client is a Python application that can be used to interact with the REST API of Timesketch from the command line. It takes
care of setting up authentication, sending the API calls to the server, error handling, and presentation.

This documentation will give an overview for the most common developer use cases of the CLI client.

The main target audience for the CLI client is Timesketch user / analyst.
While some methods might have verbose JSON output, the default should be as tailored to analyst needs as the WebUI.

## Basic Connections

The CLI client defines a config library specifically intended to help with setting up all configuration for connecting to Timesketch, including
authentication and server information. The config client will read stored connection information from `~/.timesketchrc`, asking the user questions
if information is missing (and subsequently storing the results of those questions in the RC file for future lookups).

To be able to take advantage of the config client, the user needs to be running this from the command line or in a way where questions can be asked
and answered (or the config file to be fully populated). This works both in CLI scripts as well as in a notebook.

By default the client credentials will be stored on disk in a Token file, in an encrypted format, protected by a randomly generated
password that is stored in the RC file. 

If the token file does not exist, it will be generated and encrypted using the supplied password.

## Using the Timesketch Client

Please see [the CLI client guide](guides/user/cli-client)

## Concepts

The CLI client makes heavy usage of the [Click Python framework](https://click.palletsprojects.com/).

## Building a new local version

It is recommended to do the development work in a local dev docker instance.

Open a shell in your docker container.

Change to the Timesketch CLI source directory:

```bash
cd /usr/local/src/timesketch/cli_client/python
```

From there every time to make changes, run:

```bash
python3 setup.py build && python3 setup.py install --user
```

And you can run the latest local built version of the CLI client.

```bash
timesketch sketch list
1 aaa
```

## Debugging

Add a `breakpoint()` statement in the code you want to debug in the CLI tool.

```bash
python3 setup.py build && python3 setup.py install --user
```

Run it.

## Output

There is a general concept / setting for the output format.

The common output formats are:

* text
* csv
* tabular
* json
* jsonl

In the code have the following to retrieve the output_format from the context:

```python
    output = ctx.obj.output_format
```

And when data is about to be put out:

```python
    if output == "json":
        click.echo(sigma_rules.to_json(orient="records"))
    elif output == "jsonl":
        click.echo(sigma_rules.to_json(orient="records", lines=True))
    elif output == "csv":
        click.echo(sigma_rules.to_csv(header=header))
    elif output == "text":
        click.echo(
            sigma_rules.to_string(index=header, columns=columns),
        )
    else:
        click.echo(sigma_rules.to_string(index=header, columns=columns))
```

If a specific output format is not implemented, it is best practice to error out and tell the user which formats are implemented.

Depending on the command, some output formats might not make sense.

As shown in the code, there is also an option for `header` and `columns`

```python
# add a option for header or no header
@click.option(
    "--header/--no-header",
    default=True,
    help="Include header in output. (default is to show header))",
)
# add option for columns
@click.option(
    "--columns",
    default="rule_uuid,title",
    help="Comma separated list of columns to show. (default: rule_uuid,title)",
)
```

If there are more columns, it might be worth to add a `verbose` option:

```python
@click.option(
    "--verbose/--no-verbose",
    default=True,
    help="Make the output verbose. (default is no verbose))",
)
```

This can be especially helpful if your command could be used for API development where one wants all the data available for a API call and print it.


## Adding data to Timesketch

If you are working on a functionality to add data to Timesketch, there are some things to consider.

An example for a pull request that added a new functionality to add data is [this](https://github.com/google/timesketch/pull/2604).

If you want to enable the user to provide multiple values in a variable, consider using comma separated list.

E.g.

```python
...
@click.option(
    "--tag",
    required=False,
    help="Comma separated list of Tags to add to the event.",
)
...
```

And split it out in the code:

```python
...
if tag:
        tags = tag.split(",")
...
```

## Adding a new command group

In case you want to add a new command group to:

```bash
timesketch -h
Usage: timesketch [OPTIONS] COMMAND [ARGS]...

  Timesketch CLI client.

  This tool provides similar features as the web client does. It operates
  within the context of a sketch so you either need to provide an existing
  sketch or create a new one.

  Basic options for editing the sketch is provided, e.g. re-naming and
  changing the description as well as archiving and exporting. For other
  actions not available in this CLI client the web client should be used.

  For detailed help on each command, run  <command> --help

Options:
  --version         Show the version and exit.
  --sketch INTEGER  Sketch to work in.
  -h, --help        Show this message and exit.

Commands:
  analyze         Analyze timelines.
  config          Configuration for this CLI tool.
  events          Manage event.
  import          Import timeline.
  saved-searches  Managed saved searches.
  search          Search and explore.
  
  ...
```

Please consider the best logical way to place it to make it intuitive but also mimic the concepts in the Web UI. If you are unsure, it might be worth to reach out via a Github Issue, Slack or the Github discussions page first before start coding. Moving those parts later and refactor your code might be time intense.

In case the right place is found, do not forget to add the command group to `cli_client/python/timesketch_cli_client/cli.py`:

```python
...python
from timesketch_cli_client.commands import your_new_command
...
cli.add_command(your_new_command.your_new_command_group)
```

Then it will also show up in `timesketch -h`.

## Errors

If you handle errors, catch exceptions, consider setting the corresponding exit code instead of returning an error message.

### Error: No such option: --sketch

If you try to run a command without a sketch defined in the config and then using the parameter like:

```bash
timesketch timelines --sketch 1
Usage: timesketch timelines [OPTIONS] COMMAND [ARGS]...
Try 'timesketch timelines -h' for help.

Error: No such option: --sketch
```

The correct way of using the sketch parameter is:

```bash
timesketch --sketch 1 timelines
1 2k_random_events_time_distributed
2 2k_random_events_time_distributed_fixed_datetime
```

## Pull requests

If you create a pull request for a new / adjusted CLI command, please include

* Example input / output for a expected execution
* Example input / output for a "failed" execution e.g. data not found
* (Updated) documentation for timesketch.org
* (Updated) unit tests