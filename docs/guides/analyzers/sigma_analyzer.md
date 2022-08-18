# Concept

The Sigma analyzer is a Multi Analyzer. That means each Sigma rule will create a dedicated celery job and provide results.

## Criteria to use a rule

To make a rule be used in the Analyzer:

- place it in a folder that is mentioned in the `SIGMA_RULES_FOLDERS=[]` section of `data/timesketch.conf`
- go to the Sigma tab of a sketch and check the rule is parsed correctly and the corresponding `es_query` is accurate
- add an entry in `sigma_rule_status.csv` with column `status` value: `good`
- go again to the Sigma tab and open the details of that rule and check the value of `'ts_use_in_analyzer': True`

Not every rule installed on a Timesketch server will be used by the Analyzer.
Reasons might be because:

- the rule caused parsing error
- the rule uses concepts that are not implemented from the Sigma project for the Timesketch / OpenSearch backend (e.g. Aggregations)
- the rule is marked 'bad' in `sigma_rule_status.csv` file
- the rule is located in a folder containing the term `deprecated`
- After parsing a rule the following value is set: `'ts_use_in_analyzer': False`

## Which rules should be deployed

It is not recommended to deploy all rules from https://github.com/SigmaHQ/sigma as it is impossible for the Timesketch project to ensure that all rules produce valid OpenSearch Queries.
Instead pick the rules you verified the format of your logs allign and you expect hits.

## Troubleshooting

### Unable to run, no rule given to the analyzer

If you see that error in the Analyzer results, you likely have no rule installed that matches the Sigma analyzer criteria to use it.

### Other errors

Please see the celery logs for further information.

### Find the rule that is causing problems

If you run into a problem after installing a new rule or multiple rules:

- seek the celery logs to identify the Sigma rule causing problems and identify the Sigma rule uuid
- remove all new rules and add rules individually till the error occurs and write down the Sigma rule uuid

Please open a Github issue in the Timesketch project providing the Sigma rule UUID (as long as it is part of https://github.com/SigmaHQ/sigma) and the exception shown in celery.