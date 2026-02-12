# Development with Tilt

Tilt is an orchestration tool that provides a faster and more integrated development experience for Timesketch. It replaces the manual workflow of running multiple `tsdev.sh` commands.

## Why use Tilt?

*   **Unified Dashboard**: See the status and logs of the API, Celery Worker, Vite Frontend, and all infrastructure (OpenSearch, Postgres, etc.) in a single UI at `http://localhost:10350`.
*   **Live Updates**:
    *   **Docker Volumes**: Handle the instant synchronization of files from your host to the container filesystem.
    *   **Tilt Monitoring**: Tracks the `deps` defined in the `contrib/Tiltfile`. When a file changes, Tilt ensures the corresponding resource reflects that update in the dashboard logs.
    *   **Automatic Restarts**: Backend services (Gunicorn/Celery) are configured to auto-reload when the filesystem changes. This includes:
        *   **API Changes**: Modifying routes or views restarts the web server.
        *   **Background Tasks**: Modifying `timesketch/lib/tasks.py` or any file in `timesketch/lib/analyzers/` will cause Tilt to restart the Celery worker (`ts-worker`), ensuring new tasks use the updated logic.
        *   **Configuration**: If you modify core configuration files (like `timesketch.conf`), Tilt will proactively restart the managed processes to ensure the new settings are applied.
*   **Isolated E2E Testing**: Spin up and run end-to-end tests with a single click.
    *   **Data Isolation**: These tests use curated datasets from `end_to_end_tests/test_data/` and are completely isolated from your development data to ensure reproducible results and prevent accidental data loss.
    *   **Code Installation**: Unlike the "Live Updates" environment, the E2E environment installs the code once during container creation. If you modify your code, you must stop the E2E environment and restart it for changes to take effect.

---

## Getting Started

### 1. Prerequisites
Ensure you have the following installed on your host machine:
*   [Docker](https://docs.docker.com/get-docker/)
*   [Tilt](https://docs.tilt.dev/install.html)

**Note**: Although Tilt documentation often mentions Kubernetes tools like `kubectl` or `ctlptl`, they are **not required** for Timesketch development as we run everything directly in Docker.

### 2. Launching the Environment
From the project root, simply run:
```bash
tilt up -f contrib/Tiltfile
```

By default, Tilt will ask you how you want to interact with it:
*   **Browser (Recommended)**: Opens the unified dashboard at `http://localhost:10350`.
*   **Stream logs**: Shows logs directly in your terminal.

#### Remote Development (SSH)
If you are developing on a remote machine, you can access the Tilt dashboard by forwarding port `10350`. When connecting via SSH, use:
```bash
ssh -L 10350:localhost:10350 user@remote-host
```
Then, you can visit `http://localhost:10350` in your local browser. You may also want to forward ports `5000` (Web UI) and `5001` (Vite Frontend) for a complete experience.

## How to use the Dashboard

The dashboard is organized into several rows:

### Managed Services (Always Running)
*   **ts-web**: The Timesketch Gunicorn server. It serves both the **REST API** and the **stable frontend** (Vue 2 / `frontend-ng`). Automatically reloads on `.py` changes.
*   **ts-worker**: The Celery worker for background tasks.
*   **ts-frontend-v3**: The Vue 3 development server. This is used for developing the **new experimental UI**. Automatically reloads on UI changes.
*   **infra/**: Group containing OpenSearch, Postgres, Redis, and Prometheus.

### End-to-End Testing
1.  Click **e2e-environment** to spin up the independent E2E Docker cluster.
2.  Click **run-e2e-tests** to execute the tests.
3.  Click **stop-e2e** when finished to tear down the environment and free up resources.

### Utilities
These tools are configured with `auto_init=False`, meaning they **do not run on startup**. They are manually triggered by clicking the "Play" button in the Tilt UI, keeping your initial environment launch fast.

*   **run-unit-tests**: Executes the Python backend unit tests via `run_tests.py`.
*   **run-pylint**: Runs Pylint only against Python files that have changed relative to the `origin/master` branch. This matches the behavior of the GitHub Actions linter.
*   **run-pylint-all**: Runs Pylint against the entire project (backend and clients). Use this to check for global issues or perform project-wide cleanup.
*   **run-black**: Runs the Black formatter in `--check` mode to verify code style.
*   **run-black-fix**: Runs the Black formatter and **automatically applies** formatting changes to your code.
*   **build-api-cli**: Installs the API, CLI, and Importer clients in **editable mode** (`-e`) inside the container. You only need to run this **once**. After that, any code changes you make in the client directories will be picked up by the container automatically.
*   **run-frontend-v3-tests**: Runs the test suite for the new Vue 3 experimental frontend.

---

## Configuration

Tilt monitors the configuration file located in `data/timesketch.conf`. 

When you modify this file, Tilt automatically triggers a configuration refresh inside the container (re-applying environment-specific settings) and restarts the backend services. This ensures your changes are applied immediately without requiring a manual container restart.

To add items to the Dashboard or modify tracked dependencies, edit `contrib/Tiltfile`.
## Troubleshooting

*   **Port 10350 in use**: Ensure no other Tilt processes are running (`killall tilt`).
*   **Port 5001 in use**: The Vue 3 frontend is configured to strictly use port 5001 to match Docker's port mapping. If this port is in use, the service will fail to start. Ensure no other Vite processes or services are using port 5001. Run `docker exec -it timesketch-dev pkill -f vite` to clear any orphaned processes.
*   **Port 5000 in use**: If the API fails to start because the address is in use, it means a background process (likely from a previous `docker-compose up`) is still holding the port. Run `docker exec -it timesketch-dev pkill -9 gunicorn` to clear it.
