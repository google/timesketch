# Timesketch LLM Prompts

This directory is the single, unified location for all LLM prompt files used by
Timesketch's AI-powered features. Consolidating prompts here simplifies
configuration, maintenance, and discoverability.

## Files

| File | Feature | Config Key |
|------|---------|-----------|
| `nl2q_prompt.txt` | Natural Language to Query (NL2Q) | `PROMPT_NL2Q` |
| `nl2q_examples.txt` | NL2Q few-shot examples | `EXAMPLES_NL2Q` |
| `nl2q_data_types.csv` | NL2Q data type descriptions | `DATA_TYPES_PATH` |
| `llm_summarize_prompt.txt` | Event summarization | `PROMPT_LLM_SUMMARIZATION` |
| `llm_synthesize_prompt.txt` | Investigative question synthesis | `PROMPT_LLM_SYNTHESIZE` |
| `llm_starred_events_report_prompt.txt` | Starred events forensic report | `PROMPT_LLM_STARRED_EVENTS_REPORT` |

## Customizing Prompts

To use custom prompts, copy this folder to your deployment configuration
directory (e.g. `/etc/timesketch/llm_prompts/`) and update the corresponding
paths in `timesketch.conf`.
