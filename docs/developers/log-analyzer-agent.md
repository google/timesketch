### Developer Deep Dive: The Hybrid AI Log Analyzer Architecture

The AI-powered Investigation View introduces a powerful capability for automated,
large-scale log analysis. Unlike other LLM features that operate on-demand on a
small selection of events, the Log Analyzer is designed to process
**all active timelines** in a sketch, which can involve millions of events.
This requirement necessitates a robust, asynchronous, and streaming-native architecture.

This guide provides a technical deep dive into the components that power this
feature and outlines the API contract required to connect your own compatible log
reasoning agent.

#### Architectural Overview: A Hybrid Approach

To handle potentially long-running analysis tasks without timing out web requests,
we've implemented a hybrid architecture that combines Timesketch's existing
**Analyzer Framework** with the new **LLM Feature and Provider** system.

This approach gives us the best of both worlds:
*   **Asynchronous Execution:** The analysis is triggered as a Celery background
    task, preventing API timeouts and allowing the user to continue working while
    the analysis runs.
*   **Decoupling and Reusability:** The core logic is encapsulated in the LLM
    Feature and Provider, separating it from the task queue system.
*   **Scalability:** The architecture is built on streaming data (NDJSON),
    ensuring that memory usage remains low on both the Timesketch server and the
    AI agent, regardless of the number of events.

The three key components are:

1.  **The Analyzer (`llm_log_analyzer`):** The trigger and Celery task wrapper.
2.  **The Feature (`LogAnalyzer`):** The orchestrator of the entire workflow.
3.  **The Provider (`SecGeminiLogAnalyzer`):** The communicator that handles the
    streaming connection to the external AI agent.

#### Component Breakdown

**1. The Analyzer: Triggering the Workflow**

The `LLMLogAnalyzer` is a lightweight `BaseAnalyzer` plugin. Its sole
responsibility is to initiate the analysis process on a Celery worker.

*   **File:** `timesketch/lib/analyzers/llm_log_analyzer.py`

```python
# A simplified view of the analyzer's run method
class LLMLogAnalyzer(interface.BaseAnalyzer):
    NAME = "llm_log_analyzer"
    # ...

    def run(self):
        # 1. Get the feature instance
        feature_instance = feature_manager.FeatureManager.get_feature_instance(
            "log_analyzer"
        )

        # 2. Get the LLM provider instance
        llm_provider = llm_provider_manager.LLMManager.create_provider(
            feature_name=feature_instance.NAME
        )

        # 3. Call the feature's execute method to start the real work
        result = feature_instance.execute(
            sketch=self.sketch.sql_sketch,
            form={},
            llm_provider=llm_provider,
        )

        # 4. Summarize the result and update the analyzer status in the UI
        self.output.result_summary = f"Log Analyzer finished. Processed {result.get('total_findings_processed', 0)} findings."
        return str(self.output)
```

When a user clicks "Generate Initial Report", this analyzer is queued. It runs
in the background, instantiates the necessary LLM feature and provider, and then
calls the `execute` method to kick off the main logic.

**2. The Feature: Orchestrating the Data Flow**

The `LogAnalyzer` feature is the heart of the operation. It manages the entire
process from data extraction to result processing.

*   **File:** `timesketch/lib/llms/features/log_analyzer.py`

Its `execute` method orchestrates the following steps:

1.  **Prepare Log Stream:** It calls `prepare_log_stream_for_analysis`, which
    creates a Python generator that yields events one by one from all active
    timelines in the sketch using the OpenSearch `sliced_scroll` API. This ensures
    data is streamed efficiently from the datastore.
2.  **Invoke Provider:** It passes this log generator to the LLM provider's
    `generate_stream_from_logs` method.
3.  **Process Findings Stream:** It receives a generator of "findings" back from
    the provider. It iterates through each finding as it arrives.
4.  **Commit to Database:** For each finding, it calls its own `process_response`
    method, which creates and commits the necessary `InvestigativeQuestion` and
    `InvestigativeQuestionConclusion` objects to the PostgreSQL database.

**3. The Provider: Communicating with the AI Agent**

The `SecGeminiLogAnalyzer` provider acts as the client for the external AI agent.
It is responsible for the network communication.

*   **File:** `timesketch/lib/llms/providers/secgemini_log_analyzer_agent.py`

Key methods:

*   `_stream_log_data_as_ndjson_gen`: This helper method takes the Python
    generator of log events from the feature and converts each event into a
    line of a **Newline Delimited JSON (NDJSON)** stream.
