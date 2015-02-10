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
"""This module implements HTTP request handler."""

from flask import Blueprint
from flask import render_template
from flask import redirect
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from sqlalchemy import not_

from timesketch.models.sketch import Sketch
from timesketch.lib.forms import HiddenNameDescriptionForm
from timesketch.models import db_session


# Register flask blueprint
home_views = Blueprint('home_views', __name__)


@home_views.route('/', methods=['GET', 'POST'])
@home_views.route('/sketch/', methods=['GET', 'POST'])
@login_required
def home():
    """Generates the home page view template.

    Returns:
        Template with context.
    """
    form = HiddenNameDescriptionForm()
    sketches = Sketch.all_with_acl().filter(
        not_(Sketch.Status.status == 'deleted'),
        Sketch.Status.parent).order_by(Sketch.updated_at.desc())
    query_filter = request.args.get('filter', '')
    query = request.args.get('q', '')

    if query_filter:
        if query_filter == 'user':
            sketches = sketches.filter(Sketch.user == current_user)
        elif query_filter == 'shared':
            sketches = sketches.filter(not_(Sketch.user == current_user))

    # TODO: Figure out a better way to handle this.
    if query:
        if query.startswith('*'):
            query = ''
        else:
            sketches = sketches.filter(Sketch.name.contains(query)).limit(100)

    # Handle form for creating a new sketch.
    if form.validate_on_submit():
        sketch = Sketch(
            name=form.name.data, description=form.description.data,
            user=current_user)
        sketch.status.append(sketch.Status(user=None, status='new'))
        # Give the requesting user permissions on the new sketch.
        sketch.grant_permission(current_user, 'read')
        sketch.grant_permission(current_user, 'write')
        sketch.grant_permission(current_user, 'delete')
        db_session.add(sketch)
        db_session.commit()
        return redirect(url_for('sketch_views.overview', sketch_id=sketch.id))

    return render_template(
        'home/home.html', sketches=sketches, form=form, query=query)
