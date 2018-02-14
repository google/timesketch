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
"""Tests for the sketch views."""

from timesketch.lib.testlib import BaseTest


class SketchViewTest(BaseTest):
    """Test the sketch view."""
    # TODO: Test POST
    resource_url = u'/sketch/1/'

    def test_sketch_view(self):
        """Test the view handler."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assert200(response)
        self.assert_template_used(u'sketch/overview.html')


class TimelinesViewTest(BaseTest):
    """Test the timelines view."""
    # TODO: Test POST
    resource_url = u'/sketch/1/timelines/'

    def test_timelines_list_view(self):
        """Test the view handler."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assert200(response)
        self.assert_template_used(u'sketch/timelines.html')


class TimelineViewTest(BaseTest):
    """Test the timeline view."""
    resource_url = u'/sketch/1/timelines/1/'

    def test_timeline_view(self):
        """Test the view handler."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assert200(response)
        self.assert_template_used(u'sketch/timeline.html')


class ViewTest(BaseTest):
    """Test the view view."""
    # TODO: Test POST
    resource_url = u'/sketch/1/views/'

    def test_view_list_view(self):
        """Test the view handler."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assert200(response)
        self.assert_template_used(u'sketch/views.html')


class StoryViewTest(BaseTest):
    """Test the story view."""
    resource_url = u'/sketch/1/stories/'

    def test_stories_view(self):
        """Test the view handler."""
        self.login()
        response = self.client.get(self.resource_url)
        self.assert200(response)
        self.assert_template_used(u'sketch/stories.html')