*   `generate_stream_from_logs`: This is the main communication method.
    *   It initiates a streaming `requests.post` call to the AI agent's API endpoint.
    *   The `data` parameter of the request is the NDJSON generator, which streams
        the log data to the agent.
    *   It then listens to the response stream from the agent, using
        `response.iter_lines()` to read the incoming NDJSON findings one by one.
    *   It `yields` each finding back to the feature layer for processing.

---

### Experiment With Your Own Log Reasoning Agent

To integrate your own custom log analysis service, you need to build an HTTP
service that adheres to the API contract expected by the `SecGeminiLogAnalyzer`
provider or create your own custom provider file similar to the `SecGeminiLogAnalyzer`
that works with the `log_analyzer` feature.

**API Contract:**

#### **Endpoint**
Your service must expose an endpoint to receive the log data. The default is `/analyze_logs`.

#### **Request Format**
The provider will send a streaming `POST` request with the following characteristics:
*   **Method:** `POST`
*   **Headers:**
    *   `Content-Type: application/x-ndjson`
    *   `Accept: application/x-ndjson`
*   **Body:** A stream of newline-delimited JSON objects. Each object is a complete Timesketch event.

**Example Request Body (NDJSON stream):**
```json
{"_index": "a1b2c3d4...", "_id": "event_id_1", "_source": {"message": "User 'admin' logged in from 192.168.1.100", "timestamp": 1672531200000000, ...}}
{"_index": "a1b2c3d4...", "_id": "event_id_2", "_source": {"message": "Process 'evil.exe' created by pid 1234", "timestamp": 1672531201000000, ...}}
```

#### **Response Format**
Your agent must stream back a response with the following characteristics:
*   **Headers:** `Content-Type: application/x-ndjson`
*   **Body:** A stream of newline-delimited JSON objects. Each line should be a
    complete, self-contained JSON object representing a question and "finding"
    that links back to an original Timesketch event.

**Finding Object Schema:**

The Timesketch backend will parse each incoming JSON object from the stream.
The following table details the schema for a single finding object.

| Key | Type | Required | Description |
|---|---|---|---|
| `record_id` | String | **Yes** | The `_id` of the original Timesketch event this finding relates to. |
| `annotations` | List of Objects | **Yes** | A list of annotation objects. Each annotation will generate DFIQ objects in Timesketch. |
| `_index` or `__ts_index_name` | String | No | The OpenSearch index of the original event. Including this is recommended for performance. |
| `error` | String | No | If an error occurred while processing, send an object with this key instead of a finding. |

**Annotation Object Schema:**

Each object inside the `annotations` list must have the following structure:

| Key | Type | Required | Description |
|---|---|---|---|
| `investigative_question` | String | **Yes** | The DFIQ question that was generated. This will become an `InvestigativeQuestion`. |
| `conclusions` | List of Strings | **Yes** | A list of answers or findings for the question. Each will become an `InvestigativeQuestionConclusion`. |
| `priority` | String | No | The priority for the question. Can be `low`, `medium`, or `high`. |
| `attack_stage` | String | No | A suggested attack stage (e.g., MITRE ATT&CK Tactic). This is stored as a question attribute. |

**Example of a Single Finding Object (one line in the NDJSON stream):**
```json
{
  "annotations": [
    {
      "attack_stage": "Initial access",
      "priority": "high",
      "investigative_question": "What is the initial access vector?",
      "conclusions": [
        "Successful password-based root login from a known Tor exit node IP address, indicating potential anonymity seeking by the attacker."
      ]
    },
    {
      "attack_stage": "Persistence",
      "investigative_question": "What is the persistence mechanism?",
      "conclusions": [
        "Creation of a malicious cron job file for cryptocurrency mining."
      ]
    }
  ],
  "record_id": "8XdJUJgB092O9Z5p3KNH",
}
```

**A Note on API Flexibility:**

The Timesketch `log_analyzer` feature will only parse the fields specified as
"Required" in the schemas above. Any other fields in your finding or annotation
objects will be safely ignored. This allows you to include additional metadata
in your agent's output for your own logging or debugging purposes without
breaking the integration. If you want to utilize any additional fields, you need
to create your own LLM feature file.

#### **Configuration in Timesketch**

Once your agent is deployed, update your `timesketch.conf` to point to it:

```python
LLM_PROVIDER_CONFIGS = {
    'log_analyzer': {
        '<PROVIDER>_log_analyzer_agent': {
            'server_url': 'http://YOUR_AGENT_HOST:PORT',
            'api_key': '<YOUR_API_KEY_IF_ANY>',
        }
    }
}
```

By following this architecture and API contract, you can seamlessly integrate
custom, large-scale log analysis capabilities into the Timesketch Investigation View.
