#!/usr/bin/env python
# Copyright 2017, Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from setuptools import setup, Extension

bindings = Extension(
    'pycypher.bindings',
    sources=[
        'pycypher/bindings.c',
        'pycypher/node_types.c',
        'pycypher/operators.c',
        'pycypher/props.c',
        'pycypher/extract_props.c',
        'pycypher/parser.c',
    ],
    libraries=['cypher-parser'],
)

description = u"""
Python bindings for libcypher-parser that provide access to parsed AST.
""".strip()

setup(
    name=u'pycypher',
    version='0.1.0',
    description=description,
    long_description=description,
    license='Apache License 2.0',
    url=u'https://github.com/google/timesketch/tree/master/contrib/libcypher-python',
    maintainer=u'Timesketch development team',
    maintainer_email=u'timesketch-dev@googlegroups.com',
    classifiers=[
        u'Development Status :: 1 - Planning',
        u'Intended Audience :: Developers',
        u'Programming Language :: Python',
        u'Programming Language :: Python :: 2',
        u'Programming Language :: C',
        u'Topic :: Software Development :: Libraries',
    ],
    ext_modules=[bindings],
    packages=['pycypher'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[],
)
