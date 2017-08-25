# Docker

Timesketch has support for Docker. This is a convenient way of getting up and running.

### Install Docker
Follow the official instructions [here](https://www.docker.com/community-edition)

### Clone Timesketch

```shell
git clone https://github.com/google/timesketch.git
cd timesketch
```

### Build Timesketch frontend
Follow steps "Installing Node.js and Yarn" and "Building Timesketch frontend" from [developers guide](../docs/Developers-Guide.md).

### Build and Start Containers

```shell
cd docker
docker-compose up
```

### Access Timesketch
* Retrieve the randomly generated password from startup logs: `TIMESKETCH_PASSWORD set randomly to: xxx`
* Go to: http://127.0.0.1:5000/
* Login with username: admin and the retrieved random password

### How to test your installation
1. You can now create your first sketch by pressing the green button on the middle of the page
2. Add the test timeline under the [Timeline](http://127.0.0.1:5000/sketch/1/timelines/) tab in your new sketch
3. Go to http://127.0.0.1:5000/explore/ and have fun exploring!
