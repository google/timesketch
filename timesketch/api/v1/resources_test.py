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
"""Tests for v1 of the Timesketch API."""
from __future__ import print_function

import json
import os
import re
import mock

from flask_restful import fields

from timesketch.lib.definitions import HTTP_STATUS_CODE_CREATED
from timesketch.lib.definitions import HTTP_STATUS_CODE_OK
from timesketch.lib.definitions import HTTP_STATUS_CODE_BAD_REQUEST
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore

from timesketch.api.v1.resources import ResourceMixin


class TypescriptDefinitionTest(BaseTest):
    def test_definition_is_in_sync_with_api_schema(self):
        """Parse Typescript definition for API types and compare it to
        api schema defined in ResourceMixin.
        """
        # pylint: disable=redefined-outer-name,missing-docstring
        def parse_definition():
            this_dir = os.path.dirname(__file__)
            definition_path = os.path.join(
                this_dir, '..', '..', 'ui', 'api', 'models.ts')
            with open(definition_path) as definition_file:
                definition = definition_file.read()
            interfaces = r'interface\s+([a-zA-Z_]+)\s*\{([^\}]*)\}'
            fields = r'^\s*([a-zA-Z_]+)\s*\:\s*(.*?)\s*((?:\[\])?)\s*$'
            parsed_definition = {}
            for interface in re.finditer(interfaces, definition):
                interface_name, interface_body = interface.groups()
                parsed_interface = {}
                for field in re.finditer(fields, interface_body, re.MULTILINE):
                    field_name, field_type, is_array = field.groups()
                    if is_array:
                        parsed_interface[field_name] = {'[i]': field_type}
                    else:
                        parsed_interface[field_name] = field_type
                parsed_definition[interface_name] = parsed_interface
            return parsed_definition

        def resolve_references(definition):
            def resolve(x):
                if isinstance(x, str) and x in definition:
                    return definition[x]
                if isinstance(x, dict):
                    return {k: resolve(v) for k, v in x.items()}
                return x
            for _ in range(10):
                definition = {k: resolve(v) for k, v in definition.items()}
            return definition

        def parse_api_schema():
            def format_fields(fields):
                return {k: format_field(v) for k, v in fields.items()}

            def format_field(field):
                # pylint: disable=unidiomatic-typecheck
                typemap = {
                    fields.Integer: 'fields.Integer',
                    fields.String: 'fields.String',
                    fields.Boolean: 'fields.Boolean',
                    fields.DateTime: 'fields.DateTime',
                }
                if isinstance(field, type):
                    return typemap[field]
                if type(field) in typemap:
                    return typemap[type(field)]
                elif isinstance(field, fields.Nested):
                    return format_fields(field.nested)
                elif isinstance(field, fields.List):
                    return {'[i]': format_field(field.container)}
                else:
                    assert False

            api_schema = {
                k: format_fields(v)
                for k, v in ResourceMixin.__dict__.items()
                if k.endswith('_fields')
            }
            return api_schema

        def flatten_dict(d):
            result = {}
            for k, v in d.items():
                if isinstance(v, dict):
                    v = flatten_dict(v)
                    v = {('%s.%s' % (k, kk)): vv for kk, vv in v.items()}
                    result.update(v)
                else:
                    result[k] = v
            return result

        def fix_array_access(d):
            return {k.replace('.[i]', '[i]'): v for k, v in d.items()}

        def key(entry):
            return entry[0].replace('_fields', '').lower()

        def consecutive_pairs(li):
            for i in range(1, len(li)):
                yield li[i-1], li[i]

        def match_type(t1, t2):
            types = [
                ('fields.Integer', 'number'),
                ('fields.String', 'string'),
                ('fields.Boolean', 'boolean'),
                ('fields.DateTime', 'DateTime'),
            ]
            return (t1, t2) in types or (t2, t1) in types

        definition = parse_definition()
        definition = resolve_references(definition)
        definition = flatten_dict(definition)
        definition = fix_array_access(definition)
        api_schema = parse_api_schema()
        api_schema = flatten_dict(api_schema)
        api_schema = fix_array_access(api_schema)
        entries = sorted(
            list(definition.items()) + list(api_schema.items()), key=key)
        errors = 0
        for entry1, entry2 in consecutive_pairs(entries):
            if key(entry1) == key(entry2):
                if not match_type(entry1[1], entry2[1]):
                    print('')
                    print('Type mismatch:')
                    print('%s: %s' % entry1)
                    print('%s: %s' % entry2)
                    errors += 1
                definition.pop(entry1[0], None)
                definition.pop(entry2[0], None)
                api_schema.pop(entry1[0], None)
                api_schema.pop(entry2[0], None)
        if definition:
            print('')
            print(
                'The following fields are present in Typescript definition'
                ' but are not present in ResourceMixin API schema:'
            )
        for item in definition.items():
            print('%s: %s' % item)
        if api_schema:
            print('')
            print(
                'The following fields are present in ResourceMixin API schema'
                ' but are not present in Typescript definition:'
            )
        for item in api_schema.items():
            print('%s: %s' % item)
        self.assertEqual(len(definition) + len(api_schema) + errors, 0)


