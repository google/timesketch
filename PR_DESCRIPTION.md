# PR Title
feat(otel): instrument LLM providers for latency and prompt visibility

# PR Description

## Summary
This PR adds manual OpenTelemetry instrumentation to the core LLM providers in Timesketch (Google GenAI/Gemini, Ollama, and Azure AI). This enables deep observability into AI-driven features, allowing analysts to track request latency, model performance, and prompt context.

## Why this is important
LLM requests are often the most time-consuming part of an analysis workflow. Without tracing, it is difficult to distinguish between network lag, model processing time, or application-layer overhead. This PR makes these "black box" operations transparent in the trace waterfall.

## Changes
- **Google GenAI (Gemini):** Wrapped `generate()` in a span; captured `llm.provider`, `llm.model`, `llm.prompt_length`, and `llm.response_length`.
- **Ollama:** Wrapped `generate()` in a span; captured similar metadata for local LLM usage.
- **Azure AI:** Wrapped `generate()` in a span; captured similar metadata for Azure-hosted models.
- **Privacy by Design:** Full prompt and response text are intentionally **excluded** from telemetry to ensure no sensitive analyst conversation data is stored in the trace backend. Instead, we capture **character lengths**, providing sufficient data for performance and cost analysis without any risk of data leakage.
- **Error Handling:** Integrated OTel exception recording and status reporting for all model generation failures.

## Dependencies
This PR is designed to be merged **after** the core OpenTelemetry Phase 2 PR, as it relies on the `telemetry` helper and the global privacy scrubber.

## Verification
Verified locally using the Jaeger stack. LLM requests now appear as clear, attribute-rich spans under the parent API or task spans.
