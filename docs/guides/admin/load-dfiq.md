---
hide:
  - footer
---
# Loading DFIQ Template Data

This guide explains how to load DFIQ (Digital Forensics Investigative Questions)
template data into Timesketch. DFIQ data provides a structured way to ask
questions and provides approaches for digital forensic investigations.

Timesketch can load this data from two sources: the local filesystem or a
connected [YETI threat intelligence platform](https://yeti-platform.io/).
These sources can be used independently or together.

## Enabling DFIQ

Before loading any data, you must first enable the DFIQ feature in your
Timesketch configuration.

1.  Open your `timesketch.conf` file.
2.  Locate the `DFIQ_ENABLED` setting.
3.  Set the value to `True`.

With DFIQ enabled, you can now choose one or both of the following methods to
load template data.

---

## Option 1: Loading from the Filesystem

This method involves loading DFIQ YAML files directly from a directory on your
Timesketch server.

1.  **Configure the Path:**
    *   In your `timesketch.conf`, ensure the `DFIQ_PATH` setting points to your
        desired directory. The default is `/etc/timesketch/dfiq`.
2.  **Populate the Directory:**
    *   Navigate to the directory specified by `DFIQ_PATH`.
    *   It is recommended to import the full set of DFIQ data from the official
        [DFIQ repository](https://github.com/google/dfiq/tree/main/dfiq).
    *   Ensure your `DFIQ_PATH` folder is actually mapped into the `timesketch`
        containers!

---

## Option 2: Loading from YETI

Timesketch can dynamically fetch DFIQ templates directly from a connected
[YETI threat intelligence platform](https://yeti-platform.io/). This is useful
for centralizing your investigative questions alongside your threat intelligence.
YETI also provides a UI to create and organize DFIQ components like Scenarios and
Questions.

1.  **Enable YETI DFIQ Integration:**
    *   In `timesketch.conf`, set `YETI_DFIQ_ENABLED` to `True`.
2.  **Configure YETI API Credentials:**
    *   Set `YETI_API_ROOT` to the host of your YETI API endpoint (e.g., `http://yeti-api:8000`).
    *   Set `YETI_API_KEY` to a valid API key for your YETI instance.
3.  **(Optional) Configure TLS Certificate:**
    *   If your YETI instance uses a self-signed TLS certificate, set
        `YETI_TLS_CERTIFICATE` to the path of the certificate file so Timesketch
        can verify the connection.

## Combining Filesystem and YETI Sources

You can enable both filesystem and YETI sources simultaneously. When both are
active, Timesketch will load all templates from both locations.

**Important:** If a DFIQ template with the same UUID exists in both the local
filesystem and YETI, the version from **YETI will be used**, overwriting the
local one in memory.

---

## Applying Changes

1. **Restart Timesketch:**
    * After making any changes to `timesketch.conf` or the DFIQ filesystem
      directory, restart your Timesketch docker containers.
    * This ensures that the new configuration and DFIQ data are loaded and
      recognized by the system.

## Verification

After completing these steps, you should see the DFIQ Question elements available
in the "Investigative Questions" bar within your sketches.
