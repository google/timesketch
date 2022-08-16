# Sigma

## What is Sigma

See description at the [Sigma Github repository](https://github.com/Neo23x0/sigma#what-is-sigma)

## Sigma in Timesketch

Since early 2020 Timesketch has Sigma support implemented. Sigma can be used as an analyzer.
The other option is to use Sigma via the API and the API client or the Web interface.

### Web Interface

Sigma rules are exposed to the Web Interface as part of a sketch.

To list all Sigma rules, visit :

```
https://$TIMESKETCH/sketch/1/sigma/
```

This will show a table with all Sigma rules installed on a system. You can search for:

- Rule ID
- Title
- OpenSearch Search query (ES Query)
- File Name
- Tag

So if you want to search for ZMap related rules, you can search for `zma` in `Title, File Name` and it will show you the pre installed rule.

#### Hits

If you have run the Sigma Analyzer on a sketch and a rule has produced hits, the following fields will be added to the event:

* `ts_sigma_rule` will store the rule name that produced hits on an event.
* `ts_ttp` if a rule had ATT&CK(r) tags added, they will be added to this array

To query all rules that had Sigma rules matched in an analyzer run, query for:
`ts_sigma_rule:*`.

E.g. an event might have the following attributes:
```
ts_sigma_rule:[ "av_password_dumper.yml" ]
ts_ttp:[ "attack.t1003.002", "attack.t1003.001", "attack.credential_access", "attack.t1558", "attack.t1003" ]
```

#### ES Query

From that table, there are small icons to copy the values or explore the sketch with the given value. For example if you click the small lens icon next to the ES Query from the found rule `(data_type:("shell\:zsh\:history" OR "bash\:history\:command" OR "apt\:history\:line" OR "selinux\:line") AND "*apt\-get\ install\ zmap*")` it will open an explore view for this sketch with this query pre filled for you to explore the data.

#### Rule ID

If you click the rule ID `5266a592-b793-11ea-b3de-0242ac130004` a detail view for that rule will open up.

```bash
https://$TIMESKETCH/sketch/1/sigma/details?ruleId=5266a592-b793-11ea-b3de-0242ac130004
```

In this detail view all key and values of that rule that has been parsed by Timesketch are exposed.

### Install rules

Timesketch deliberately does not provide a set of Sigma rules, as those would add complexity to maintain.
To use the official community rules you can clone [github.com/Neo23x0/sigma](https://github.com/Neo23x0/sigma) to /data/sigma.
This directory will not be caught by git.

```shell
cd data
git clone https://github.com/Neo23x0/sigma
```

The rules then will be under

```shell
timesketch/data/sigma
```

### Sigma Rules sigma_rule_status file

The `data/sigma_rule_status.csv` is where Timesketch maintains a list of rules. 
Each rule can have one of the following status values: `good,bad,exploratory`.
* `exploratoy` rules will be shown in the UI but ignored in the Analyzer. So this status can be used to test rules. By default each rule is considered `exploratory`. 
* `good` rules will be used in the Sigma analyzer. 
* `bad` will be ignored and not shown in the UI or used in the Sigma analyzer.

It is good practice to add new rules in this file if they are tested and verified to not be compatible.

Each method that reads Sigma rules from the a folder is checking if part of the full path of a rule is mentioned in the `data/sigma_rule_status.csv` file.

For example a file at `/etc/timesketch/data/sigma/rules-unsupported/foo/bar.yml` would not be parsed as a line in `data/sigma_rule_status.csv` mentions:

```
/rules-unsupported/,bad,Sigma internal folder name,2021-11-19,
```

The header for that file are:

```
path,status,reason,last_checked,rule_id
```

### Sigma Rules

The windows rules are stored in

```shell
timesketch/data/sigma/rules/windows
```

The linux rules are stored in

```shell
timesketch/data/sigma/rules/linux
```

### Timesketch config file

There are multiple sigma related config variables in `timesketch.conf`.

```
# Sigma Settings

SIGMA_RULES_FOLDERS = ['/etc/timesketch/sigma/rules/']
SIGMA_CONFIG = '/etc/timesketch/sigma_config.yaml'
SIGMA_TAG_DELAY = 5
SIGMA_BLOCKLIST_CSV = '/etc/timesketch/sigma_rule_status.csv'
```

The `SIGMA_RULES_FOLDERS` points to the folder(s) where Sigma rules are stored. The folder is the local folder of the Timesketch server (celery worker and webserver). For a distributed system, mounting network shares is possible.

`SIGMA_TAG_DELAY`can be used to throttle the Sigma analyzer. If Timesketch is running on a less powerful machine (or docker-dev) a sleep timer of 15 seconds will help avoid OpenSearch Search exceptions for to many requests to the ES backend in a to short timerange. For more powerful Timesketch installations, this value can be set to 0.

### Sigma config

In the config file

```shell
sigma_config.yaml
```

There is a section with mappings, most mappings where copied from HELK configuration.
If you find a mapping missing, feel free to add and create a PR.

### Field Mapping

The field mappings are used to translate the generalised term from Sigma into the expected field names in Timesketch. Most of the field names in Timesketch are mapped to the expected output names of Plaso.

Some adjustments verified:

- s/EventID/event_identifier
- s/Source/source_name

There are many entries in https://github.com/google/timesketch/blob/master/data/sigma_config.yaml mapped to `xml_string`. This is because a lot of data in Windows EVTX XML is not valid XML and will be represented in the section `xml_string` (see https://github.com/log2timeline/plaso/issues/442).

Field mappings like:

```
  TargetFilename:
      product=linux: filename
      default: xml_string
```

Are interpreted depending on the selected product in the rule. If the product in the rule is `linux` the Selector `TargetFilename` in a rule would be tranlated to `filename:"foobar"`. If the product is anything else, e.g. `Windows` it would be `xml_string:"foobar"`

### Analyzer_run.py

You can run the Sigma analyzer providing sample data:

```shell
python3 test_tools/analyzer_run.py --test_file test_tools/test_events/sigma_events.jsonl timesketch/lib/analyzers/sigma_tagger.py RulesSigmaPlugin
```

## Test data

If you want to test that feature, get some evtx files from the following
links and parse it via plaso

- [github.com/sbousseaden/EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES)
- [github.com/sans-blue-team/DeepBlueCLI/evtx](https://github.com/sans-blue-team/DeepBlueCLI/evtx)

## Compose new rules

In the Sigma Tab in a sketch there is a toggle called `Compose Sigma rule`.
If turned on it will show a text area that takes the yaml text of a Sigma rule.
Once you are happy with your rule, click `Parse` and the rule will be parsed as if it is installed on Timesketch.

This feature can be helpful if you want to test out field mapping.

From the parse result you can copy the `es_query` value and paste it in a new window where you have the explore of a Sketch open.

You need to remember to copy your rule when you are ready and create a new file on your Timesketch server to store the rule and make it available to others. The text from the compose area will be reset with each reload of the page.

### Best practices

When writing Rules specific for Timesketch first and foremost you should the guide from one of the creators of Sigma:
[How to Write Sigma Rules](https://www.nextron-systems.com/2018/02/10/write-sigma-rules/).

### Date format

When setting the `date` field in your rule, stick to `YYYY/MM/DD`.

#### Number of or

On top of that, it is recommended to avoid a large chain or `or` checks.

```yaml
detection:
    keywords:
        - 'value1'
        - 'value2'
        - 'value3'
        ...
        - 'value20'
    condition: keywords
```

such a query would look like:
` *value1* or *value2* or *value3* ... or *value20*` because that results in a very expensive / long query to execute on the dataset.

Instead it is recommended to splice it into multiple rules:

Rule 1:

```yaml
detection:
    keywords:
        - 'value1'
        - 'value2'
        - 'value3'
        ...
        - 'value10'
    condition: keywords
```

and

Rule 2:

```yaml
detection:
    keywords:
        - 'value11'
        - 'value12'
        - 'value13'
        ...
        - 'value20'
    condition: keywords
```

That will create two queries:
` *value1* or *value2* or *value3* ... or *value10*` and ` *value11* or *value12* or *value13* ... or *value20*`.

The Sigma analyzer is designed to batch and throttle execution of queries which is beneficial for such rule structure.

### Reduce the haystack

If you can, define the haystack OpenSearch has to query. This can be achieved by adding a check for `data_type:"foosource"`.

## Verify rules

Deploying rules that can not be parsed by Sigma can cause problems on analyst side
as well as Timesketch operator side. The analyst might not be able to see
the logs and the errors might only occur when running the analyzer.

This is why a standalone tool can be used from:

```shell
test_tools/sigma_verify_rules.py
```

This tool takes the following options:

```shell
usage: sigma_verify_rules.py [-h] [--config_file PATH_TO_TEST_FILE]
                             PATH_TO_RULES
sigma_verify_rules.py: error: the following arguments are required: PATH_TO_RULES
```

And could be used like the following to verify your rules would work:

```shell
sigma_verify_rules.py --config_file ../data/sigma_config.yaml ../data/sigma/rules
```

If any rules in that folder is causing problems it will be shown:

```shell
sigma_verify_rules.py --config_file ../data/sigma_config.yaml ../timesketch/data/sigma/rules
ERROR:root:reverse_shell.yaml Error generating rule in file ../timesketch/data/sigma/rules/linux/reverse_shell.yaml you should not use this rule in Timesketch: No condition found
ERROR:root:recon_commands.yaml Error generating rule in file ../timesketch/data/sigma/rules/data/linux/recon_commands.yaml you should not use this rule in Timesketch: No condition found
You should NOT import the following rules
../timesketch/data/sigma/rules/linux/reverse_shell.yaml
../timesketch/data/sigma/rules/linux/recon_commands.yaml
```

## Troubleshooting

### How to find issues

#### Logs

In the celery logs, while running the sigma analyzer, you will see something like that:

```shell
result: Applied 0 tags
* win_apt_carbonpaper_turla.yml: 0
...
* win_syskey_registry_access.yml: 0
Problematic rules:
XXXX
```

The XXX here is the "problem" and you should note those rules. Once you note and identified those rules, it is recommended to take the id and attempt a API call like the following:

```python
from timesketch_api_client import config
ts = config.get_client()
rule = ts.get_sigma_rule("c0478ead-5336-46c2-bd5e-b4c84bc3a36e")
print(rule.es_query)
```

Where the ID is the id of your problematic rule. This will hopefully give you more insight from the web server logs of what caused the problem. E.g.
"Aggregations not implemented for this backend"
It is then recommended to move those rules to a separate folder, maybe even creating a small shell script that does that for you once you pull upstream rules from the Sigma repository.

### How to verify issues

#### Timesketch API / logs

If you have doubt if a rule does work, take the uuid and run python code mentioned above.

#### sigmac

Another option is to run the rule against the official sigma client with the Timesketch sigma mapping file.

For our example from above:

```shell
sigma/tools/sigma$ python3 sigmac.py -t es-qs --config ../../../sigma_config.yaml ../../rules/windows/image_load/sysmon_mimikatz_inmemory_detection.yml
An unsupported feature is required for this Sigma rule (../../rules/windows/image_load/sysmon_mimikatz_inmemory_detection.yml): Aggregations not implemented for this backend
Feel free to contribute for fun and fame, this is open source :) -> https://github.com/Neo23x0/sigma
```

### What to do with problematic rules

To reduce load on the system it is recommended to not keep the problematic rules in the directory, as it will cause the exception every time the rules folders are parsed (a lot!).

The parser is made to ignore "deprecated" folders. So you could move the problematic rules to your rules folder in a subfolder /deprecated/.

If the rules do not contain any sensitive content, you could also open an issue in the timesketch project and or in the upstream sigma project and explain your issue (best case: provide your timesketch sigma config and the rule file so it can be verified).
