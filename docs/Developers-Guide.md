### Developers guide

It is recommended to develop Timesketch using a docker container. Refer to [Docker Readme](../docker/dev/README.md) for details on how to bring up the development container.

Note: Exclamation mark `!` denotes commands that should run in the docker container shell, dollar sign `$` denotes commands to run in your local shell.

#### Frontend development

First we need to get an interactive shell to the container to install the frontend modules:
```
$ docker exec -it $CONTAINER_ID bash
```
Then inside the container shell go to the Timesketch frontend directory. 
```
! cd /usr/local/src/timesketch/timesketch/frontend
```
Note that this directory in the container is mounted as volume from your local repo and mirrors changes to your local repo.

Install node dependencies
```
! npm install
```
This will create `node_modules/` folder from `package.json` in the frontend directory.
```
! yarn install
```

#### Running tests and linters

The main entry point is `run_tests.py` in Timesketch root. Please note that for testing 
and linting python/frontend code in your local environment you need respectively python/
frontend dependencies installed.

For more information:
```
! run_tests.py --help
```
To run frontend tests in watch mode, cd to `frontend` directory and use
```
! yarn run test --watch
```
To run TSLint in watch mode, use
```
! yarn run lint --watch
```

#### Building Timesketch frontend

To build frontend files and put bundles in `timesketch/static/dist/`, use
```
! yarn run build
```
To watch for changes in code and rebuild automatically, use
```
! yarn run build --watch
```
This is what you would normally use when making changes to the frontend.
Changes are not instantaneous, it takes a couple of seconds to rebuild. It's best to
keep this interactive shell to your container running so you can monitor the re-build.

Don't forget to refresh page if your browser doesn't automatically load the changes.

#### Packaging

Before pushing package to PyPI, make sure you build the frontend before.

#### Local development

You may work on the frontend for your local environment for integration with your IDE or other reasons. This is not recommended however as it may cause clashes with your installed NodeJS.

Add Node.js 8.x repo
```
$ curl -sS https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add -
$ echo "deb https://deb.nodesource.com/node_8.x $(lsb_release -s -c) main"  | sudo tee /etc/apt/sources.list.d/nodesource.list
```
Add Yarn repo
```
$ curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
$ echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list
```
Install Node.js and Yarn
```
$ apt-get update && apt-get install nodejs yarn
```
After that you would run the same steps as with docker container to install frontend 
dependencies and build/test.