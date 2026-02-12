# Development with Tilt

Tilt is an orchestration tool that provides a faster and more integrated development experience for Timesketch. It replaces the manual workflow of running multiple `tsdev.sh` commands.

## Why use Tilt?

*   **Unified Dashboard**: See the status and logs of the API, Celery Worker, Vite Frontend, and all infrastructure (OpenSearch, Postgres, etc.) in a single UI at `http://localhost:10350`.
*   **Live Updates**: When you save a file, Tilt automatically syncs it into the container.
*   **Isolated E2E Testing**: Spin up and run end-to-end tests with a single click, completely isolated from your development data.

---

## Getting Started

### 1. Prerequisites
Ensure you have the following installed on your host machine:
*   [Docker](https://docs.docker.com/get-docker/)
*   [Tilt](https://docs.tilt.dev/install.html)

### 2. Launching the Environment
From the project root, simply run:
```bash
tilt up -f contrib/Tiltfile
```

## How to use the Dashboard

The dashboard is organized into several rows:

### Managed Services (Always Running)
*   **ts-web**: The Timesketch Gunicorn API server. Automatically reloads on `.py` changes.
*   **ts-worker**: The Celery worker for background tasks.
*   **ts-frontend-v3**: The Vue 3 development server. Automatically reloads on UI changes.
*   **infra/**: Group containing OpenSearch, Postgres, Redis, and Prometheus.

### End-to-End Testing
1.  Click **e2e-environment** to spin up the independent E2E Docker cluster.
2.  Click **run-e2e-tests** to execute the tests.
3.  Click **stop-e2e** when finished to tear down the environment and free up resources.

### Utilities
*   **run-unit-tests**: Runs the Python unit tests using `run_tests.py`.
*   **run-pylint**: Runs Pylint on the backend and client libraries.
*   **run-black**: Runs Black (check mode) to verify code formatting.

---

## Configuration

Tilt uses the configuration located in `data/timesketch.conf`. If you modify this file, Tilt will automatically restart the backend services to apply the new settings.
To add items to the Dashboard, modify the `contrib/Tiltfile`.

## Troubleshooting

*   **Port 10350 in use**: Ensure no other Tilt processes are running (`killall tilt`).
*   **Port 5000 in use**: If the API fails to start because the address is in use, it means a background process (likely from a previous `docker-compose up`) is still holding the port. Run `docker exec -it timesketch-dev pkill -9 gunicorn` to clear it.
