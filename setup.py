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
"""Setup setuptools."""

from setuptools import find_packages
from setuptools import setup


setup(
    name=u'Timesketch',
    version=u'15.02-dev',
    long_description=__doc__,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    scripts=[u'tsctl'],
    install_requires=frozenset([
        u'Flask',
        u'Flask-Login',
        u'Flask-script',
        u'Flask-SQLAlchemy',
        u'Flask-Bcrypt',
        u'Flask-RESTful',
        u'Flask-WTF',
        u'Flask-Testing',
        u'SQLAlchemy ==0.9.8',
        u'celery',
        u'redis',
        u'blinker',
        u'elasticsearch',
        u'nose',
        u'mock',
        u'pylint',
        u'coverage',
    ])
)
