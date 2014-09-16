# Copyright 2014 Google Inc. All rights reserved.
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
"""This module implements timesketch API."""

import json

from django.contrib.auth.models import User
from tastypie.resources import Resource
from tastypie.resources import ModelResource
from tastypie.authorization import Authorization
from tastypie.authentication import SessionAuthentication
from tastypie import fields, utils
from pyelasticsearch.exceptions import ElasticHttpNotFoundError

from timesketch.lib.datastores import elasticsearch_datastore
from timesketch.apps.sketch.models import Sketch
from timesketch.apps.sketch.models import EventComment
from timesketch.apps.sketch.models import SavedView
from timesketch.apps.sketch.models import Timeline
from timesketch.apps.sketch.models import SketchTimeline
from timesketch.apps.userprofile.models import UserProfile

# Set the type of datastore.
DATASTORE = elasticsearch_datastore.ElasticSearchDataStore


class DatastoreObject(object):
    """Tastypie need this. Generic object to get data in and out."""
    def __init__(self, initial=None):
        self.__dict__['_data'] = {}

        if not initial:
            return

        if initial.get("_source"):
            self.__dict__['_data'] = initial["_source"]
            self.__dict__['_data']['es_index'] = initial['_index']
            self.__dict__['_data']['es_id'] = initial['_id']
            self.__dict__['_data']['label'] = []

            label_set = set()
            try:
                for label in initial["_source"]["timesketch_label"]:
                    if label["name"] == "__ts_star" and \
                            label["sketch"] == initial["_source"]["sketch"]:
                        label_set.add(label["name"])
                    elif label["name"] == "__ts_comment" and \
                            label["sketch"] == initial["_source"]["sketch"]:
                        label_set.add(label["name"])
                    elif label["user"] == initial["_source"]["req_user"] and \
                            label["sketch"] == initial["_source"]["sketch"]:
                        label_set.add(label["name"])
                self.__dict__['_data']['label'] = list(label_set)
            except KeyError:
                pass

    def __getattr__(self, name):
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        self.__dict__['_data'][name] = value


class UserProfileResource(ModelResource):
    """Model resource for UserProfile."""
    class Meta:
        resource_name = 'userprofile'
        queryset = UserProfile.objects.all()
        fields = ['']
        authorization = Authorization()
        authentication = SessionAuthentication()

    def dehydrate(self, bundle):
        bundle.data['avatar'] = bundle.obj.get_avatar_url()
        return bundle


class UserResource(ModelResource):
    """Model resource for User."""
    profile = fields.OneToOneField(UserProfileResource, attribute='userprofile',
                                   full=True)

    class Meta:
        resource_name = 'user'
        queryset = User.objects.all()
        fields = ['username', 'first_name', 'last_name']
        authorization = Authorization()
        authentication = SessionAuthentication()


class SearchResource(Resource):
    """Resource for handling search requests."""
    es_index = fields.CharField(attribute='es_index')
    es_id = fields.CharField(attribute='es_id')
    datetime = fields.CharField(attribute='datetime')
    timestamp = fields.IntegerField(attribute='timestamp')
    timestamp_desc = fields.CharField(attribute='timestamp_desc', null=True)
    message = fields.CharField(attribute='message')
    tag = fields.ListField(attribute='tag', null=True)
    label = fields.ListField(attribute='label', null=True)

    def __init__(self):
        self.query_result = {}
        super(SearchResource, self).__init__()

    class Meta:
        resource_name = 'search'
        object_class = DatastoreObject
        authorization = Authorization()
        authentication = SessionAuthentication()

    def obj_get_list(self, bundle, **kwargs):
        query = bundle.request.GET['q']
        query_filter = json.loads(bundle.request.GET['filter'])
        indexes_to_search = query_filter.get("indexes")
        sketch = Sketch.objects.get(id=bundle.request.GET['sketch'])
        datastore = DATASTORE(indexes_to_search)
        result = []
        try:
            self.query_result = datastore.search(sketch.id, query, query_filter)
        except ElasticHttpNotFoundError:
            self.query_result = {'hits': {'hits': []}}

        for event in self.query_result['hits']['hits']:
            event["_source"]["req_user"] = bundle.request.user.id
            event["_source"]["sketch"] = str(sketch.id)
            result.append(DatastoreObject(initial=event))
        # Save state to an unnamed view
        SavedView.objects.create(user=bundle.request.user, sketch=sketch,
                                 query=query, filter=json.dumps(query_filter),
                                 name="")
        return result

    def alter_list_data_to_serialize(self, request, data):
        timeline_colors = {}
        timeline_names = {}
        sketch = Sketch.objects.get(id=request.GET['sketch'])
        for t in sketch.timelines.all():
            timeline_colors[t.timeline.datastore_index] = t.color
            timeline_names[t.timeline.datastore_index] = t.timeline.title
        try:
            data['meta']['es_time'] = self.query_result['took']
            data['meta']['es_total_count'] = self.query_result['hits']['total']
        except KeyError:
            data['meta']['es_time'] = 0
            data['meta']['es_total_count'] = 0
        data['meta']['timeline_colors'] = timeline_colors
        data['meta']['timeline_names'] = timeline_names
        return data


