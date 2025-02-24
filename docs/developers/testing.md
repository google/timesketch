---
hide:
  - footer
---
## Running tests

The main entry point is `run_tests.py` in Timesketch root. Please note that for testing
and linting python/frontend code in your local environment you need respectively python/
frontend dependencies installed.

For more information:

```python
! run_tests.py --help
```

To run frontend tests in watch mode, cd to `frontend` directory and use

```bash
! yarn run test --watch
```

To run TSLint in watch mode, use

```bash
! yarn run lint --watch
```

To run a single test (there are multiple ways to do it), open a shell in the docker container:

```shell
docker exec -it timesketch /bin/bash
```

Switch to:

```shell
! cd /usr/local/src/timesketch
```

And execute the single test

```shell
! python3 -m pytest timesketch/lib/emojis_test.py -v
```

Or all in one:

```bash
sudo docker exec -it timesketch python3 -m pytest /usr/local/src/timesketch/timesketch/lib/emojis_test.py -v
```

## Writing unittests

It is recommended to write unittests as much as possible.

Test files in Timesketch have the naming convention `_test.py` and are stored next to the files they test. E.g. a test file for `/timesketch/lib/emojis.py` is stored as `/timesketch/lib/emojis_test.py`

The unittests for the api client can use `mock` to emulate responses from the server. The mocked answers are written in: `api_client/python/timesketch_api_client/test_lib.py`.

To introduce a new API endpoint to be tested, the endpoint needs to be registered in the `url_router` section in `/api_client/python/timesketch_api_client/test_lib.py` and the response needs to be defined in the same file.

## Debugging tests

To debug tests, simply add the following at the point of interest:

```python
breakpoint()
```

And then within the docker container execute

```shell
! python3 -m pytest /usr/local/src/timesketch/timesketch/lib/emojis_test.py -s -pdb
```

## end2end tests

End2end (e2e) tests are run on Github with every commit. Those tests will setup and run a full Timesketch instance, with the ability to import data and perform actions with it.
To run the e2e-tests locally execute to setup the e2e docker images and run them:

```bash
sh end_to_end_tests/tools/run_end_to_end_tests.sh
```

The tests are stored in:

```shell
end_to_end_tests/*.py
```

And the sample data (currently a plaso file and a csv) is stored in:

```shell
end_to_end_tests/test_data/
```

## Writing end2end tests

While writing end2end tests one approach to make it easier to develop these e2e tests is to create a simlink to the source files, in order for the changes to the files being reflected in the container. Another way is to mount the Timesketch source code from `/usr/local/src/timesketch/` to `/usr/local/lib/python3.8/dist-packages/`

The following example is for changing / adding tests to `client_test.py`

```shell
$ export CONTAINER_ID="$(sudo -E docker container list -f name=e2e_timesketch -q)"
$ docker exec -it timesketch /bin/bash
! rm /usr/local/lib/python3.10/dist-packages/end_to_end_tests/client_test.py
! ln -s /usr/local/src/timesketch/end_to_end_tests/client_test.py /usr/local/lib/python3.10/dist-packages/end_to_end_tests/client_test.py
```

From now on you can edit the `client_test.py` file outside of the docker instance and run it again with

```shell
! python3 /usr/local/src/timesketch/end_to_end_tests/tools/run_in_container.py
```

or run the following outside of the container:

```bash
sudo docker exec -it timesketch python3 /usr/local/src/timesketch/end_to_end_tests/tools/run_in_container.py
```

## Linting / Code format

The project has a certain code style / code format across the project. The main settings are stored in `.pylintrc`. When creating a Pull Request, one of the things automation checks is correct linting. Pull Request with failed pylint checks can not be accepted.

To check linting on a single file, run the following in your docker container:

```bash
! apt-get update
! apt-get install pylint==2.6.0
! pylint /usr/local/src/timesketch/timesketch/  --rcfile .pylintrc -v
```
