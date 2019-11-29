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

from __future__ import unicode_literals

import glob
import os

from setuptools import find_packages
from setuptools import setup

try:  # for pip >= 10
    from pip._internal.download import PipSession
    from pip._internal.req import parse_requirements
except ImportError:  # for pip <= 9.0.3
    from pip.download import PipSession
    from pip.req import parse_requirements


timesketch_version = '20190609'

timesketch_description = (
    'Timesketch is a web based tool for collaborative forensic timeline '
    'analysis. Using sketches you and your collaborators can easily organize '
    'timelines and analyze them all at the same time.  Add meaning to '
    'your raw data with rich annotations, comments, tags and stars.')

setup(
    name='timesketch',
    version=timesketch_version,
    description='Digital forensic timeline analysis',
    long_description=timesketch_description,
    license='Apache License, Version 2.0',
    url='http://www.timesketch.org/',
    maintainer='Timesketch development team',
    maintainer_email='timesketch-dev@googlegroups.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    data_files=[
        ('share/timesketch', glob.glob(
            os.path.join('data', '*'), recursive=True)),
        ('share/doc/timesketch', [
            'AUTHORS', 'LICENSE', 'README.md']),
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={'console_scripts': ['tsctl=timesketch.tsctl:main']},
    install_requires=[str(req.req) for req in parse_requirements(
        'requirements.txt', session=PipSession(),
    )],
    tests_require=[str(req.req) for req in parse_requirements(
        'test_requirements.txt', session=PipSession(),
    )],
)
