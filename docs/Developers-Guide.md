### Developers guide

#### Python dependencies
We use pip-tools and virtualenv for development. Pip-tools must be installed
inside a virtualenv, installing it system-wide will cause issues.
If you want to add a new python dependency, please add it to `requirements.in`
and then run `pip-compile` to pin it's version in `requirements.txt`.
Use `pip-sync` instead of `pip install -r requirements.txt` when possible.
Use `pip-compile --upgrade` to keep dependencies up to date.

#### Frontend dependencies
Add Node.js 8.x repo

    $ curl -sS https://deb.nodesource.com/gpgkey/nodesource.gpg.key | sudo apt-key add -
    $ echo "deb https://deb.nodesource.com/node_8.x $(lsb_release -s -c) main"  | sudo tee /etc/apt/sources.list.d/nodesource.list

Add Yarn repo

    $ curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
    $ echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list

Install Node.js and Yarn

    $ apt-get update && apt-get install nodejs yarn

Cd to timesketch repository root (folder that contains `package.json`)
and install Node.js packages (this will create `node_modules/` folder in the
current directory and install packages from `package.json` there)

    $ yarn install

#### Running tests and linters
The main entry point is `run_tests.py`. Please note that for testing and
linting python/frontend code you need respectively python/frontend dependencies
installed.

For more information:

    $ run_tests.py --help

To run frontend tests in watch mode, use

    $ yarn run test:watch

To run TSLint in watch mode, use

    $ yarn run lint:watch

#### Building Timesketch frontend
To build frontend files and put bundles in `timesketch/static/dist/`, use

    $ yarn run build

To watch for changes in code and rebuild automatically, use

    $ yarn run build:watch

#### Packaging
Before pushing package to PyPI, make sure you build the frontend before.
