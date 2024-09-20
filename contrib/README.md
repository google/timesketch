# Contrib

This folder contains various scripts, templates and pieces contributed from the community.

## Disclaimer

None of the content of this folder is maintained by the Timesketch-dev team.
Using it is at your own risk.

# Content

## deploy_timesketch.ps1

This PowerShell script automates the deployment of Timesketch on a system. It checks for existing Timesketch installations, Docker service, and Timesketch containers to prevent conflicts. The script sets up necessary directories, configures parameters, and downloads the required configuration files. It then modifies these files to establish connections with OpenSearch, Redis, and Postgres. Finally, it provides instructions on how to start Timesketch and create a user.

## deploy_timesketch.sh

This Bash script automates the deployment of Timesketch, a digital forensic timeline analysis tool. It checks for prerequisites like root access, Docker, and Docker Compose, then sets up necessary directories and fetches configuration files. The script configures Timesketch parameters, including connections to a PostgreSQL database, OpenSearch instance, and Redis. It can also start the Timesketch containers and guide the user to create a new Timesketch user.

## gcs_importer.py

This Python script facilitates the import of forensic timeline data from Google Cloud Storage (GCS) into Timesketch. It listens for messages on a Google Cloud Pub/Sub topic, automatically downloading and indexing Plaso files from GCS when Turbinia processes are completed. The script creates or uses existing Timesketch sketches and timelines to organize the imported data, enhancing the automation of forensic analysis workflows.

## timesketch-importer.sh

This Bash script automates importing forensic timeline data into Timesketch. It monitors a specified directory for new files with extensions `.plaso, .csv, or .jsonl`, commonly used for storing timeline data. When a new file is detected, it automatically imports the data into Timesketch using the `tsctl` command. This script simplifies the process of adding new data to Timesketch for analysis.

## nginx.conf

This Nginx configuration file sets up a reverse proxy for Timesketch, routing incoming HTTP requests to the appropriate backend servers. It defines two server blocks: one for the main Timesketch application (/) and another for the legacy interface (/legacy/).  The configuration includes settings for client maximum body size, proxy buffering, and request timeouts to optimize performance.  Additionally, it sets necessary headers to ensure proper communication between the proxy and the backend servers.    

## timesketch-importer.conf / timesketch-importer.service

This configuration file defines the settings for the Timesketch Importer script. It specifies the directory that the script should monitor for new Plaso, CSV, or JSONL files to import into Timesketch.

This systemd service file configures the Timesketch Importer script to run as a service. It defines the service description, start command, and restart behavior.  This allows the importer to run automatically in the background and restart if it fails, ensuring continuous monitoring and importing of forensic timeline data.