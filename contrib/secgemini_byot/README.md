# SecGemini Bring Your Own Tool (BYOT) client for Timesketch

This directory contains the code to build and run a client-side BYOT connection
tunnel for Google's SecGemini log analysis agent.

Instead of uploading raw log files to the cloud, this client establishes a secure
outbound reverse tunnel to SecGemini, exposing standard search and describe
tools that query your Timesketch server on-demand using the official
`timesketch-api-client`.

---

## Deployment Steps

### 1. Create a Bot User in Timesketch
It is recommended to run the BYOT client under a dedicated "bot user" profile (e.g. `sec-gemini-bot`):
1. Create a new user account in Timesketch.
  * `tsctl create-user --username sec-gemini-bot --password <password>`
2. **Sharing sketches:**
   * **Automatic (Recommended):** If you configure `byot_username` in the server's
      `timesketch.conf` (see Server Configuration below), the server will
      automatically share any analyzed sketch with the bot user.
   * **Manual:** Alternatively, manually use the "Share" button in the Timesketch
      UI and grant **Read** permission to your bot user.

### 2. Build the Docker Image
Build the image locally:

```bash
cd contrib/secgemini_byot/
docker build -t timesketch-secgemini-byot .
```

### 3. Run the Container
Run the container on a host that has network access to both the Timesketch
server API and the internet (to reach SecGemini API in the cloud).

Pass the credentials and configurations via environment variables:

```bash
docker run -d \
  --name timesketch-byot-client \
  --restart unless-stopped \
  -e TIMESKETCH_URL="<Timesketch-URL>" \
  -e TIMESKETCH_USERNAME="<sec-gemini-bot>" \
  -e TIMESKETCH_PASSWORD="<password>" \
  -e SEC_GEMINI_API_KEY="<your-secgemini-cloud-api-key>" \
  -e TUNNEL_NAME="byot-sec-gemini-bot" \
  timesketch-secgemini-byot
```

> [!TIP]
> **Automatic Recovery:** We strongly recommend running the container with
> `--restart unless-stopped` (or `--restart always`). The BYOT client runs an
> internal health check every 5 seconds and will exit automatically if the
> reverse tunnel disconnects, allowing Docker to restart it and re-establish a
> clean websocket connection within seconds.

> [!NOTE]
> If running in a local development environment (e.g., Docker Compose), you may
> need to attach the container to the same network as the Timesketch instance:
> `--network timesketch-network` and set `TIMESKETCH_URL="http://timesketch:5000"`.

### Environment Variables

| Variable | Description | Required |
| :--- | :--- | :--- |
| `TIMESKETCH_URL` | Root URL of the Timesketch instance (e.g. `https://timesketch.example.com`) | Yes |
| `TIMESKETCH_USERNAME` | Username of the bot or analyst account | Yes |
| `TIMESKETCH_PASSWORD` | Password of the bot or analyst account | Yes |
| `SEC_GEMINI_API_KEY` | Your Google Cloud API Key for SecGemini | Yes |
| `SEC_GEMINI_HOST` | Custom endpoint/host for the SecGemini Hub (e.g. to route to internal or staging endpoints) | No |
| `TUNNEL_NAME` | Name of the reverse tunnel. Must match `byot_tunnel_name` in the Timesketch server configuration. Default: `byot-sec-gemini-bot` | No |

---

## Server Configuration
For this tunnel to work, the Timesketch server must know not to upload logs and
instead reference the tunnel name.

In your Timesketch server's `timesketch.conf`, configure the
`secgemini_log_analyzer_agent` provider:

```python
LLM_PROVIDER_CONFIGS = {
    "secgemini_log_analyzer_agent": {
        "host": "",
        "api_key": "<SEC-GEMINI-API-KEY>",
        # Disable log uploading
        "upload_logs_to_secgemini": False,
        # Specify the name of the tunnel created by this client container
        "byot_tunnel_name": "byot-sec-gemini-bot",
        # Automatically grant access to this bot user when triggering analysis
        "byot_username": "sec-gemini-bot",
        "meta": {},
    }
}
```

---

## Ownership & Support
* [samomi-oss](https://github.com/samomi-oss)
* [jkppr](https://github.com/jkppr)
