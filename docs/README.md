# Documentation

This is the place for user facing documentation. This is the source for the public site https://timesketch.org/

## Adding/edit docs

We are using a site generation tool called mkdocs. It is fully automated using GH actions.
To update or add new content you edit the files under this directory (/docs/). When the code is merged to the master branch it will automatically be build and deployed.

## Preview changes locally before opening a PR

In your development container navigate to the root directory of the repo:

```
cd /usr/local/src/timesketch/
```

Install mkdocs in your container:

```
pip3 install mkdocs mkdocs-material mkdocs-redirects
```

Start the preview webserver:

```
mkdocs serve
```

Access your generated docs at http://127.0.0.1:8000/
