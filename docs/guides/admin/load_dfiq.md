---
hide:
  - footer
---
# Loading DFIQ Template Data

This guide explains how to load DFIQ (Digital Forensics Investigative Questions) template data into Timesketch. DFIQ data provides a structured way to ask questions and create approaches for digital forensic investigations.

## Prerequisites

Before loading DFIQ data, ensure that:

1.  **DFIQ is enabled:** In your `timesketch.conf` file, the `DFIQ_ENABLED` value must be set to `True`. This setting enables the DFIQ features within Timesketch. You can find the configuration file here: [https://github.com/google/timesketch/blob/master/data/timesketch.conf#L345](https://github.com/google/timesketch/blob/master/data/timesketch.conf#L345).
2.  **DFIQ data is available:** Ensure that the DFIQ data is present in the correct directory within the Timesketch installation.

## Steps

Follow these steps to load the DFIQ template data:

1.  **Enable DFIQ:**
    *   Open your `timesketch.conf` file.
    *   Locate the `DFIQ_ENABLED` setting.
    *   Set the value to `True`.
2.  **Replace DFIQ folders:**
    *   Navigate to the Timesketch `data/dfiq` directory: [https://github.com/google/timesketch/tree/master/data/dfiq](https://github.com/google/timesketch/tree/master/data/dfiq).
    *   Delete the existing content of the directory.
    *   Replace the content with the folders from the DFIQ repository: [https://github.com/google/dfiq/tree/main/dfiq/data](https://github.com/google/dfiq/tree/main/dfiq/data).
3. **Restart Timesketch:**
    * Restart your docker timesketch container.
    * This ensures that the new DFIQ data is loaded and recognized by the system.

## Verification

After completing these steps, you can verify the successful loading of DFIQ data by:

*   Exploring the DFIQ features within the Timesketch UI.
* Using DFIQ in a sketch.
* Using the scenarios section of Timesketch.

If the data is loaded correctly, you will find new questions, approaches and facets available to be used.

## Additional Resources

*   Timesketch configuration file: [https://github.com/google/timesketch/blob/master/data/timesketch.conf#L345](https://github.com/google/timesketch/blob/master/data/timesketch.conf#L345)
*   DFIQ repository: [https://github.com/google/dfiq/tree/main/dfiq/data](https://github.com/google/dfiq/tree/main/dfiq/data)
* Timesketch DFIQ directory: [https://github.com/google/timesketch/tree/master/data/dfiq](https://github.com/google/timesketch/tree/master/data/dfiq)

---
*Use code with caution.*

This guide explains how to load DFIQ (Digital Forensics Intelligence Quotient) template data into Timesketch. DFIQ data provides a structured way to ask questions and create approaches for digital forensic investigations.

## Prerequisites

Before loading DFIQ data, ensure that:

1.  **DFIQ is enabled:** In your `timesketch.conf` file, the `DFIQ_ENABLED` value must be set to `True`. This setting enables the DFIQ features within Timesketch. You can find the configuration file here: [https://github.com/google/timesketch/blob/master/data/timesketch.conf#L345](https://github.com/google/timesketch/blob/master/data/timesketch.conf#L345).
2.  **DFIQ data is available:** Ensure that the DFIQ data is present in the correct directory within the Timesketch installation.

## Steps

Follow these steps to load the DFIQ template data:

1.  **Enable DFIQ:**
    *   Open your `timesketch.conf` file.
    *   Locate the `DFIQ_ENABLED` setting.
    *   Set the value to `True`.
2.  **Replace DFIQ folders:**
    *   Navigate to the Timesketch `data/dfiq` directory: [https://github.com/google/timesketch/tree/master/data/dfiq](https://github.com/google/timesketch/tree/master/data/dfiq).
    *   Delete the existing content of the directory.
    *   Replace the content with the folders from the DFIQ repository: [https://github.com/google/dfiq/tree/main/dfiq/data](https://github.com/google/dfiq/tree/main/dfiq/data).
3. **Restart Timesketch:**
    * Restart your docker timesketch container.
    * This ensures that the new DFIQ data is loaded and recognized by the system.

## Verification

After completing these steps, you can verify the successful loading of DFIQ data by:

*   Exploring the DFIQ features within the Timesketch UI.
* Using DFIQ in a sketch.
* Using the scenarios section of Timesketch.

If the data is loaded correctly, you will find new questions, approaches and facets available to be used.

## Additional Resources

*   Timesketch configuration file: [https://github.com/google/timesketch/blob/master/data/timesketch.conf#L345](https://github.com/google/timesketch/blob/master/data/timesketch.conf#L345)
*   DFIQ repository: [https://github.com/google/dfiq/tree/main/dfiq/data](https://github.com/google/dfiq/tree/main/dfiq/data)
* Timesketch DFIQ directory: [https://github.com/google/timesketch/tree/master/data/dfiq](https://github.com/google/timesketch/tree/master/data/dfiq)

---
*Use code with caution.*
