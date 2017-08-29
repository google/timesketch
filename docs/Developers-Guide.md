### Developers guide

#### Python dependencies
We use pip-tools and virtualenv for development. Pip-tools must be installed
inside a virtualenv, installing it system-wide will cause issues.
If you want to add a new python dependency, please add it to `requirements.in`
and then run pip-compile to pin it's version in `requirements.txt`.
Use `pip-sync` instead of `pip install -r requirements.txt` when possible.
Use `pip-compile --upgrade` to keep dependencies up to date.

#### Installing Node.js and Yarn
Add Node.js 8.x repo

    $ curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -

Add Yarn repo

    $ curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | sudo apt-key add -
    $ echo "deb https://dl.yarnpkg.com/debian/ stable main" | sudo tee /etc/apt/sources.list.d/yarn.list

Install

    $ apt-get update && apt-get install nodejs yarn

#### Building Timesketch frontend
First, cd to timesketch repository root (folder that contains package.json).

Install nodejs packages

    $ yarn install

Build frontend files

    $ yarn run build

#### Packaging
Before pushing package to PyPI, make sure you build the frontend before.
