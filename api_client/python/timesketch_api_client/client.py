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

import requests
import BeautifulSoup
import json


class TimesketchApi(object):
    """Timesketch API object.
    
    """
    def __init__(self, host_uri, username, password, verify=True):
        self.host_uri = host_uri
        self.api_root = u'{0:s}/api/v1'.format(host_uri)
        self.session = self._create_session(username, password, verify=verify)

    def _create_session(self, username, password, verify):
        session = requests.Session()
        session.verify = verify  # Depending if SSL cert is verifiable

        # Get the CSRF token from the response
        response = session.get(self.host_uri)
        soup = BeautifulSoup.BeautifulSoup(response.text)
        csrf_token = soup.find(id=u'csrf_token').get(u'value')
        session.headers.update(
            {u'x-csrftoken': csrf_token, u'referer': self.host_uri})

        # Do a POST to the login handler to set up the session cookies
        data = {u'username': username, u'password': password}
        session.post(u'{0:s}/login/'.format(self.host_uri), data=data)
        return session

    def fetch_resource_data(self, resource_uri):
        resource_url = u'{0:s}/{1:s}'.format(self.api_root, resource_uri)
        response = self.session.get(resource_url)
        return response.json()

    def get_sketch(self, sketch_id):
        return Sketch(sketch_id, api=self)

    def create_sketch(self, name, description):
        resource_url = u'{0:s}/sketches/'.format(self.api_root)
        form_data = {u'name': name, u'description': description}
        response = self.session.post(resource_url, json=form_data)
        response_dict = response.json()
        sketch_id = response_dict[u'objects'][0][u'id']
        return self.get_sketch(sketch_id)

    def list_sketches(self):
        sketches = []
        response = self.fetch_resource_data(u'sketches/')
        for sketch in response[u'objects'][0]:
            sketch_id = sketch[u'id']
            sketch_name = sketch[u'name']
            sketch_obj = Sketch(
                sketch_id=sketch_id, api=self, sketch_name=sketch_name)
            sketches.append(sketch_obj)
        return sketches


class BaseSketchResource(object):
    def __init__(self, sketch, resource_uri):
        self.sketch = sketch
        self.data = None
        self.resource_url = u'{0:s}/sketches/{1:d}/{2:s}'.format(
            sketch.api.api_root, sketch.id, resource_uri)

    def lazyload_data(self):
        if not self.data:
            print "lazyload base"
            self.data = self.sketch.api.fetch_resource_data(self.resource_url)
        return self.data


class View(BaseSketchResource):
    def __init__(self, view_id, view_name, sketch):
        self.id = view_id
        self.name = view_name
        resource_uri = u'views/{0:d}/'.format(self.id)
        super(View, self).__init__(sketch, resource_uri)

    @property
    def query_string(self):
        view = self.lazyload_data()
        return view[u'objects'][0][u'query_string']

    @property
    def query_filter(self):
        view = self.lazyload_data()
        return view[u'objects'][0][u'query_filter']

    @property
    def query_dsl(self):
        view = self.lazyload_data()
        return view[u'objects'][0][u'query_dsl']


class Timeline(BaseSketchResource):
    def __init__(self, timeline_id, timeline_name, timeline_index, sketch):
        self.id = timeline_id
        self.name = timeline_name
        self.index = timeline_index
        resource_uri = u'views/{0:d}/'.format(self.id)
        super(Timeline, self).__init__(sketch, resource_uri)

    @property
    def query_string(self):
        view = self.lazyload_data()
        return view[u'objects'][0][u'query_string']


class Sketch(object):
    def __init__(self, sketch_id, api, sketch_name=None):
        self.id = sketch_id
        self.sketch_name = sketch_name
        self.api = api
        self.data = None

    def _lazyload_data(self):
        if not self.data:
            resource_uri = u'sketches/{0:d}'.format(self.id)
            self.data = self.api.fetch_resource_data(resource_uri)
            print json.dumps(self.data, indent=2)
        return self.data

    @property
    def name(self):
        if not self.sketch_name:
            sketch = self._lazyload_data()
            self.sketch_name = sketch[u'objects'][0][u'name']
        return self.sketch_name

    @property
    def description(self):
        sketch = self._lazyload_data()
        return sketch[u'objects'][0][u'description']

    @property
    def status(self):
        sketch = self._lazyload_data()
        return sketch[u'objects'][0][u'status'][0][u'status']

    @property
    def views(self):
        sketch = self._lazyload_data()
        views = []
        for view in sketch[u'meta'][u'views']:
            view_obj = View(
                view_id=view[u'id'], view_name=view[u'name'], sketch=self)
            views.append(view_obj)
        return views

    def upload(self, timeline_name, file_path):
        resource_url = u'{0:s}/upload/'.format(self.api.api_root)
        files = {u'file': open(file_path, 'rb')}
        data = {u'name': timeline_name, u'sketch_id': self.id}
        response = self.api.session.post(resource_url, files=files, data=data)
        response_dict = response.json()
        index_id = response_dict[u'objects'][0][u'id']
        return index_id

    def explore(self, query_string=None, query_dsl=None, query_filter=None,
                view=None):

        default_filter = {
            u'time_start': None,
            u'time_end': None,
            u'limit': 40,
            u'indices': u'_all',
            u'order': u'asc'
        }

        if not (query_string or query_filter or query_dsl or view):
            raise RuntimeError(u'You need to supply a query or view')

        if not query_filter:
            query_filter = default_filter

        if view:
            query_string = view.query_string
            query_filter = json.loads(view.query_filter)
            query_dsl = json.loads(view.query_dsl)

        resource_url = u'{0:s}/sketches/{1:d}/explore/'.format(
            self.api.api_root, self.id)

        form_data = {
            u'query': query_string,
            u'filter': query_filter,
            u'dsl': query_dsl,
        }
        response = self.api.session.post(resource_url, json=form_data)
        return response.json()
