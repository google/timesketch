---
hide:
  - footer
---
# Investigation View: Deployment and Configuration

The Investigation View is a new feature in the v3 user interface designed to
streamline forensic analysis with structured questions, findings, and optionally
AI-powered assistance. This guide walks administrators through deploying the
necessary container and configuring the feature.

---

### 1. Deploying the v3 User Interface Container

Timesketch is transitioning to a new user interface built with Vue3, referred to
as `frontend-v3`. This new interface runs in a separate Docker container
alongside the existing Timesketch services. To enable it, you need to activate
the `v3-ui` profile in your Docker Compose setup.

**Prerequisites:**

*   A standard Timesketch installation using Docker Compose, as outlined in the
    [installation guide](/guides/admin/install/).
*   If you have an existing Timesketch deployment, please ensure to collect the
    latest version of the files in the [data](https://github.com/google/timesketch/tree/master/data)
    folder and [nginx.conf](https://github.com/google/timesketch/blob/master/contrib/nginx.conf).

**Steps:**

1.  **Navigate to your Timesketch directory:**

    Open a terminal and change to the directory where your `docker-compose.yml`
    file is located (e.g., `/opt/timesketch`).

1.  **Stop your current Timesketch instance (if running):**

    ```bash
    sudo docker compose down
    ```

1. **Update your nginx.conf**

   Open the `nginx.conf` file in your `etc/` folder and uncomment the
   `location /v3/` section.

1.  **Start Timesketch with the v3 UI profile:**

    When starting your Timesketch instance, add the `--profile v3-ui` flag to
    your `docker compose up` command. This tells Docker to also start the
    `timesketch-web-v3` service defined in the compose file.

    ```bash
    sudo docker compose --profile v3-ui up -d
    ```

    Your Timesketch instance will now be running with both the standard UI and
    the new v3 UI container. Your Nginx service will automatically route traffic
    to the appropriate container, so you can access your Timesketch instance
    using the same URL as before.

### 2. Enabling the Investigation View

The Investigation View is a powerful new feature within the v3 interface that
provides a structured environment for managing investigative questions,
documenting findings, and generating reports. To use it, you must enable a few
settings in your `timesketch.conf` file. We also recommend to ensure the DFIQ
(Digital Forensics Investigative Questions) data is loaded correctly.

**Steps:**

1.  **Enable the necessary settings in `timesketch.conf`:**

    *   Open your `timesketch.conf` file for editing. This file is typically
        located in `etc/timesketch/` within your main Timesketch data directory.
    *   Find and set the following variables to `True`:

        ```python
        # In /etc/timesketch/timesketch.conf
        DFIQ_ENABLED = True
        ENABLE_V3_INVESTIGATION_VIEW = True
        ```

1.  [optional] **Load the DFIQ Template Data:**

    The Investigation View works better with DFIQ templates. If you haven't
    already, follow the guide to [load the DFIQ template data](https://timesketch.org/guides/admin/load-dfiq/).
    This involves replacing the default `data/dfiq` directory with the contents
    from the official DFIQ repository.

3.  **Restart Timesketch:**

    For the configuration changes to take effect, you must restart your Docker
    containers.

    ```python
    # In your Timesketch directory (e.g., /opt/timesketch)
    sudo docker compose -f /opt/timesketch/docker-compose.yml --env-file /opt/timesketch/config.env down
    sudo docker compose -f /opt/timesketch/docker-compose.yml --env-file /opt/timesketch/config.env --profile v3-ui up -d
    ```

4.  **Verification:**

    *   Log in to your Timesketch instance.
    *   Navigate to any sketch.
    *   You should now see a new **"Investigation"** tab in the top of the Left Panel.

### 3. Connecting the LLM Answer Drafting feature


The Investigation View includes LLM text drafting features (e.g. drafting an
answer based on conclusions) that can be enabled with default LLM services.

1. Follow the steps described for [configuring LLM Features](/guides/admin/llm-features/)
2. Add your prefered LLM provider for the new `llm_synthesize` feature in your `timesketch.conf`.
3. Ensure the prompt file configured in `PROMPT_LLM_SYNTHESIZE` exists and the
   prompt works for your needs.

### 4. Connecting the AI Investigation Agent

The Investigation View includes an experimental AI mode designed to support workflows
utilizing AI Log Reasoning Agents wich automate the generation of key findings
and investigative questions by analyzing timeline data. This feature is powered
by a dedicated AI agent service that must be configured by an administrator.

**How it Works**

When a user triggers the "Generate Initial Report" in the Investigation View,
Timesketch sends all timeline data to an external AI service defined in the
`timesketch.conf` file for the `log_analyzer` feature. This service processes
the data and sends back structured findings and questions.

> **IMPORTANT 1**: We have developed and tested the AI feature with the experimental
> Sec-Gemini Log Reasoning Agent. Sec-Gemini and the Agent are not open-source,
> and not yet openly available.
> However, if you want to apply for trusted tester access, you can do this via this
> form: https://bit.ly/46x9GLr

> **IMPORTANT 2**: We encurage everyone to experiment with their own AI Agent
> frameworks. Head to the [developer section](/developers/log-analyzer-agent/)
> to learn more about how to design and deploy your own provider file and what
> Timesketch expects as response format to work with the AI Investigation View Mode.

**Configuration Steps:**

1.  **Configure the Agent Endpoint in `timesketch.conf`:**

    Once your agent is running, or you have gotten access to Sec-Gemini's
    Log Reasoning Agent, you need to tell Timesketch how to communicate with it.
    *   Open your `timesketch.conf` file for editing.
    *   Locate the `LLM_PROVIDER_CONFIGS` dictionary.
    *   Within this dictionary, configure the `log_analyzer` section to use your
        custom provider endpoint or the Sec-Gemini service.

    **Example Configuration:**

    ```python
    # In /etc/timesketch/timesketch.conf
    LLM_PROVIDER_CONFIGS = {
        # ... other feature configs ...

        'log_analyzer':
        {
            # This feature requires a dedicated log analyzer agent service.
            '<PROVIDER>_log_analyzer_agent': {
                'server_url': '<YOUR_AGENT_API_ENDPOINT>',
                'api_key': '<YOUR_AGENT_API_KEY>',
            }
        },
    }
    ```

    *   **`server_url`**: This is the API endpoint URL of your deployed AI agent.
    *   **`api_key`**: If your agent requires an API key for authentication, provide it here.
    *   Those values can vary depending on the provider you are using.

3.  **Restart Timesketch:**
    After saving your changes to `timesketch.conf`, restart the Docker containers
    to apply the new configuration.

    ```bash
    sudo docker compose -f /opt/timesketch/docker-compose.yml --env-file /opt/timesketch/config.env down
    sudo docker compose -f /opt/timesketch/docker-compose.yml --env-file /opt/timesketch/config.env --profile v3-ui up -d
    ```

With these steps completed, your users can now leverage the AI-powered features
within the Investigation View to accelerate their forensic analysis workflows.

#### For Developers: Building an AI Agent

The setup of the AI log reasoning agent provider itself is a developer-focused task.
Documentation on creating a compatible agent service can be found in the
[Developer Guides](/developers/log-analyzer-agent/)
