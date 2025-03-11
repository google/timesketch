---
hide:
  - footer
---

# LLM Features Configuration

Timesketch includes experimental features leveraging Large Language Models (LLMs) to enhance analysis capabilities. These features include event summarization and AI-generated queries (NL2Q - Natural Language to Query). This document outlines the steps required to configure these features for Timesketch administrators.

## LLM Provider Configuration

To utilize the LLM features, the Timesketch **administrator** must configure an LLM provider in the `timesketch.conf` file. It's possible to configure a specific LLM provider and model per LLM powered feature, or to use a default provider. For most features we recommend using a fast model (such as `gemini-2.0-flash-001` ) for optimal performance, especially for the event summarization feature.

Edit your `timesketch.conf` file to include the `LLM_PROVIDER_CONFIGS` dictionary.  Below is a sample configuration with explanations for each parameter.

```python
# LLM provider configs
LLM_PROVIDER_CONFIGS = {
    # Configure a LLM provider for a specific LLM enabled feature, or the
    # default provider will be used.
    # Supported LLM Providers:
    # - ollama:  Self-hosted, open-source.
    #   To use the Ollama provider you need to download and run an Ollama server.
    #   See instructions at: https://ollama.ai/
    # - vertexai: Google Cloud Vertex AI. Requires Google Cloud Project.
    #   To use the Vertex AI provider you need to:
    #   1. Create and export a Service Account Key from the Google Cloud Console.
    #   2. Set the GOOGLE_APPLICATION_CREDENTIALS environment variable to the full path
    #      to your service account private key file by adding it to the docker-compose.yml
    #      under environment:
    #      GOOGLE_APPLICATION_CREDENTIALS=/usr/local/src/timesketch/<key_file>.json
    #   3. Verify your instance has the `google-cloud-aiplatform` lib installed.
    #     * $ sudo docker exec timesketch-web pip list | grep google-cloud-aiplatform
    #     * You can install it manually using:
    #       $ sudo docker exec timesketch-web pip install google-cloud-aiplatform==1.70.0
    #
    #   IMPORTANT: Private keys must be kept secret. If you expose your private key it is
    #   recommended to revoke it immediately from the Google Cloud Console.
    # - aistudio: Google AI Studio (API key).  Get API key from Google AI Studio website.
    #   To use Google's AI Studio simply obtain an API key from https://aistudio.google.com/
    #   Verify your instance runs the required library:
    #     * $ sudo docker exec timesketch-web pip list | grep google-generativeai
    #     * You can install it manually using:
    #       $ sudo docker exec timesketch-web pip install google-generativeai==0.8.4
    'nl2q': {
        'vertexai': {
            'model': 'gemini-2.0-flash-001',
            'project_id': '', # Required if using vertexai
        },
    },
    'llm_summarization': {
        'aistudio': {
            'model': 'gemini-2.0-flash-001', # Recommended model
            'api_key': '', # Required if using aistudio
        },
    },
    'default': {
        'ollama': {
             'server_url': 'http://localhost:11434',
             'model': 'gemma2-2b-it',
        },
    }
}
```

**Note:**  While [users can enable/disable these features](../user/llm-features-user.md), the underlying LLM provider and its configuration are managed by the Timesketch administrator. Enabling these features may incur costs depending on the chosen LLM provider. Please review the pricing details of your selected provider before enabling these features.

## Prompt and Data Configuration

Administrators can further customize the behavior of the LLM features by configuring the paths to various prompt and data files within the `timesketch.conf` file.

```python
# LLM nl2q configuration
DATA_TYPES_PATH = '/etc/timesketch/nl2q/data_types.csv'
PROMPT_NL2Q = '/etc/timesketch/nl2q/prompt_nl2q'
EXAMPLES_NL2Q = '/etc/timesketch/nl2q/examples_nl2q'

# LLM event summarization configuration
PROMPT_LLM_SUMMARIZATION = '/etc/timesketch/llm_summarize/prompt.txt'
```

*   `DATA_TYPES_PATH`: Specifies the path to a CSV file defining common Timesketch data types for the NL2Q feature.
*   `PROMPT_NL2Q`: Specifies the path to the prompt file used by the NL2Q feature to translate a natural language into a Timesketch search query.
*   `EXAMPLES_NL2Q`: Specifies the path to the examples file used by the NL2Q feature. This file provides the LLM with examples of natural language queries and their corresponding Timesketch search queries, which help improve the accuracy of the NL2Q feature.
*   `PROMPT_LLM_SUMMARIZATION`: Specifies the path to the prompt file used by the event summarization feature.  Administrators can modify this file to customize the summarization output to their specific needs. This template allows for injecting the event data into the prompt using Python-style string formatting using curly braces `{}`.
Timesketch provides some default configuration files for both features:
* [NL2Q default configuration](https://github.com/google/timesketch/tree/master/data/nl2q).
* [LLM Summarization default configuration](https://github.com/google/timesketch/tree/master/data/llm_summarize).
