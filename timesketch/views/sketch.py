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

from __future__ import unicode_literals

import codecs
import csv
import json

import six
from six import StringIO

from flask import abort
from flask import Blueprint
from flask import current_app
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import current_user
from flask_login import login_required
from sqlalchemy import desc
from sqlalchemy import or_
from sqlalchemy import not_

from timesketch.models import db_session
from timesketch.lib.datastores.elastic import ElasticsearchDataStore
from timesketch.lib.definitions import DEFAULT_FIELDS
from timesketch.lib.definitions import HTTP_STATUS_CODE_FORBIDDEN
from timesketch.lib.definitions import HTTP_STATUS_CODE_NOT_FOUND
from timesketch.lib.forms import AddTimelineForm
from timesketch.lib.forms import NameDescriptionForm
from timesketch.lib.forms import TimelineForm
from timesketch.lib.forms import TogglePublic
from timesketch.lib.forms import StatusForm
from timesketch.lib.forms import TrashForm
from timesketch.lib.forms import TrashViewForm
from timesketch.lib.forms import SaveViewForm
from timesketch.models.sketch import Sketch
from timesketch.models.sketch import SearchIndex
from timesketch.models.sketch import SearchTemplate
from timesketch.models.sketch import Timeline
from timesketch.models.sketch import View
from timesketch.models.sketch import Story
from timesketch.models.user import Group
from timesketch.models.user import User


# Register flask blueprint
sketch_views = Blueprint('sketch_views', __name__)