class EventResource(Resource):
    """Get all details for an event."""
    es_index = fields.CharField(attribute='es_index')
    es_id = fields.CharField(attribute='es_id')
    label = fields.CharField(attribute='label', null=True)
    timestamp = fields.IntegerField(attribute='timestamp')
    timestamp_desc = fields.CharField(attribute='timestamp_desc')
    datetime = fields.CharField(attribute='datetime')
    source_short = fields.CharField(attribute='source_short')
    source_long = fields.CharField(attribute='source_long')
    message = fields.CharField(attribute='message')
    # Plaso specific
    tag = fields.ListField(attribute='tag', null=True)
    display_name = fields.CharField(attribute='display_name', null=True)
    filename = fields.CharField(attribute='filename', null=True)
    parser = fields.CharField(attribute='parser', null=True)
    username = fields.CharField(attribute='username', null=True)
    store_number = fields.CharField(attribute='store_number', null=True)
    hostname = fields.CharField(attribute='hostname', null=True)
    uuid = fields.CharField(attribute='uuid', null=True)
    data_type = fields.CharField(attribute='data_type', null=True)
    fs_type = fields.CharField(attribute='fs_type', null=True)
    store_index = fields.IntegerField(attribute='store_index', null=True)
    offset = fields.IntegerField(attribute='offset', null=True)
    allocated = fields.CharField(attribute='allocated', null=True)
    inode = fields.IntegerField(attribute='inode', null=True)
    size = fields.IntegerField(attribute='size', null=True)

    class Meta:
        resource_name = 'event'
        object_class = DatastoreObject
        authorization = Authorization()
        authentication = SessionAuthentication()

    def obj_get_list(self, bundle, **kwargs):
        event = bundle.request.GET['id']
        index = bundle.request.GET['index']
        datastore = DATASTORE([index])
        result = []
        r = datastore.get_single_event(event)
        r["_source"]["req_user"] = bundle.request.user.id
        new_obj = DatastoreObject(initial=r)
        result.append(new_obj)
        return result


class CommentResource(ModelResource):
    """Resource for add comment to event."""
    user = fields.ForeignKey(UserResource, attribute='user', full=True)
    body = fields.CharField(attribute='body', null=True)
    datastore_index = fields.CharField(attribute='datastore_index', null=True)
    datastore_id = fields.CharField(attribute='datastore_id', null=True)
    created = fields.CharField(attribute='created', default=utils.now)
    updated = fields.CharField(attribute='updated')

    class Meta:
        resource_name = 'comment'
        always_return_data = True
        authorization = Authorization()
        authentication = SessionAuthentication()

    def obj_get_list(self, bundle, **kwargs):
        datastore_index = bundle.request.GET['index']
        datastore_id = bundle.request.GET['id']
        sketch_id = bundle.request.GET['sketch']
        sketch = Sketch.objects.get(id=sketch_id)
        result = EventComment.objects.filter(datastore_index=datastore_index,
            datastore_id=datastore_id, sketch=sketch)
        return result

    def obj_create(self, bundle, **kwargs):
        datastore_index = json.loads(bundle.request.body)['data']['index']
        datastore_id = json.loads(bundle.request.body)['data']['id']
        sketch_id = json.loads(bundle.request.body)['data']['sketch']
        sketch = Sketch.objects.get(pk=sketch_id)
        body = json.loads(bundle.request.body)['data']['body']
        result = EventComment.objects.create(user=bundle.request.user,
            datastore_index=datastore_index, datastore_id=datastore_id, 
            body=body, sketch=sketch, created=utils.now())
        bundle.obj = result
        bundle.data['data']['created'] = result.created
        bundle.data['data']['user'] = {}
        bundle.data['data']['user']['first_name'] = result.user.first_name
        bundle.data['data']['user']['last_name'] = result.user.last_name
        bundle.data['data']['user']['profile'] = {}
        bundle.data['data']['user']['profile']['avatar'] = result.user.userprofile.get_avatar_url()
        datastore = DATASTORE(datastore_index)
        datastore.add_label_to_event(datastore_id, sketch_id,
            bundle.request.user.id, "__ts_comment")
        return bundle


