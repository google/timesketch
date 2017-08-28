### Developers guide

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
