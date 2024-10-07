---
hide:
  - footer
---
The Sigma analyzer is a Multi Analyzer. That means each Sigma rule will create a dedicated celery job and provide results.

## Criteria to use a rule

Status of a rule must be set to `stable`

Not every rule installed on a Timesketch server will be used by the Analyzer.
Reasons might be because:

- the rule caused parsing error
- the rule uses concepts that are not implemented from the Sigma project for the Timesketch / OpenSearch backend (e.g. Aggregations)

## Which rules should be deployed

It is not recommended to deploy all rules from https://github.com/SigmaHQ/sigma as it is impossible for the Timesketch project to ensure that all rules produce valid OpenSearch Queries.
Instead pick the rules you verified the format of your logs align and you expect hits.

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
