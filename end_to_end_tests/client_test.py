# Copyright 2020 Google Inc. All rights reserved.
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
"""End to end tests of Timesketch client functionality."""

from timesketch_api_client import search

from . import interface
from . import manager


class ClientTest(interface.BaseEndToEndTest):
    """End to end tests for client functionality."""

    NAME = 'client_test'

    def test_client(self):
        """Client tests."""
        expected_user = 'test'
        user = self.api.current_user
        self.assertions.assertEqual(user.username, expected_user)
        self.assertions.assertEqual(user.is_admin, False)
        self.assertions.assertEqual(user.is_active, True)

        sketches = list(self.api.list_sketches())
        number_of_sketches = len(sketches)

        sketch_name = 'Testing'
        sketch_description = 'This is truly a foobar'
        new_sketch = self.api.create_sketch(
            name=sketch_name, description=sketch_description)

        self.assertions.assertEqual(new_sketch.name, sketch_name)
        self.assertions.assertEqual(
            new_sketch.description, sketch_description)

        sketches = list(self.api.list_sketches())
        self.assertions.assertEqual(len(sketches), number_of_sketches + 1)

        for index in self.api.list_searchindices():
            self.assertions.assertTrue(bool(index.name))


    def test_sigma_list(self):
        """Client Sigma list tests."""
        
        rules = self.api.list_sigma_rules()
        self.assertions.assertGreaterEqual(len(rules), 1)
        rule = rules[0]
        self.assertions.assertEqual(
            rule.id, '5266a592-b793-11ea-b3de-0242ac130004')
        self.assertions.assertEqual(
            rule.rule_uuid, '5266a592-b793-11ea-b3de-0242ac130004')
        self.assertions.assertEqual(
            rule.title, 'Suspicious Installation of Zenmap')
        self.assertions.assertIn('zmap', rule.es_query, 'ES_Query does not match')
        self.assertions.assertIn('b793', rule.id)
        self.assertions.assertIn('Alexander', rule.author)
        self.assertions.assertIn('2020/06/26',rule.date)
        self.assertions.assertIn('installation of Zenmap', rule.description)
        self.assertions.assertEqual(len(rule.detection), 2)
        self.assertions.assertIn('zmap*', rule.es_query)
        self.assertions.assertIn('Unknown', rule.falsepositives[0])
        self.assertions.assertEqual(len(rule.logsource), 2)
        self.assertions.assertIn('2020/06/26', rule.modified)
        self.assertions.assertIn('lnx_susp_zenmap.yml', rule.file_relpath)
        self.assertions.assertIn('lnx_susp_zenmap', rule.file_name)
        self.assertions.assertIn('high', rule.level)
        self.assertions.assertIn('rmusser.net', rule.references[0])

    def test_get_sigma_rule(self):
        rule = self.api.get_sigma_rule(
            rule_uuid='5266a592-b793-11ea-b3de-0242ac130004')
        rule.from_rule_uuid('5266a592-b793-11ea-b3de-0242ac130004')
        self.assertions.assertGreater(len(rule.attributes),5)
        self.assertions.assertIsNotNone(rule)
        self.assertions.assertIn('Alexander', rule.author)
        self.assertions.assertIn('Alexander', rule.get_attribute('author'))
        self.assertions.assertEqual(rule.id, '5266a592-b793-11ea-b3de-0242ac130004')
        self.assertions.assertEqual(rule.title, 'Suspicious Installation of Zenmap')
        self.assertions.assertIn('zmap', rule.es_query, 'ES_Query does not match')
        self.assertions.assertIn('b793', rule.id)
        self.assertions.assertIn('lnx_susp_zenmap.yml', rule.file_relpath)
        self.assertions.assertIn('sigma/rule/5266a592', rule.resource_uri)
        self.assertions.assertIn('suspicious installation of Zenmap', rule.description)
        self.assertions.assertIn('high', rule.level)
        self.assertions.assertEqual(len(rule.falsepositives), 1)
        self.assertions.assertIn('Unknown', rule.falsepositives[0])
        self.assertions.assertIn('susp_zenmap', rule.file_name)
        self.assertions.assertIn('2020/06/26', rule.date)
        self.assertions.assertIn('2020/06/26', rule.modified)
        self.assertions.assertIn('high', rule.level)
        self.assertions.assertIn('rmusser.net', rule.references[0])
        self.assertions.assertEqual(len(rule.detection), 2)
        self.assertions.assertEqual(len(rule.logsource), 2)

        # Test an actual query

        self.import_timeline('sigma_events.csv')
        search_obj = search.Search(self.sketch)
        search_obj.query_string = rule.es_query
        data_frame = search_obj.table
        count = len(data_frame)
        self.assertions.assertEqual(count, 1)


manager.EndToEndTestManager.register_test(ClientTest)
