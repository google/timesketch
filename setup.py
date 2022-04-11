#!/usr/bin/env python
# Copyright 2015 Google Inc. All rights reserved.
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
"""This is the setup file for the project. The standard setup rules apply:

   python setup.py build
   sudo python setup.py install
"""

from __future__ import print_function
from __future__ import unicode_literals

import glob
import os
import sys

import pkg_resources

from setuptools import find_packages
from setuptools import setup

from timesketch import version


version_tuple = (sys.version_info[0], sys.version_info[1])
if version_tuple < (3, 6):
    print(
        (
            "Unsupported Python version: {0:s}, version 3.6 or higher " "required."
        ).format(sys.version)
    )
    sys.exit(1)


def parse_requirements_from_file(path):
    """Parses requirements from a requirements file.

    Args:
      path (str): path to the requirements file.

    Yields:
      str: package resource requirement.
    """
    with open(path, "r") as file_object:
        file_contents = file_object.read()
    for req in pkg_resources.parse_requirements(file_contents):
        try:
            requirement = str(req.req)
        except AttributeError:
            requirement = str(req)
        yield requirement


timesketch_description = (
    "Timesketch is a web based tool for collaborative forensic timeline "
    "analysis. Using sketches you and your collaborators can easily organize "
    "timelines and analyze them all at the same time.  Add meaning to "
    "your raw data with rich annotations, comments, tags and stars."
)

setup(
    name="timesketch",
    version=version.get_version(),
    description="Digital forensic timeline analysis",
    long_description=timesketch_description,
    license="Apache License, Version 2.0",
    url="http://www.timesketch.org/",
    maintainer="Timesketch development team",
    maintainer_email="timesketch-dev@googlegroups.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    data_files=[
        ("share/timesketch", glob.glob(os.path.join("data", "*.*"))),
        ("share/timesketch/linux", glob.glob(os.path.join("data", "linux", "*.*"))),
        ("share/doc/timesketch", ["AUTHORS", "LICENSE", "README.md"]),
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={"console_scripts": ["tsctl=timesketch.tsctl:cli"]},
    install_requires=parse_requirements_from_file("requirements.txt"),
    tests_require=parse_requirements_from_file("test_requirements.txt"),
)
