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
"""This module implements HTTP request handlers for the sketch views."""

from flask import abort
from flask import Blueprint
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from sqlalchemy import desc
from sqlalchemy import not_

from timesketch.models import db_session
from timesketch.lib.forms import AddTimelineForm
from timesketch.lib.forms import NameDescriptionForm
from timesketch.lib.forms import TimelineForm
from timesketch.lib.forms import TogglePublic
from timesketch.lib.forms import StatusForm
from timesketch.lib.forms import TrashForm
from timesketch.lib.forms import SaveViewForm
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import Timeline
from timesketch.models.sketch import View
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND


# Register flask blueprint
sketch_views = Blueprint(u'sketch_views', __name__)


@sketch_views.route(u'/sketch/<int:sketch_id>/', methods=[u'GET', u'POST'])
@login_required
def overview(sketch_id):
    """Generates the sketch overview template.

    Returns:
        Template with context.
    """
    sketch = Sketch.query.get_with_acl(sketch_id)
    sketch_form = NameDescriptionForm()
    permission_form = TogglePublic()
    status_form = StatusForm()
    trash_form = TrashForm()

    # Edit sketch form POST
    if sketch_form.validate_on_submit():
        if not sketch.has_permission(current_user, u'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        sketch.name = sketch_form.name.data
        sketch.description = sketch_form.description.data
        db_session.commit()
        return redirect(
            url_for(u'sketch_views.overview', sketch_id=sketch.id))

    # Toggle public/private form POST
    if permission_form.validate_on_submit():
        if not sketch.has_permission(current_user, u'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        if permission_form.permission.data == u'public':
            sketch.grant_permission(user=None, permission=u'read')
        else:
            sketch.revoke_permission(user=None, permission=u'read')
        db_session.commit()
        return redirect(
            url_for(u'sketch_views.overview', sketch_id=sketch.id))

    # Change status form POST
    if status_form.validate_on_submit():
        if not sketch.has_permission(current_user, u'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        sketch.set_status(status=status_form.status.data)
        return redirect(
            url_for(u'sketch_views.overview', sketch_id=sketch.id))

    # Trash form POST
    if trash_form.validate_on_submit():
        if not sketch.has_permission(current_user, u'delete'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        sketch.set_status(status=u'deleted')
        return redirect(
            url_for(u'home_views.home'))

    return render_template(
        u'sketch/overview.html', sketch=sketch, sketch_form=sketch_form,
        permission_form=permission_form, status_form=status_form,
        trash_form=trash_form)


@sketch_views.route(
    u'/sketch/<int:sketch_id>/explore/', methods=[u'GET', u'POST'])
@sketch_views.route(
    u'/sketch/<int:sketch_id>/explore/view/<int:view_id>/',
    methods=[u'GET', u'POST'])
@login_required
def explore(sketch_id, view_id=None):
    """Generates the sketch explore view template.

    Returns:
        Template with context.
    """
    sketch = Sketch.query.get_with_acl(sketch_id)
    if view_id:
        view = View.query.get(view_id)
    else:
        view = View.query.filter(
            View.user == current_user,
            View.name == u'',
            View.sketch_id == sketch_id).order_by(
                View.created_at.desc()).first()
    if not view:
        view = View(
            user=current_user, name=u'', sketch=sketch, query_string=u'',
            query_filter=u'{}')
        db_session.add(view)
        db_session.commit()
    sketch_timelines = u','.join(
        [t.searchindex.index_name for t in sketch.timelines])
    view_form = SaveViewForm()

    return render_template(
        u'sketch/explore.html', sketch=sketch, view=view,
        timelines=sketch_timelines, view_form=view_form)


@sketch_views.route(
    u'/sketch/<int:sketch_id>/timelines/', methods=[u'GET', u'POST'])
@login_required
def timelines(sketch_id):
    """Generates the sketch explore view template.

    Returns:
        Template with context.
    """
    sketch = Sketch.query.get_with_acl(sketch_id)
    searchindices_in_sketch = [t.searchindex.id for t in sketch.timelines]
    query = request.args.get(u'q', None)
    indices = SearchIndex.all_with_acl(current_user).order_by(
        desc(SearchIndex.created_at)).filter(
        not_(SearchIndex.id.in_(searchindices_in_sketch)))
    filtered = False

    if query:
        indices = indices.filter(SearchIndex.name.contains(query)).limit(500)
        filtered = True
    if not filtered:
        indices = indices.limit(20)

    # Setup the form
    form = AddTimelineForm()
    form.timelines.choices = set((i.id, i.name) for i in indices.all())

    # Create new timeline form POST
    if form.validate_on_submit():
        if not sketch.has_permission(current_user, u'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        for searchindex_id in form.timelines.data:
            searchindex = SearchIndex.query.get_with_acl(searchindex_id)
            if searchindex not in [t.searchindex for t in sketch.timelines]:
                _timeline = Timeline(
                    name=searchindex.name, description=searchindex.description,
                    sketch=sketch, user=current_user, searchindex=searchindex)
                db_session.add(_timeline)
                sketch.timelines.append(_timeline)
        db_session.commit()
        return redirect(url_for(u'sketch_views.overview', sketch_id=sketch.id))

    return render_template(
        u'sketch/timelines.html', sketch=sketch, form=form, filtered=filtered)


@sketch_views.route(
    u'/sketch/<int:sketch_id>/timelines/<int:timeline_id>/',
    methods=[u'GET', u'POST'])
@login_required
def timeline(sketch_id, timeline_id):
    """Generates the sketch timeline view template.

    Returns:
        Template with context.
    """
    timeline_form = TimelineForm()
    sketch = Sketch.query.get_with_acl(sketch_id)
    sketch_timeline = Timeline.query.filter(
        Timeline.id == timeline_id, Timeline.sketch == sketch).first()
    if not sketch_timeline:
        abort(HTTP_STATUS_CODE_NOT_FOUND)

    if timeline_form.validate_on_submit():
        if not sketch.has_permission(current_user, u'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        sketch_timeline.name = timeline_form.name.data
        sketch_timeline.description = timeline_form.description.data
        sketch_timeline.color = timeline_form.color.data
        db_session.add(sketch_timeline)
        db_session.commit()
        return redirect(
            url_for(u'sketch_views.timeline', sketch_id=sketch.id,
                    timeline_id=sketch_timeline.id))

    return render_template(
        u'sketch/timeline.html', sketch=sketch, timeline=sketch_timeline,
        timeline_form=timeline_form)


@sketch_views.route(u'/sketch/<int:sketch_id>/views/')
@login_required
def views(sketch_id):
    """Generates the sketch views template.

    Returns:
        Template with context.
    """
    sketch = Sketch.query.get_with_acl(sketch_id)
    return render_template(u'sketch/views.html', sketch=sketch)


@sketch_views.route(u'/sketch/<int:sketch_id>/explore/event/')
@sketch_views.route(
    u'/sketch/<int:sketch_id>/explore/view/<int:unused_view_id>/event/')
@login_required
def event(sketch_id, unused_view_id=None):
    """Generates the event template.

    Returns:
        Template with context.
    """
    sketch = Sketch.query.get_with_acl(sketch_id)
    return render_template(
        u'sketch/event.html', sketch=sketch)