class ResourceMixinTest(BaseTest):
    """Test ResourceMixin."""

    def test_to_json_empty_list(self):
        """Behavior of to_json when given an empty list."""
        response = ResourceMixin().to_json([])
        self.assertEqual(response.json, {
            'meta': {},
            'objects': [],
        })


class SketchListResourceTest(BaseTest):
    """Test SketchListResource."""
    resource_url = u'/api/v1/sketches/'

    def test_sketch_list_resource(self):
        """Authenticated request to get list of sketches."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assertEqual(len(response.json[u'objects'][0]), 2)
        result = sorted(i['name'] for i in response.json[u'objects'][0])
        self.assertEqual(result, [u'Test 1', u'Test 3'])
        self.assert200(response)

    def test_sketch_post_resource(self):
        """Authenticated request to create a sketch."""
        self.login()
        data = dict(name=u'test', description=u'test')
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type=u'application/json')
        self.assertEquals(response.status_code, HTTP_STATUS_CODE_CREATED)


class SketchResourceTest(BaseTest):
    """Test SketchResource."""
    resource_url = u'/api/v1/sketches/1/'

    def test_sketch_resource(self):
        """Authenticated request to get a sketch."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assertEqual(len(response.json[u'objects']), 1)
        self.assertEqual(len(response.json[u'objects'][0][u'timelines']), 1)
        self.assertEqual(response.json[u'objects'][0][u'name'], u'Test 1')
        self.assert200(response)

    def test_sketch_acl(self):
        """
        Authenticated request to get a sketch that the user do not have read
        permission on.
        """
        self.login()
        response = self.client.get(u'/api/v1/sketches/2/')
        self.assert403(response)


class ViewListResourceTest(BaseTest):
    """Test ViewListResource."""
    resource_url = u'/api/v1/sketches/1/views/'

    def test_post_view_list_resource(self):
        """Authenticated request to create a view."""
        self.login()
        data = dict(
            name=u'test',
            new_searchtemplate=False,
            query=u'test',
            filter={},
            dsl={})
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type=u'application/json')
        data[u'from_searchtemplate_id'] = 1
        response_with_searchtemplate = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type=u'application/json')
        self.assertEquals(response.status_code, HTTP_STATUS_CODE_CREATED)
        self.assertEquals(response_with_searchtemplate.status_code,
                          HTTP_STATUS_CODE_CREATED)


class ViewResourceTest(BaseTest):
    """Test ViewResource."""
    resource_url = u'/api/v1/sketches/1/views/1/'

    def test_view_resource(self):
        """Authenticated request to get a view."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assertEqual(len(response.json[u'objects']), 1)
        self.assertEqual(response.json[u'objects'][0][u'name'], u'View 1')
        self.assert200(response)

    def test_post_view_resource(self):
        """Authenticated request to update a view."""
        self.login()
        data = dict(name=u'test', query=u'test', filter=u'{}')
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type=u'application/json')
        self.assertEquals(response.status_code, HTTP_STATUS_CODE_CREATED)

    def test_invalid_user_in_view(self):
        """Authenticated request to get a view for another user."""
        self.login()
        response = self.client.get(u'/api/v1/sketches/1/views/3/')
        self.assert403(response)

    def test_invalid_view(self):
        """Authenticated request to get a view for non existing view."""
        self.login()
        response = self.client.get(u'/api/v1/sketches/1/views/2/')
        self.assert404(response)


class SearchTemplateResourceTest(BaseTest):
    """Test Search template resource."""
    resource_url = u'/api/v1/searchtemplate/1/'

    def test_searchtemplate_resource(self):
        """Authenticated request to get a search template."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assertEqual(len(response.json[u'objects']), 1)
        self.assertEqual(response.json[u'objects'][0][u'name'], u'template')
        self.assert200(response)

    def test_invalid_searchtemplate(self):
        """Authenticated request to get a non existing search template."""
        self.login()
        response = self.client.get(u'/api/v1/searchtemplate/2/')
        self.assert404(response)


class ExploreResourceTest(BaseTest):
    """Test ExploreResource."""
    resource_url = u'/api/v1/sketches/1/explore/'
    expected_response = {
        u'meta': {
            u'timeline_names': {
                u'test': u'Timeline 1'
            },
            u'timeline_colors': {
                u'test': u'FFFFFF'
            },
            u'es_total_count': 1,
            u'es_time': 5
        },
        u'objects': [{
            u'sort': [1410593223000],
            u'_type': u'plaso_event',
            u'_source': {
                u'timestamp': 1410593222543942,
                u'message': u'Test event',
                u'label': [u'__ts_star'],
                u'timestamp_desc': u'Content Modification Time',
                u'datetime': u'2014-09-13T07:27:03+00:00'
            },
            u'_score': u'null',
            u'selected': False,
            u'_index': u'test',
            u'_id': u'test'
        }]
    }

    @mock.patch(u'timesketch.api.v1.resources.ElasticsearchDataStore',
                MockDataStore)
    def test_search(self):
        """Authenticated request to query the datastore."""
        self.login()
        data = dict(query=u'test', filter={})
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type=u'application/json')
        self.assertDictEqual(response.json, self.expected_response)
        self.assert200(response)


