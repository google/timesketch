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

## Troubleshooting

### Unable to run, no rule given to the analyzer

If you see that error in the Analyzer results, you likely have no rule installed that matches the Sigma analyzer criteria to use it.