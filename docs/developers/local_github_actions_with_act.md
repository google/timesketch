# How to Run GitHub Actions Locally with act

Running your GitHub Actions workflows locally before pushing your changes can save significant time and CI/CD resources. This guide explains how to use `act`, a tool that lets you run your workflows in a local Docker environment that mimics the GitHub Actions runners.

## Prerequisites

1.  **Docker:** You must have Docker installed, and the Docker daemon must be running.
2.  **`act`:** The `act` command-line tool.

## Installation

You can install `act` using its official installation script. Open a terminal and run the following command. You will be prompted for your password as it installs the binary into `/usr/local/bin/`.

```bash
curl -s https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

For other installation methods, please refer to the [official `act` documentation](https://github.com/nektos/act#installation).

## Running the Workflows

The most common use case is to simulate a `pull_request` event, which is what triggers the e2e tests.

### Listing and Running a Specific Job

1.  To see all jobs that would run for a pull request, navigate to the root of the Timesketch repository and run:
    ```bash
    act pull_request --list
    ```
    `act` will list all the jobs from the `.github/workflows/e2e_tests.yml` file.

2.  To run a **specific job** from the list, use the `-j` flag. This is the recommended approach as it consumes fewer resources.

    **Example:** To run the e2e test suite with stable Plaso and OpenSearch v2:
    ```bash
    act pull_request -j PyPi-plaso-stable-opensearch-v2 --container-options "-m 4g --privileged"
    ```

### Running All Jobs

To run all jobs for a given event (e.g., `pull_request`), simply run `act` without the `-j` flag.

**Warning:** This will run all 8 e2e test jobs in parallel, which is very resource-intensive (CPU, RAM, and disk space).

```bash
act pull_request --container-options "-m 4g --privileged"
```

## Important Considerations

### Resource Allocation
*   `--container-options "-m 4g --privileged"`: It is highly recommended to allocate at least 4GB of memory to the container to prevent memory-related failures (which can manifest as `exit code 137`). The `--privileged` flag grants extended permissions that can help avoid certain container runtime errors.

### Docker-in-Docker

The Timesketch e2e test workflow uses `docker compose` to set up its test environment. This means `act` will be running a Docker container, which in turn needs to run `docker compose`. This "Docker-in-Docker" scenario requires the `act` container to have access to your system's Docker daemon.
`act` typically handles this automatically by mounting the Docker socket (`/var/run/docker.sock`). If you encounter errors related to `docker` not being found, ensure your Docker setup is standard and the socket is accessible.

### File Permissions
If you encounter `permission denied` errors, particularly related to `metadata.json`, you may need to adjust the file's ownership on your host machine. You can do this by running:
```bash
sudo chown $(whoami) metadata.json
```

### Secrets

`act` does not have access to your repository's GitHub secrets. If a workflow depends on secrets, you can provide them locally by creating a `.secrets` file in the root of the repository and running `act` with the `--secret-file .secrets` flag. The e2e tests do not require any secrets.
### Controlling Log Verbosity
By default, `act` can produce very verbose output, logging every detail of the workflow execution. You can control this verbosity using the following flags:
*   **`--quiet`** (or **`-q`**): Disables the logging of output from individual steps, making the overall output less verbose. This is useful when you only care about the job's success or failure.

    **Example:** To run a specific job with quiet output:
    ```bash
    act pull_request -j PyPi-plaso-stable-opensearch-v2 --quiet
    ```

*   **`--verbose`** (or **`-v`**): Provides more detailed output for debugging purposes. Use this when you need to inspect the inner workings of an action or step.

    **Example:** To run a specific job with verbose output:
    ```bash
    act pull_request -j PyPi-plaso-stable-opensearch-v2 --verbose
    ```

**Note:** The exact path to the `act` executable may vary depending on your installation method. If the command is not in your shell's `PATH`, you may need to provide the full path to the executable.