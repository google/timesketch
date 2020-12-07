# Sigma

## What is Sigma

See description at the [Sigma Github repository](https://github.com/Neo23x0/sigma#what-is-sigma)

## Sigma in Timesketch

Since early 2020 Timesketch has Sigma support implemented. Sigma can be used as an analyser.
The other option is to use Sigma via the API and the API client.

### Install rules

Timesketch deliberately does not provide a set of Sigma rules, as those would add complexity to maintain.
To use the official community rules you can clone [github.com/Neo23x0/sigma](https://github.com/Neo23x0/sigma) to /data/sigma.
This directory will not be catched by git.

```shell
cd data
git clone https://github.com/Neo23x0/sigma
```

The rules then will be under

```shell
timesketch/data/sigma
```

### Sigma Rules

The windows rules are stored in

```shell
timesketch/data/sigma/rules/windows
```

The linux rules are stored in

```shell
timesketch/data/linux
timesketch/data/sigma/rules/linux
```

### Sigma config

In the config file

```shell
sigma_config.yaml
```

There is a section with mappings, most mappings where copied from HELK configuration.
If you find a mapping missing, feel free to add and create a PR.

### Field Mapping

Some adjustments verified:

- s/EventID/event_identifier
- s/Source/source_name

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

## Toubleshooting

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

To reduce load on the system it is recommended to not keep the rules in the directory, as it will cause the exception every time the rules folders are parsed (a lot!).

The parser is made to ignore "deprecated" folders. So you could move the problematic rules to your rules folder in a subfolder /deprecated/.

If the rules do not contain any sensitive content, you could also open an issue in the timesketch project and or in the upstream sigma project and explain your issue (best case: provide your timesketch sigma config and the rule file so it can be verified).
