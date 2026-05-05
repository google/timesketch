# OpenTelemetry in Timesketch: Getting Started Guide

This document provides a comprehensive guide for developers, admins, and users on how OpenTelemetry (OTel) is implemented in Timesketch, how to configure it, and how to verify it locally.

---

## 1. Overview
Timesketch uses OpenTelemetry to provide distributed tracing across its web (Flask) and worker (Celery) components. This enables deep observability into request life cycles and background task performance.

### Key Benefits
*   **Distributed Tracing:** Track a single request from an external tool (like `dftimewolf`) through the API and into background analyzers.
*   **Log Correlation:** Trace IDs and Span IDs are automatically injected into structured JSON logs, allowing you to jump from a log line directly to a trace waterfall in tools like GCP Cloud Trace or Jaeger.
*   **Standardized Protocol:** Uses the industry-standard OpenTelemetry Protocol (OTLP).

---

## 2. Architecture
The instrumentation is centralized in a dedicated module: `timesketch/lib/telemetry.py`.

*   **Flask Instrumentation:** Automatically captures spans for all HTTP requests, including route patterns and status codes.
*   **Celery Instrumentation:** Captures spans for both task dispatching (producer) and execution (worker), maintaining the trace context across process boundaries.
*   **Async Exporting:** Spans are exported asynchronously using a `BatchSpanProcessor` to ensure minimal impact on application performance.

---

## 3. Configuration Reference
Telemetry is controlled entirely via environment variables.

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `TIMESKETCH_OTEL_MODE` | The export mode. Must start with `otlp-`. | `otlp-grpc`, `otlp-http`, `otlp-default-gce` |
| `TIMESKETCH_OTLP_GRPC_ENDPOINT` | OTLP collector endpoint (gRPC). | `jaeger:4317` |
| `TIMESKETCH_OTLP_HTTP_ENDPOINT` | OTLP collector endpoint (HTTP). | `http://jaeger:4318/v1/traces` |
| `TIMESKETCH_OTLP_INSECURE` | Use insecure (non-TLS) connection. | `true` (default for dev) |
| `TIMESKETCH_ENV` | Environment identifier. | `production`, `development` |

### Supported Modes:
1.  **`otlp-grpc`:** Best for local collectors (e.g., OTel Collector or Jaeger).
2.  **`otlp-http`:** Standard OTLP over HTTP/JSON.
3.  **`otlp-default-gce`:** **Recommended for production on GCP.** Sends traces directly to Google Cloud Trace API from a GCE instance using the Metadata Server for project identification and credentials.

---

## 4. Local Development & Testing

### Option A: Using Docker Compose
1. **Start the Core Environment:**
   Navigate to the dev docker directory and start the core services:
   ```bash
   cd docker/dev
   docker-compose up -d
   ```

2. **Start the Telemetry Stack (Optional):**
   Spin up the dedicated telemetry services (OTel Collector and Jaeger):
   ```bash
   docker-compose -f docker-compose-telemetry.yml up -d
   ```

**Note on Dependencies:**
Since the development image does not yet contain the new OpenTelemetry libraries, you must install them manually whenever the container is recreated:
```bash
docker exec timesketch-dev pip install -r /usr/local/src/timesketch/requirements.txt
# Ensure environment variables are set (uncomment in docker-compose.yml or set manually)
docker restart timesketch-dev
```

### Option B: Using Tilt
If you use Tilt for development, the telemetry stack is integrated automatically:
```bash
tilt up
```
The Tilt dashboard will show `otel-collector` and `jaeger` resources, including a direct link to the Jaeger UI.

---

## 5. Visualization Options

The local environment provides two ways to see your traces. You can switch between them by changing the `TIMESKETCH_OTLP_GRPC_ENDPOINT`.

### 1. Via OTel Collector (Gateway)
**Default Configuration:** `TIMESKETCH_OTLP_GRPC_ENDPOINT=otel-collector:4317`
*   **Why use this:** The collector acts as a gateway. It logs the raw spans to its own terminal (`docker logs -f otel-collector`) AND forwards them to Jaeger.
*   **Best for:** Seeing raw attributes and verifying the export pipeline.