class LabelResource(Resource):
    """Add and remove labels."""
    class Meta:
        resource_name = 'label'
        always_return_data = True
        authorization = Authorization()
        authentication = SessionAuthentication()

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        return kwargs

    def obj_create(self, bundle, request=None, **kwargs):
        toggle = False
        req_data = json.loads(bundle.request.body)['data']
        if req_data['label'] == "__ts_star":
            toggle = True
        datastore = DATASTORE(req_data['index'])
        datastore.add_label_to_event(req_data['id'], req_data['sketch'], 
            bundle.request.user.id, req_data['label'], toggle=toggle)
        return bundle


class SketchResource(ModelResource):
    class Meta:
        resource_name = 'sketch'
        authorization = Authorization()
        authentication = SessionAuthentication()

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        return kwargs

    def obj_create(self, bundle, **kwargs):
        req_data = json.loads(bundle.request.body)['data'] 
        Sketch.objects.create(owner=bundle.request.user, 
            title=req_data['title'], description=req_data['description'])
        return bundle


class SketchTimelineResource(ModelResource):
    """Create new timeline bound to a specific sketch."""
    class Meta:
        resource_name = 'sketchtimeline'
        authorization = Authorization()
        authentication = SessionAuthentication()

    def obj_create(self, bundle, **kwargs):
        """Create new timeline for a sketch."""
        req_data = json.loads(bundle.request.body)['data']
        sketch = Sketch.objects.get(id=req_data['sketch'])
        timeline = Timeline.objects.get(id=req_data['timeline'])
        try:
            sketch_timeline = SketchTimeline.objects.get(timeline=timeline, 
                sketch=sketch)
        except SketchTimeline.DoesNotExist:
            sketch_timeline = SketchTimeline.objects.create(timeline=timeline)
            sketch_timeline.color = sketch_timeline.generate_color()
            sketch_timeline.save()
        sketch.timelines.add(sketch_timeline)
        sketch.save()
        return bundle


class SketchAclResource(ModelResource):
    class Meta:
        resource_name = 'sketch_acl'
        authorization = Authorization()
        authentication = SessionAuthentication()

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        return kwargs

    def obj_create(self, bundle, **kwargs):
        req_data = json.loads(bundle.request.body)['data']
        sketch = Sketch.objects.get(id=req_data['sketch'])
        if req_data['sketch_acl'] == "public":
            sketch.make_public(bundle.request.user)
        else:
            sketch.make_private(bundle.request.user)
        return bundle


class ViewResource(ModelResource):
    class Meta:
        queryset = SavedView.objects.filter(name__exact="").order_by("-created")
        resource_name = 'view'
        list_allowed_methods = ['get', 'post']
        ordering = "created"
        limit = 1
        authorization = Authorization()
        authentication = SessionAuthentication()

    def obj_get_list(self, bundle, **kwargs):
        sketch_id = bundle.request.GET['sketch']
        view_id = int(bundle.request.GET['view'])
        sketch = Sketch.objects.get(id=sketch_id)
        result = []
        if view_id > 0:
            view = SavedView.objects.get(id=view_id)
            if view.sketch == sketch:
                result = [view]
        else:
            result = SavedView.objects.filter(user=bundle.request.user,
                sketch=sketch,
                name__exact="").order_by("-created")
        return result

    def obj_create(self, bundle, **kwargs):
        req_data = json.loads(bundle.request.body)['data']
        sketch = Sketch.objects.get(id=req_data['sketch'])
        query = req_data['query']
        if not query:
            query = " "
        SavedView.objects.create(user=bundle.request.user, sketch=sketch,
            query=query, filter=json.dumps(req_data['query_filter']),
            name=req_data['name'])
        return bundle
