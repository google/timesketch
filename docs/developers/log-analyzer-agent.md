---
hide:
  - footer
  - title
---
### Developer Deep Dive: The Hybrid AI Log Analyzer Architecture

The AI-powered Investigation View introduces a powerful capability for automated,
large-scale log analysis. Unlike other LLM features that operate on-demand on a
small selection of events, the Log Analyzer is designed to process
**all active timelines** in a sketch, which can involve millions of events.
This requirement necessitates a robust, asynchronous, and streaming-native architecture.

This guide provides a technical deep dive into the components that power this
feature and outlines the API contract required to connect your own compatible log
analysis capability.

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
*   **Body:** A stream of newline-delimited JSON objects. Each object is a complete
              Timesketch event.

**Example Request Body (NDJSON stream):**

```json
{"_index": "a1b2c3d4...", "_id": "event_id_1", "_source": {"message": "User 'admin' logged in from 192.168.1.100", "timestamp": 1672531200000000, ...}}
{"_index": "a1b2c3d4...", "_id": "event_id_2", "_source": {"message": "Process 'evil.exe' created by pid 1234", "timestamp": 1672531201000000, ...}}
```

#### **Response Format**

Your agent should return a complete response as a single block of text. This
response must contain a markdown-formatted section that includes a JSON object
with the analysis findings.

*   **Headers:** `Content-Type: application/x-ndjson`
*   **Body:** A text response that includes a `**JSON Summary of Findings**` marker,
              followed by a JSON code block. Timesketch will parse the entire response
              to find and extract this specific JSON block.

**Finding List Schema:**

The Timesketch backend will parse the JSON block from the response. This block
should be a list of "finding" objects. The following table details the schema
for a single object within that list.

| Key | Type | Required | Description |
|---|---|---|---|
| `log_records` | List of Objects | **Yes** | A list of log record objects, each identifying a Timesketch event. |
| `annotations` | List of Objects | **Yes** | A list of annotation objects. Each annotation will generate DFIQ objects in Timesketch. |

Each object inside the `log_records` list must have the following structure:

**Annotation Object Schema:**

Each object inside the `annotations` list must have the following structure:

| Key | Type | Required | Description |
|---|---|---|---|
| `investigative_question` | String | **Yes** | The DFIQ question that was generated. This will become an `InvestigativeQuestion`. |
| `conclusions` | List of Strings | **Yes** | A list of answers or findings for the question. Each will become an `InvestigativeQuestionConclusion`. |
| `priority` | String | No | The priority for the question. Can be `low`, `medium`, or `high`. |
| `attack_stage` | String | No | A suggested attack stage (e.g., MITRE ATT&CK Tactic). This is stored as a question attribute. |

**Example of a Single Finding Object (from the list in the JSON block):**

```json
{
  "log_records": [
    { "record_id": "8XdJUJgB092O9Z5p3KNH" },
    { "record_id": "another_event_id" }
  ],
  "annotations": [
    {
      "attack_stage": "Initial access",
      "priority": "high",
      "investigative_question": "What is the initial access vector?",
      "conclusions": [
        "Successful password-based root login from a known Tor exit node."
      ]
    },
    {
      "attack_stage": "Persistence",
      "investigative_question": "What is the persistence mechanism?",
      "conclusions": ["Creation of a malicious cron job."]
    }
  ]
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

---

### Integrating Custom Tools and AI Scripts with the Investigation View

While the Hybrid AI Log Analyzer provides a powerful streaming interface, you
can also programmatically interact with the Investigation View using the
Timesketch API client. This is ideal for integrating your own external tools,
AI scripts, or workflows that generate investigative questions, conclusions,
and link them to specific events.

This approach allows you to populate the Investigation View with findings from
your custom analytics, making them immediately available to analysts within the
Timesketch UI.

Here’s how you can use the
[scenario.py](https://github.com/google/timesketch/blob/main/api_client/python/timesketch_api_client/scenario.py)
and [sketch.py](https://github.com/google/timesketch/blob/main/api_client/python/timesketch_api_client/sketch.py)
API client methods to achieve this.

#### Step 1: Add an Investigative Question

First, you need to add a question to your sketch. You can do this by using the
`add_question` method on a `Sketch` object. You can add a question that is
already part of your DFIQ library of questions or a free text question. This
will create a new `InvestigativeQuestion` in the Investigation View.

```python
from timesketch_api_client import config
from timesketch_api_client import sketch

# Authenticate and get a sketch object
my_sketch = config.get_client().get_sketch(1)

# Add a new question to the sketch
question_text = "What is the source of the anomalous network traffic?"
question = my_sketch.add_question(question_text=question_text)

print(f"Successfully added question '{question.name}' with ID: {question.id}")
```

#### Step 2: Add a Conclusion

Once you have a question object, you can add conclusions to it. A conclusion is
the answer or finding that your tool or script has generated for that specific
question. Use the `add_conclusion` method on the `Question` object.

The API response from adding a conclusion will contain the `id` of the newly
created conclusion, which you will need to link events to it.

```python
# Assume 'question' is the Question object from the previous step
conclusion_text = "The anomalous traffic originates from a compromised user's workstation (IP: 192.168.1.101)."
conclusion_response = question.add_conclusion(conclusion_text)

# Extract the conclusion ID from the API response
conclusion_objects = conclusion_response.get("objects", [])
if conclusion_objects:
    conclusion_id = conclusion_objects[0].get("id")
    print(f"Successfully added conclusion with ID: {conclusion_id}")
else:
    print("Failed to add conclusion.")
    conclusion_id = None
```

#### Step 3: Link Events to the Conclusion

The final and most crucial step is to link the events from your timeline that
support your conclusion. This provides the evidence for your findings. Use the
`link_event_to_conclusion` method on the `Sketch` object.

You need to provide the `conclusion_id` and a list of event dictionaries. Each
dictionary must contain the `_id` and `_index` of the event you want to link.
You would typically get these event details from a search query using
`sketch.explore()` or `sketch.search()`.

```python
# Assume 'my_sketch' is your Sketch object and 'conclusion_id' is from the previous step

# First, find the events you want to link.
# For example, search for events from the compromised IP.
search_results = my_sketch.explore(query_string='ip:"192.168.1.101"')
events_to_link = search_results.get("objects", [])

if events_to_link and conclusion_id:
    # Format the events for the linking method
    formatted_events = [
        {
            "_id": event.get("_id"),
            "_index": event.get("_index"),
        }
        for event in events_to_link
    ]

    # Link the events to the conclusion
    my_sketch.link_event_to_conclusion(
        events=formatted_events,
        conclusion_id=conclusion_id
    )
    print(f"Successfully linked {len(formatted_events)} events to conclusion ID: {conclusion_id}")
```

By following these steps, you can build powerful integrations that leverage your
own analytics and AI models to automatically populate the Timesketch
Investigation View, providing analysts with structured, evidence-backed findings
to accelerate their investigations.
