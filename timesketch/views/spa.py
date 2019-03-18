# Copyright 2019 Google Inc. All rights reserved.
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
"""This module implements HTTP request handler."""

from __future__ import unicode_literals

from flask import Blueprint
from flask import render_template
from flask_login import login_required

# Register flask blueprint
spa_views = Blueprint('spa_views', __name__)


@spa_views.route('/', defaults={'path': ''})
@spa_views.route('/<path:path>')
@login_required
# pylint: disable=unused-argument
def overview(path):
    """Generates the template.

    Returns:
        Template with context.
    """
    return render_template('index.html')
