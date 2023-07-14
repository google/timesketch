#!/bin/bash

CONTAINER_ID="$(docker container list -f name=timesketch-dev -q)"
frontend=${2:-"frontend"}

if [ $1 == "web" ]; then
  docker exec -it $CONTAINER_ID gunicorn --reload -b 0.0.0.0:5000 --log-level debug --capture-output --timeout 600 timesketch.wsgi:application
elif [ $1 == "celery" ]; then
  docker exec -it $CONTAINER_ID celery -A timesketch.lib.tasks worker --loglevel=info
elif [ $1 == "vue-install-deps" ]; then
  docker exec -it $CONTAINER_ID yarn install --cwd=/usr/local/src/timesketch/timesketch/$frontend
elif [ $1 == "vue-dev" ]; then
  docker exec -it $CONTAINER_ID yarn run --cwd=/usr/local/src/timesketch/timesketch/$frontend serve
elif [ $1 == "vue-build" ]; then
  docker exec -it $CONTAINER_ID yarn run --cwd=/usr/local/src/timesketch/timesketch/$frontend build
elif [ $1 == "test" ]; then
  docker exec -w /usr/local/src/timesketch -it $CONTAINER_ID python3 run_tests.py --coverage
elif [ $1 == "shell" ]; then
  docker exec -it $CONTAINER_ID /bin/bash
elif [ $1 == "logs" ]; then
  docker logs -f $CONTAINER_ID
elif [ $1 == "build_api_cli" ]; then
    docker exec -w '/usr/local/src/timesketch/cli_client/python' -it $CONTAINER_ID python3 setup.py build
    docker exec -w '/usr/local/src/timesketch/cli_client/python' -it $CONTAINER_ID python3 setup.py install
    docker exec -w '/usr/local/src/timesketch/api_client/python' -it $CONTAINER_ID python3 setup.py build
    docker exec -w '/usr/local/src/timesketch/api_client/python' -it $CONTAINER_ID python3 setup.py install
fi
