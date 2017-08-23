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
from flask import current_app
from flask import render_template
from flask import redirect
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from sqlalchemy import not_

from timesketch.models.sketch import Sketch
from timesketch.lib.forms import HiddenNameDescriptionForm
from timesketch.models import db_session

# Register flask blueprint
home_views = Blueprint(u'home_views', __name__)


@home_views.route(u'/', methods=[u'GET', u'POST'])
@home_views.route(u'/sketch/', methods=[u'GET', u'POST'])
@login_required
def home():
    """Generates the home page view template.

    Returns:
        Template with context.
    """
    form = HiddenNameDescriptionForm()
    sketches = Sketch.all_with_acl().filter(
        not_(Sketch.Status.status == u'deleted'),
        Sketch.Status.parent).order_by(Sketch.updated_at.desc())
    # Only render upload button if it is configured.
    upload_enabled = current_app.config[u'UPLOAD_ENABLED']

    # Handle form for creating a new sketch.
    if form.validate_on_submit():
        sketch = Sketch(
            name=form.name.data,
            description=form.description.data,
            user=current_user)
        sketch.status.append(sketch.Status(user=None, status=u'new'))
        # Give the requesting user permissions on the new sketch.
        sketch.grant_permission(permission=u'read', user=current_user)
        sketch.grant_permission(permission=u'write', user=current_user)
        sketch.grant_permission(permission=u'delete', user=current_user)
        db_session.add(sketch)
        db_session.commit()
        return redirect(url_for(u'sketch_views.overview', sketch_id=sketch.id))

    return render_template(
        u'home/home.html',
        sketches=sketches,
        form=form,
        upload_enabled=upload_enabled)
