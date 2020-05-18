# Sigma Analyser in Timesketch

## What is Sigma

See description at the Sigma Github repository: https://github.com/Neo23x0/sigma#what-is-sigma

## Sigma in Timesketch

Since early 2020 Timesketch has Sigma support implemented. Sigma can be used as an analyser.

### Sigma Rules

The windows rules are stored in 
```
timesketch/data/windows
```

The linux rules are stored in
```
timesketch/data/linux
```

### Sigma config

In the config file
```
sigma_config.yaml
```

There is a section with mappings, most mappings where copied from HELK configuration.
If you find a mapping missing, feel free to add and create a PR.

###Field Mapping
Some adjustments verified:

- s/EventID/event_identifier
- s/Source/source_name

## Adding a new Operating System to support Sigma TS

To adda  new operating system or new set of rules, adjust the following file:
```
timesketch/timesketch/analyzers/sigma_tagger.py
```

In that file, specify, where your rules are stored and how they should appear in the Timesketch UI.

## Testing new rules

There is a folder in the data directory that has .gitignore content for createing new rules locally.
 
Folder:
```
timesketch/data/test_rules 
```

Which will show up in Timesketch UI as *a_sigma_test* on top of the analyzers.

Note: if you create new rules, you need to restart your celery worker to pick them up.

## Test data

If you want to test that feature, get some evtx files from the following
 links and parse it via plaso

- https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES
- https://github.com/sans-blue-team/DeepBlueCLI/evtx
