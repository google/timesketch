# Performance Monitoring

Timesketch includes a built-in performance profiler to help diagnose and troubleshoot performance issues. When enabled, it captures detailed profiling data for every HTTP request to the backend and saves it for later analysis.

## Enabling the Profiler

To enable the performance profiler, you need to edit your `timesketch.conf` file and set the `ENABLE_PROFILING` configuration option to `True`.

1.  **Locate your configuration file:** This is typically at `/etc/timesketch/timesketch.conf`.
2.  **Enable profiling:** Find the `ENABLE_PROFILING` setting and change it to `True`.

    ```ini
    # In /etc/timesketch/timesketch.conf
    ENABLE_PROFILING = True
    ```

3.  **Restart the Timesketch server:** For the change to take effect, you must restart the application server.

Once enabled, the profiler will start writing `.prof` files for each request into a `profiles/` directory. The location of this directory depends on your deployment:

*   **Local Development (timesketch-dev container):** `/usr/local/src/timesketch/profiles/`
*   **Release Containers:** `/var/log/timesketch/profiles/`

## Analyzing Performance Profiles with `pstats`

If you have enabled performance profiling (by setting `ENABLE_PROFILING = True` in `timesketch.conf`), the application will generate `.prof` files in the appropriate `profiles/` directory. These files contain detailed performance statistics for each request.

You can analyze these files using Python's built-in `pstats` module, which provides a command-line browser for profiling statistics.

1.  **Navigate to the profiles directory:**

    ```bash
    # For local development
    cd /usr/local/src/timesketch/profiles/

    # For release containers
    # cd /var/log/timesketch/profiles/
    ```

2.  **Open a `.prof` file with `pstats`:**

    ```bash
    python3 -m pstats <filename>.prof
    ```

    Replace `<filename>.prof` with the actual name of one of the profiling files (e.g., `GET.api.v1.sketches.153ms.1762433265.prof`).

3.  **Use the `pstats` browser:**

    Once inside the `pstats` browser, you can use various commands to inspect the data:

    *   `sort time`: Sorts the output by internal time spent in each function.
    *   `stats <n>`: Displays the top `n` entries (e.g., `stats 20` for the top 20).
    *   `callers <function_name>`: Shows who called a specific function.
    *   `callees <function_name>`: Shows which functions a specific function called.
    *   `help`: Displays a list of all available commands.
    *   `quit`: Exits the `pstats` browser.

    Example session:

    ```
    Welcome to the profile statistics browser.
    GET.api.v1.sketches.153ms.1762433265.prof%
    (pstats) sort time
    (pstats) stats 10
    # ... (output of top 10 functions by time)
    (pstats) quit
    ```


## Analyzing Profiling Data with SnakeViz

The `.prof` files can be analyzed with `snakeviz`, a browser-based graphical viewer for Python profiling data.

### 1. Install SnakeViz on the Server

First, install `snakeviz` on your Timesketch server using pip:

```bash
pip install snakeviz
```

### 2. Run the SnakeViz Web Server

Navigate to the directory where the profiling data is stored and start the `snakeviz` server. It will bind to `localhost` by default, which is ideal for use with SSH port forwarding.

```bash
# For local development
cd /usr/local/src/timesketch/profiles/

# For release containers
# cd /var/log/timesketch/profiles/

# Start snakeviz, pointing it to all .prof files
snakeviz . -s
```

SnakeViz will start a web server, typically on `http://127.0.0.1:8080`.

### 3. Access the SnakeViz UI with SSH Port Forwarding

To access the `snakeviz` web interface from your local machine, you can use SSH to forward the server's port to your local machine.

Open a new terminal on your **local machine** and run the following command, replacing `USER` and `TIMESKETCH_SERVER_IP` with your credentials:

```bash
ssh -L 8080:localhost:8080 USER@TIMESKETCH_SERVER_IP
```

This command forwards your local port `8080` to the remote server's port `8080`.

Now, open a web browser on your local machine and navigate to:

[http://localhost:8080/snakeviz](http://localhost:8080/snakeviz)

You can now interact with the `snakeviz` UI to analyze the performance data for your Timesketch application.