### 2. Directly to Jaeger
**Custom Configuration:** `TIMESKETCH_OTLP_GRPC_ENDPOINT=jaeger:4317`
*   **Why use this:** Bypasses the collector and sends data straight to Jaeger.
*   **Access:** Open [http://localhost:16686/jaeger](http://localhost:16686/jaeger) in your browser.
*   **Best for:** Clean waterfall visualization and searching for past traces.

---

## 6. Triggering Activity & Verification
Generate some traffic to verify the setup:
```bash
# Trigger a Flask Trace (API Call)
docker exec timesketch-dev curl -s http://localhost:5000/api/v1/info/

# Trigger a Celery Trace (Run Analyzer)
docker exec timesketch-dev celery -A timesketch.lib.tasks call timesketch.lib.tasks.run_index_analyzer
```

**Check Application Logs:**
Verify that `trace_id` and `span_id` appear in the JSON output:
```bash
docker logs timesketch-dev | grep trace_id
```

---

## 7. Secure Private Access (GCP)
If you are running Timesketch on a private GCE VM without an external IP, you can "proxy in" securely using **Identity-Aware Proxy (IAP) Tunneling**.

### Accessing the Web Interfaces
Run these commands on your local machine to create a secure tunnel:

**Tip for Cloudtop Users:**
If you are on Cloudtop, the recommended way to connect is via the **BeyondCorp SUP Relay**.

**1. Direct SSH into the VM:**
```bash
ssh ${USER}_google_com@nic0.timesketch-otel-lab.us-central1-a.c.jaegeral-timesketch-946302.internal.gcpnode.com \
    -o ProxyCommand='corp-ssh-helper %h %p'
```

**2. Access Timesketch UI (Tunneling):**
You can use standard SSH port forwarding with the command above:
```bash
ssh -L 5000:localhost:5000 \
    ${USER}_google_com@nic0.timesketch-otel-lab.us-central1-a.c.jaegeral-timesketch-946302.internal.gcpnode.com \
    -o ProxyCommand='corp-ssh-helper %h %p'
```
Now open [http://localhost:5000](http://localhost:5000) in your browser.

**Alternative: Standard IAP Tunneling**
If the above doesn't work, you can use `gcloud` IAP tunnels:
```bash
gcloud compute start-iap-tunnel timesketch-otel-lab 5000 \
    --local-host-port=localhost:5000 \
    --zone=us-central1-a \
    --project=jaegeral-timesketch-946302 \
    --ssh-flag="-o ProxyCommand='corp-ssh-helper %h %p'"
```

---

## 8. Deployment Guide (GCP)
To enable production tracing in GCP:
1.  Set `TIMESKETCH_OTEL_MODE=otlp-default-gce`.
2.  Ensure the service account running Timesketch has the `roles/cloudtrace.agent` role.
3.  View your traces in the [GCP Trace Explorer](https://console.cloud.google.com/traces/explorer).

---

## 8. Information for Developers

### Automated Coverage
Most common operations are already covered by auto-instrumentation:
*   **Web API:** All Flask routes, status codes, and HTTP methods.
*   **Background Tasks:** All Celery task dispatching and executions.
*   **Analyzers:** All analyzers automatically report `sketch_id`, `analyzer_name`, `timeline_id`, and execution status via the `BaseAnalyzer` interface.

### Adding Custom Attributes & Events
If you need to record specific domain metadata (e.g., number of matches found, search query used) from within your code, use the helpers in `timesketch.lib.telemetry`.

#### Example: Adding attributes in an Analyzer
```python
from timesketch.lib import telemetry

def analyze(self):
    # ... logic ...
    matches_found = len(results)
    
    # This will appear in the Span attributes in Jaeger/GCP
    telemetry.add_attribute_to_current_span("sigma.matches_count", matches_found)
    
    # Record a significant milestone as an event
    telemetry.add_event_to_current_span("Finished parsing rules")
    
    return f"Found {matches_found} matches."
```

#### Best Practices for Attributes
*   **Use Namespace Prefixes:** To avoid collisions, prefix your attributes (e.g., `sigma.rule_id`, `sketch.member_count`).
*   **Data Types:** Simple types (strings, ints, bools, floats) are stored natively. Complex objects (dicts, lists) are automatically serialized to JSON.
*   **Avoid PII:** Never record sensitive user data or authentication tokens in span attributes.
