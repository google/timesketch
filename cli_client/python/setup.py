#!/usr/bin/env python
# Copyright 2021 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This is the setup file for the Timesketch CLI client."""

import os

from setuptools import find_packages
from setuptools import setup


def get_version():
    """Extracts the version from timesketch_cli_client/version.py.

    This is done manually to avoid importing the module during installation,
    which can lead to ModuleNotFoundError in isolated build environments.
    """
    version_file = os.path.join("timesketch_cli_client", "version.py")
    with open(version_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("__version__"):
                return line.split("=")[1].strip().strip("\"'")
    return "unknown"


setup(
    name="timesketch-cli-client",
    version=get_version(),
    description="Timesketch CLI client",
    license="Apache License, Version 2.0",
    url="http://www.timesketch.org/",
    maintainer="Timesketch development team",
    maintainer_email="timesketch-dev@googlegroups.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={"console_scripts": ["timesketch = timesketch_cli_client.cli:cli"]},
    install_requires=frozenset(
        [
            "click",
            "tabulate",
            "pandas",
            "timesketch-api-client",
            "timesketch-import-client",
        ]
    ),
)