@sketch_views.route('/sketch/<int:sketch_id>/', methods=['GET', 'POST'])
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
    upload_enabled = current_app.config['UPLOAD_ENABLED']
    graphs_enabled = current_app.config['GRAPH_BACKEND_ENABLED']

    # Dynamically set the forms select options.
    # pylint: disable=singleton-comparison
    permission_form.groups.choices = set(
        (g.id, g.name)
        for g in Group.query.filter(
            or_(Group.user == current_user, Group.user == None)))

    permission_form.remove_groups.choices = set((g.id, g.name)
                                                for g in sketch.groups)

    permission_form.remove_users.choices = set((u.id, u.username)
                                               for u in sketch.collaborators)

    # Edit sketch form POST
    if sketch_form.validate_on_submit():
        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        sketch.name = sketch_form.name.data
        sketch.description = sketch_form.description.data
        db_session.commit()
        return redirect(url_for('sketch_views.overview', sketch_id=sketch.id))

    # Toggle public/private form POST
    # TODO: Move these resources to the API.
    if permission_form.validate_on_submit():
        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)

        # Add collaborators to the sketch
        # TODO(jbn): Make write permission off by default
        # and selectable in the UI
        if permission_form.username.data:
            usernames = permission_form.username.data
            for username in usernames.split(','):
                base_username = username.split('@')[0]
                base_username = base_username.strip()
                user = User.query.filter_by(username=base_username).first()
                if user:
                    sketch.grant_permission(permission='read', user=user)
                    sketch.grant_permission(permission='write', user=user)

        # Add a group to the sketch
        if permission_form.groups.data:
            group_id = permission_form.groups.data
            group = Group.query.get(group_id)
            # Only add groups publicly visible or owned by the current user
            if not group.user or group.user == current_user:
                sketch.grant_permission(permission='read', group=group)
                sketch.grant_permission(permission='write', group=group)

        # Remove groups from sketch
        if permission_form.remove_groups.data:
            for group_id in permission_form.remove_groups.data:
                group = Group.query.get(group_id)
                sketch.revoke_permission(permission='read', group=group)
                sketch.revoke_permission(permission='write', group=group)

        # Remove users from sketch
        if permission_form.remove_users.data:
            for user_id in permission_form.remove_users.data:
                user = User.query.get(user_id)
                sketch.revoke_permission(permission='read', user=user)
                sketch.revoke_permission(permission='write', user=user)

        if permission_form.permission.data == 'public':
            sketch.grant_permission(permission='read')
        else:
            sketch.revoke_permission(permission='read')
        db_session.commit()
        return redirect(url_for('sketch_views.overview', sketch_id=sketch.id))

    # Change status form POST
    if status_form.validate_on_submit():
        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        sketch.set_status(status=status_form.status.data)
        return redirect(url_for('sketch_views.overview', sketch_id=sketch.id))

    # Trash form POST
    if trash_form.validate_on_submit():
        if not sketch.has_permission(current_user, 'delete'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        sketch.set_status(status='deleted')
        return redirect(url_for('home_views.home'))

    return render_template(
        'sketch/overview.html',
        sketch=sketch,
        sketch_form=sketch_form,
        permission_form=permission_form,
        status_form=status_form,
        trash_form=trash_form,
        upload_enabled=upload_enabled,
        graphs_enabled=graphs_enabled)


@sketch_views.route(
    '/sketch/<int:sketch_id>/explore/', methods=['GET', 'POST'])
@sketch_views.route(
    '/sketch/<int:sketch_id>/explore/view/<int:view_id>/',
    methods=['GET', 'POST'])
@sketch_views.route(
    '/sketch/<int:sketch_id>/explore/searchtemplate/<int:searchtemplate_id>/',
    methods=['GET', 'POST'])
@login_required
def explore(sketch_id, view_id=None, searchtemplate_id=None):
    """Generates the sketch explore view template.

    Returns:
        Template with context.
    """
    save_view = False  # If the view should be saved to the database.
    sketch = Sketch.query.get_with_acl(sketch_id)
    sketch_timelines = [t.searchindex.index_name for t in sketch.timelines]
    view_form = SaveViewForm()
    graphs_enabled = current_app.config['GRAPH_BACKEND_ENABLED']
    similarity_enabled = current_app.config.get('ENABLE_EXPERIMENTAL_UI')

    # Get parameters from the GET query
    url_query = request.args.get('q', '')
    url_time_start = request.args.get('time_start', None)
    url_time_end = request.args.get('time_end', None)
    url_index = request.args.get('index', None)
    url_size = request.args.get('size', None)

    if searchtemplate_id:
        searchtemplate = SearchTemplate.query.get(searchtemplate_id)
        view = sketch.get_user_view(current_user)
        if not view:
            view = View(user=current_user, name='', sketch=sketch)
        view.query_string = searchtemplate.query_string
        view.query_filter = searchtemplate.query_filter
        view.query_dsl = searchtemplate.query_dsl
        save_view = True
    elif view_id:
        view = View.query.get(view_id)

        # Check that this view belongs to the sketch
        if view.sketch_id != sketch.id:
            abort(HTTP_STATUS_CODE_NOT_FOUND)

        # Return 404 if view is deleted
        if view.get_status.status == 'deleted':
            return abort(HTTP_STATUS_CODE_NOT_FOUND)
    else:
        view = sketch.get_user_view(current_user)
        if not view:
            view = View(
                user=current_user, name='', sketch=sketch, query_string='*')
            view.query_filter = view.validate_filter(
                dict(indices=sketch_timelines))
            save_view = True

    if url_query:
        view.query_string = url_query
        query_filter = json.loads(view.query_filter)
        query_filter['from'] = 0 # if we loaded from get, start at first event
        query_filter['time_start'] = url_time_start
        query_filter['time_end'] = url_time_end
        if url_index in sketch_timelines:
            query_filter['indices'] = [url_index]
        if url_size:
            query_filter['size'] = url_size
        view.query_filter = view.validate_filter(query_filter)
        view.query_dsl = None
        save_view = True

    if save_view:
        db_session.add(view)
        db_session.commit()

    return render_template(
        'sketch/explore.html',
        sketch=sketch,
        view=view,
        named_view=view_id,
        timelines=sketch_timelines,
        view_form=view_form,
        searchtemplate_id=searchtemplate_id,
        graphs_enabled=graphs_enabled,
        similarity_enabled=similarity_enabled)


@sketch_views.route(
    '/sketch/<int:sketch_id>/graph/', methods=['GET', 'POST'])
@login_required
def graphs(sketch_id):
    """Generates the sketch views template.

    Returns:
        Template with context.
    """
    sketch = Sketch.query.get_with_acl(sketch_id)
    graphs_enabled = current_app.config['GRAPH_BACKEND_ENABLED']

    return render_template(
        'sketch/graph.html',
        sketch=sketch,
        graphs_enabled=graphs_enabled)


@sketch_views.route('/sketch/<int:sketch_id>/stories/')
@sketch_views.route('/sketch/<int:sketch_id>/stories/<int:story_id>/')
@login_required
def story(sketch_id, story_id=None):
    """Generates the story list template.

    Returns:
        Template with context.
    """
    sketch = Sketch.query.get_with_acl(sketch_id)
    graphs_enabled = current_app.config['GRAPH_BACKEND_ENABLED']

    current_story = None
    if story_id:
        current_story = Story.query.get(story_id)
    return render_template(
        'sketch/stories.html', sketch=sketch, story=current_story,
        graphs_enabled=graphs_enabled)


@sketch_views.route(
    '/sketch/<int:sketch_id>/views/', methods=['GET', 'POST'])
@login_required
def views(sketch_id):
    """Generates the sketch views template.

    Returns:
        Template with context.
    """
    sketch = Sketch.query.get_with_acl(sketch_id)
    trash_form = TrashViewForm()
    graphs_enabled = current_app.config['GRAPH_BACKEND_ENABLED']

    # Trash form POST
    if trash_form.validate_on_submit():
        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        view_id = trash_form.view_id.data
        view = View.query.get(view_id)
        # Check that this view belongs to the sketch
        if view.sketch_id != sketch.id:
            abort(HTTP_STATUS_CODE_NOT_FOUND)
        view.set_status(status='deleted')
        return redirect('/sketch/{0:d}/views/'.format(sketch.id))

    return render_template(
        'sketch/views.html',
        sketch=sketch,
        trash_form=trash_form,
        graphs_enabled=graphs_enabled)


@sketch_views.route(
    '/sketch/<int:sketch_id>/timelines/', methods=['GET', 'POST'])
@login_required
def timelines(sketch_id):
    """Generates the sketch explore view template.

    Returns:
        Template with context.
    """
    sketch = Sketch.query.get_with_acl(sketch_id)
    searchindices_in_sketch = [t.searchindex.id for t in sketch.timelines]
    indices = SearchIndex.all_with_acl(current_user).order_by(
        desc(SearchIndex.created_at)).filter(
            not_(SearchIndex.id.in_(searchindices_in_sketch)))
    upload_enabled = current_app.config['UPLOAD_ENABLED']
    graphs_enabled = current_app.config['GRAPH_BACKEND_ENABLED']

    try:
        plaso_version = current_app.config['PLASO_VERSION']
    except KeyError:
        plaso_version = 'Unknown'

    # Setup the form
    form = AddTimelineForm()
    form.timelines.choices = set((i.id, i.name) for i in indices.all())

    # Create new timeline form POST
    if form.validate_on_submit():
        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        for searchindex_id in form.timelines.data:
            searchindex = SearchIndex.query.get_with_acl(searchindex_id)
            if searchindex not in [t.searchindex for t in sketch.timelines]:
                _timeline = Timeline(
                    name=searchindex.name,
                    description=searchindex.description,
                    sketch=sketch,
                    user=current_user,
                    searchindex=searchindex)
                db_session.add(_timeline)
                sketch.timelines.append(_timeline)
                db_session.commit()

                # If enabled, run sketch analyzers when timeline is added.
                # Import here to avoid circular imports.
                from timesketch.lib import tasks
                sketch_analyzer_group = tasks.build_sketch_analysis_pipeline(
                    sketch_id, current_user.id)
                if sketch_analyzer_group:
                    pipeline = (tasks.run_sketch_init.s(
                        [searchindex.index_name]) | sketch_analyzer_group)
                    pipeline.apply_async(task_id=searchindex.index_name)

        return redirect(
            url_for('sketch_views.timelines', sketch_id=sketch.id))

    return render_template(
        'sketch/timelines.html',
        sketch=sketch,
        timelines=indices.all(),
        form=form,
        upload_enabled=upload_enabled,
        plaso_version=plaso_version,
        graphs_enabled=graphs_enabled)


@sketch_views.route(
    '/sketch/<int:sketch_id>/timelines/<int:timeline_id>/',
    methods=['GET', 'POST'])
@login_required
def timeline(sketch_id, timeline_id):
    """Generates the sketch timeline view template.

    Returns:
        Template with context.
    """
    timeline_form = TimelineForm()
    sketch = Sketch.query.get_with_acl(sketch_id)
    sketch_timeline = Timeline.query.filter(Timeline.id == timeline_id,
                                            Timeline.sketch == sketch).first()
    graphs_enabled = current_app.config['GRAPH_BACKEND_ENABLED']

    if not sketch_timeline:
        abort(HTTP_STATUS_CODE_NOT_FOUND)

    if timeline_form.validate_on_submit():
        if not sketch.has_permission(current_user, 'write'):
            abort(HTTP_STATUS_CODE_FORBIDDEN)
        sketch_timeline.name = timeline_form.name.data
        sketch_timeline.description = timeline_form.description.data
        sketch_timeline.color = timeline_form.color.data
        db_session.add(sketch_timeline)
        db_session.commit()
        return redirect(
            url_for(
                'sketch_views.timeline',
                sketch_id=sketch.id,
                timeline_id=sketch_timeline.id))

    return render_template(
        'sketch/timeline.html',
        sketch=sketch,
        timeline=sketch_timeline,
        timeline_form=timeline_form,
        graphs_enabled=graphs_enabled)


@sketch_views.route(
    '/sketch/<int:sketch_id>/explore/export/', methods=['GET'])
@login_required
def export(sketch_id):
    """Generates CSV from search result.

    Args:
        sketch_id: Primary key for a sketch.
    Returns:
        CSV string with header.
    """
    sketch = Sketch.query.get_with_acl(sketch_id)
    view = sketch.get_user_view(current_user)
    query_filter = json.loads(view.query_filter)
    query_dsl = json.loads(view.query_dsl)
    indices = query_filter.get('indices', [])

    # Export more than the 500 first results.
    max_events_to_fetch = 10000
    query_filter['terminate_after'] = max_events_to_fetch
    query_filter['size'] = max_events_to_fetch

    datastore = ElasticsearchDataStore(
        host=current_app.config['ELASTIC_HOST'],
        port=current_app.config['ELASTIC_PORT'])

    result = datastore.search(
        sketch_id,
        view.query_string,
        query_filter,
        query_dsl,
        indices,
        aggregations=None)

    all_fields = set()
    for event in result['hits']['hits']:
        all_fields.update(event['_source'].keys())

    all_fields.difference_update(DEFAULT_FIELDS)
    fieldnames = DEFAULT_FIELDS + sorted(all_fields)

    csv_out = StringIO()
    csv_writer = csv.DictWriter(csv_out, fieldnames=fieldnames)
    csv_writer.writeheader()
    for _event in result['hits']['hits']:
        sources = _event['_source']
        row = {}
        for key, value in iter(sources.items()):
            if isinstance(value, six.binary_type):
                value = codecs.decode(value, 'utf-8')
            row[key] = value
        row['_index'] = _event['_index']
        if isinstance(row['_index'], six.binary_type):
            row['_index'] = row['_index'].encode('utf-8')
        csv_writer.writerow(row)

    return csv_out.getvalue()
