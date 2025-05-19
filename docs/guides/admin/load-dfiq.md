---
hide:
  - footer
---
# Loading DFIQ Template Data

This guide explains how to load DFIQ (Digital Forensics Investigative Questions)
template data into Timesketch. DFIQ data provides a structured way to ask
questions and provides approaches for digital forensic investigations.

## Steps

Follow these steps to load the DFIQ template data:

1.  **Enable DFIQ:**
    *   Open your `timesketch.conf` file.
    *   Locate the `DFIQ_ENABLED` setting.
    *   Set the value to `True`.
2.  **Replace DFIQ folders:**
    *   Navigate to the default Timesketch
        [data/dfiq](https://github.com/google/timesketch/tree/master/data/dfiq)
        directory.
    *   Delete the existing content of the directory.
    *   Replace the content with the folders from the official
        [DFIQ repository](https://github.com/google/dfiq/tree/main/dfiq/data).
3. **Restart Timesketch:**
    * Restart your timesketch docker container.
    * This ensures that the new DFIQ data is loaded and recognized by the system.

## Verification

After completing these steps, you should see the DFIQ element loaded on your
sketches in the top.

If the data is loaded correctly, you will find new questions and approaches
available to be used.
