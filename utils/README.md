# utils

This folder contains tools and utils used and maintained by the Timesketch-dev team.

## tsdev.sh

This Bash script, `tsdev.sh`, provides a command-line interface for interacting with a Timesketch development environment within a Docker container. It offers a variety of commands to manage the environment, including building API and CLI clients, starting a Celery worker, accessing container logs, executing tests, and managing the Vue.js frontend. The script checks for root access and Docker to ensure the environment is set up correctly. It then identifies the Timesketch development container and executes the specified command within that container. This script simplifies common development tasks, such as building, testing, and running the Timesketch application.

## update_release.sh

Script that makes changes in preparation of a new release, such as updating the version and documentation.