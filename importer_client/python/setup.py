#!/usr/bin/env python
# Copyright 2017 Google Inc. All rights reserved.
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
"""This is the setup file for the project."""
from __future__ import unicode_literals

import os
import glob

from setuptools import find_packages
from setuptools import setup

from timesketch_import_client import version

setup(
    name='timesketch-import-client',
    version=version.get_version(),
    description='Timesketch Import Client',
    license='Apache License, Version 2.0',
    url='http://www.timesketch.org/',
    maintainer='Timesketch development team',
    maintainer_email='timesketch-dev@googlegroups.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    data_files=[
        ('data', glob.glob(
            os.path.join('timesketch_import_client', 'data', '*.yaml'))),
    ],
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'timesketch_importer = tools.timesketch_importer:main']},
    install_requires=frozenset([
        'pandas',
        'xlrd',
        'timesketch-api-client',
        'pyyaml',
    ]),
    )