class AggregationResourceTest(BaseTest):
    """Test ExploreResource."""
    resource_url = u'/api/v1/sketches/1/aggregation/'

    @mock.patch(u'timesketch.api.v1.resources.ElasticsearchDataStore',
                MockDataStore)
    def test_heatmap_aggregation(self):
        """Authenticated request to get heatmap aggregation."""
        self.login()
        data = dict(query=u'test', filter={}, aggtype=u'heatmap')
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type=u'application/json')
        self.assert200(response)


class EventResourceTest(BaseTest):
    """Test EventResource."""
    resource_url = u'/api/v1/sketches/1/event/'
    expected_response = {
        u'objects': {
            u'timestamp_desc': u'',
            u'timestamp': 1410895419859714,
            u'label': u'',
            u'source_long': u'',
            u'source_short': u'',
            u'es_index': u'',
            u'es_id': u'',
            u'message': u'',
            u'datetime': u'2014-09-16T19:23:40+00:00'
        }
    }

    @mock.patch(u'timesketch.api.v1.resources.ElasticsearchDataStore',
                MockDataStore)
    def test_get_event(self):
        """Authenticated request to get an event from the datastore."""
        self.login()
        response = self.client.get(self.resource_url +
                                   u'?searchindex_id=test&event_id=test')
        self.assertDictContainsSubset(self.expected_response, response.json)
        self.assert200(response)

    @mock.patch(u'timesketch.api.v1.resources.ElasticsearchDataStore',
                MockDataStore)
    def test_invalid_index(self):
        """
        Authenticated request to get an event from the datastore, but in the
        wrong index.
        """
        self.login()
        response_400 = self.client.get(
            self.resource_url + u'?searchindex_id=wrong_index&event_id=test')
        self.assert400(response_400)


class EventAnnotationResourceTest(BaseTest):
    """Test EventAnnotationResource."""
    resource_url = u'/api/v1/sketches/1/event/annotate/'

    @mock.patch(u'timesketch.api.v1.resources.ElasticsearchDataStore',
                MockDataStore)
    def test_post_annotate_resource(self):
        """Authenticated request to create an annotation."""
        self.login()
        for annotation_type in [u'comment', u'label']:
            event = {
                u'_type': u'test_event',
                u'_index': u'test',
                u'_id': u'test'
            }
            data = dict(
                annotation=u'test',
                annotation_type=annotation_type,
                events=[event])
            response = self.client.post(
                self.resource_url,
                data=json.dumps(data),
                content_type=u'application/json')
            self.assertIsInstance(response.json, dict)
            self.assertEquals(response.status_code, HTTP_STATUS_CODE_CREATED)

    def test_post_annotate_invalid_index_resource(self):
        """
        Authenticated request to create an annotation, but in the wrong index.
        """
        self.login()
        data = dict(
            annotation=u'test',
            annotation_type=u'comment',
            event_id=u'test',
            searchindex_id=u'invalid_searchindex')
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type=u'application/json')
        self.assertEquals(response.status_code, HTTP_STATUS_CODE_BAD_REQUEST)


class SearchIndexResourceTest(BaseTest):
    """Test SearchIndexResource."""
    resource_url = u'/api/v1/searchindices/'

    @mock.patch(u'timesketch.api.v1.resources.ElasticsearchDataStore',
                MockDataStore)
    def test_post_create_searchindex(self):
        """Authenticated request to create a searchindex."""
        self.login()
        data = dict(
            searchindex_name=u'test3', es_index_name=u'test3', public=False)
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data),
            content_type=u'application/json')
        self.assertIsInstance(response.json, dict)
        self.assertEquals(response.status_code, HTTP_STATUS_CODE_CREATED)


class TimelineListResourceTest(BaseTest):
    """Test TimelineList resource."""
    resource_url = u'/api/v1/sketches/1/timelines/'

    def test_add_existing_timeline_resource(self):
        """Authenticated request to add a timeline to a sketch."""
        self.login()
        data = dict(timeline=1)
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type=u'application/json')
        self.assertEquals(response.status_code, HTTP_STATUS_CODE_OK)

    def test_add_new_timeline_resource(self):
        """Authenticated request to add a timeline to a sketch."""
        self.login()
        data = dict(timeline=2)
        response = self.client.post(
            self.resource_url,
            data=json.dumps(data, ensure_ascii=False),
            content_type=u'application/json')
        self.assertEquals(response.status_code, HTTP_STATUS_CODE_CREATED)
