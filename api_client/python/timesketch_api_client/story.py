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
"""Timesketch API client library."""
from __future__ import unicode_literals

import json

from . import definitions
from . import resource


class Story(resource.BaseResource):
    """Story object.

    Attributes:
        id: Primary key of the story.
    """

    def __init__(self, story_id, sketch_id, api):
        """Initializes the Story object.

        Args:
            story_id: The primary key ID of the story.
            sketch_id: ID of a sketch.
            api: Instance of a TimesketchApi object.
        """
        self.id = story_id
        self._title = ''
        self._content = ''

        resource_uri = 'sketches/{0:d}/stories/{1:d}/'.format(
            sketch_id, self.id)
        super(Story, self).__init__(api, resource_uri)

    @property
    def title(self):
        """Property that returns story title.

        Returns:
            Story name as a string.
        """
        if not self._title:
            story = self.lazyload_data()
            objects = story.get('objects')
            if objects:
                self._title = objects[0].get('title', 'No Title')
        return self._title

    @property
    def content(self):
        """Property that returns the content of a story.

        Returns:
            Story content as a list of blocks.
        """
        if not self._content:
            story = self.lazyload_data()
            objects = story.get('objects')
            if objects:
                self._content = objects[0].get('content', [])
        return self._content

    def _add_block(self, block):
        """Adds a block to the story's content."""
        self.refresh()
        content = self.content
        if content:
            content_list = json.loads(content)
        else:
            content_list = []

        content_list.append(block)
        self._content = json.dumps(content_list)

        data = {
            'title': self.title,
            'content': self._content,
        }
        response = self.api.session.post(
            '{0:s}/{1:s}'.format(self.api.api_root, self.resource_uri),
            json=data)

        return response.status_code in definitions.HTTP_STATUS_CODE_20X

    def _create_new_block(self):
        """Returns a new block dict."""
        return {
            'componentName': '',
            'componentProps': {},
            'content': '',
            'edit': False,
            'showPanel': False,
            'isActive': False
        }

    def add_text(self, text):
        """Adds a text block to the story.

        Args:
            text: the string to add to the story.

        Returns:
            Boolean that indicates whether block was successfully added.
        """
        text_block = self._create_new_block()
        text_block['content'] = text

        return self._add_block(text_block)

    def add_view(self, view):
        """Add a view to the story.

        Args:
            view: a view object (instance of view.View)

        Returns:
            Boolean that indicates whether block was successfully added.

        Raises:
            TypeError: if the view object is not of the correct type.
        """
        if not hasattr(view, 'id'):
            raise TypeError('View object is not correctly formed.')

        if not hasattr(view, 'name'):
            raise TypeError('View object is not correctly formed.')

        view_block = self._create_new_block()
        view_block['componentName'] = 'TsViewEventList'
        view_block['componentProps']['view'] = {
            'id': view.id, 'name': view.name}

        return self._add_block(view_block)

    def delete(self):
        """Delete the story from the sketch.

        Returns:
            Boolean that indicates whether the deletion was successful.
        """
        response = self.api.session.delete(
            '{0:s}/{1:s}'.format(self.api.api_root, self.resource_uri))

        return response.status_code in definitions.HTTP_STATUS_CODE_20X

    def refresh(self):
        """Refresh story content."""
        self._title = ''
        self._content = ''
        _ = self.lazyload_data(refresh_cache=True)
