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
import logging

import pandas as pd

from . import aggregation
from . import definitions
from . import resource
from . import view


logger = logging.getLogger('story_api')


class BaseBlock(object):
    """Base block object."""

    # A string representation of the type of block.
    TYPE = ''

    def __init__(self, story, index):
        """Initialize the base block."""
        self.index = index
        self._story = story

        self._data = None

    @property
    def data(self):
        """Returns the building block."""
        return self.to_dict()

    @data.setter
    def data(self, data):
        """Feeds data to the block."""
        self._data = data
        self._story.commit()

    @property
    def json(self):
        """Returns the building block."""
        return self.to_dict()

    def _get_base(self):
        """Returns a base building block."""
        return {
            'componentName': '',
            'componentProps': {},
            'content': '',
            'edit': False,
            'showPanel': False,
            'isActive': False
        }

    def delete(self):
        """Remove block from index."""
        self._story.remove_block(self.index)

    def feed(self, data):
        """Feed data into the block."""
        self._data = data

    def from_dict(self, data_dict):
        """Feed a block from a block dict."""
        raise NotImplementedError

    def move_down(self):
        """Moves a block down one location in the index."""
        new_index = self.index + 1
        self._story.move_to(self, new_index)
        self.index = new_index

    def move_up(self):
        """Moves a block up one location in the index."""
        new_index = self.index - 1
        self._story.move_to(self, new_index)
        self.index = new_index

    def to_dict(self):
        """Returns a dict with the block data.

        Raises:
            ValueError: if the block has not been fed with data.
            TypeError: if the data that was fed is of the wrong type.

        Returns:
            A dict with the block data.
        """
        raise NotImplementedError

    def reset(self):
        """Resets the data in the block."""
        self._data = None


class ViewBlock(BaseBlock):
    """Block object for views."""

    TYPE = 'view'

    def __init__(self, story, index):
        super(ViewBlock, self).__init__(story, index)
        self._view_id = 0
        self._view_name = ''

    @property
    def view(self):
        """Returns the view."""
        return self._data

    @view.setter
    def view(self, new_view):
        """Sets a new view to the block."""
        self.data = new_view

    @property
    def view_id(self):
        """Returns the view ID."""
        if self._data and hasattr(self._data, 'id'):
            return self._data.id
        return self._view_id

    @property
    def view_name(self):
        """Returns the view name."""
        if self._data and hasattr(self._data, 'name'):
            return self._data.name
        return self._view_name

    def from_dict(self, data_dict):
        """Feed a block from a block dict."""
        props = data_dict.get('componentProps', {})
        view_dict = props.get('view')
        if not view_dict:
            raise TypeError('View not defined')

        self._view_id = view_dict.get('id', 0)
        self._view_name = view_dict.get('name', '')

    def to_dict(self):
        """Returns a dict with the block data.

        Raises:
            ValueError: if the block has not been fed with data.
            TypeError: if the data that was fed is of the wrong type.

        Returns:
            A dict with the block data.
        """
        if not self._data:
            raise ValueError('No data has been fed to the block.')

        view_obj = self._data
        if not hasattr(view_obj, 'id'):
            raise TypeError('View object is not correctly formed.')

        if not hasattr(view_obj, 'name'):
            raise TypeError('View object is not correctly formed.')

        view_block = self._get_base()
        view_block['componentName'] = 'TsViewEventList'
        view_block['componentProps']['view'] = {
            'id': view_obj.id, 'name': view_obj.name}

        return view_block


class TextBlock(BaseBlock):
    """Block object for text."""

    TYPE = 'text'

    @property
    def text(self):
        """Returns the text."""
        if not self._data:
            return ''
        return self._data

    @text.setter
    def text(self, new_text):
        """Sets a new text to the block."""
        self.data = new_text

    def from_dict(self, data_dict):
        """Feed a block from a block dict."""
        text = data_dict.get('content', '')
        self.feed(text)

    def to_dict(self):
        """Returns a dict with the block data.

        Raises:
            ValueError: if the block has not been fed with data.
            TypeError: if the data that was fed is of the wrong type.

        Returns:
            A dict with the block data.
        """
        if not self._data:
            raise ValueError('No data has been fed to the block.')

        if not isinstance(self._data, str):
            raise TypeError('Data to a text block needs to be a string.')

        text_block = self._get_base()
        text_block['content'] = self._data

        return text_block


class AggregationBlock(BaseBlock):
    """Block object for aggregation."""

    TYPE = 'aggregation'

    def __init__(self, story, index):
        super(AggregationBlock, self).__init__(story, index)
        self._agg_id = 0
        self._agg_name = ''
        self._agg_type = 'table'
        self._agg_dict = {}

    @property
    def aggregation(self):
        """Returns the aggregation object."""
        if self._data:
            return self._data
        return None

    @aggregation.setter
    def aggregation(self, agg_obj):
        """Set the aggregation object."""
        self._data = agg_obj

    @property
    def agg_name(self):
        """Returns the aggregation name."""
        return self._agg_name

    @property
    def agg_id(self):
        """Returns the aggregation ID."""
        return self._agg_id

    @property
    def agg_type(self):
        """Returns the aggregation type."""
        return self._agg_type

    @agg_type.setter
    def agg_type(self, new_type):
        """Sets the aggregation type."""
        self._agg_type = new_type

    @property
    def table(self):
        """Returns a table view, as a pandas DataFrame."""
        if not self._data:
            return pd.DataFrame()
        return self._data.table

    @property
    def chart(self):
        """Returns a chart back from the aggregation."""
        if not self._data:
            return None
        return self._data.chart

    def from_dict(self, data_dict):
        """Feed a block from a block dict."""
        component = data_dict.get('componentName', 'N/A')
        if component != 'TsAggregationCompact':
            raise TypeError('Not an aggregation block.')

        props = data_dict.get('componentProps', {})
        agg_dict = props.get('aggregation')
        if not agg_dict:
            raise TypeError('Aggregation not defined')

        self._agg_id = agg_dict.get('id', 0)
        self._agg_name = agg_dict.get('name', '')
        self._agg_type = agg_dict.get('chart_type', 'table')
        self._agg_dict = agg_dict

    def to_dict(self):
        """Returns a dict with the block data.

        Raises:
            ValueError: if the block has not been fed with data.
            TypeError: if the data that was fed is of the wrong type.

        Returns:
            A dict with the block data.
        """
        if not self._data:
            raise ValueError('No data has been fed to the block.')

        aggregation_obj = self._data
        if not hasattr(aggregation_obj, 'id'):
            raise TypeError('Aggregation object is not correctly formed.')

        if not hasattr(aggregation_obj, 'name'):
            raise TypeError('Aggregation object is not correctly formed.')

        aggregation_block = self._get_base()
        aggregation_block['componentName'] = 'TsAggregationCompact'
        aggregation_block['componentProps']['aggregation'] = {
            'id': aggregation_obj.id,
            'name': aggregation_obj.name,
            'chart_type': self._agg_type,
            'agg_type': self._agg_dict.get('agg_type'),
            'description': self._agg_dict.get('description'),
            'created_at': self._agg_dict.get('created_at'),
            'updated_at': self._agg_dict.get('updated_at'),
            'parameters': self._agg_dict.get('parameters', {}),
            'user': self._agg_dict.get('user', {}),
        }

        return aggregation_block


class Story(resource.BaseResource):
    """Story object.

    Attributes:
        id: Primary key of the story.
    """

    def __init__(self, story_id, sketch, api):
        """Initializes the Story object.

        Args:
            story_id: The primary key ID of the story.
            sketch: The sketch object (instance of Sketch).
            api: Instance of a TimesketchApi object.
        """
        self.id = story_id
        self._api = api
        self._title = ''
        self._blocks = []
        self._sketch = sketch

        resource_uri = 'sketches/{0:d}/stories/{1:d}/'.format(
            sketch.id, self.id)
        super(Story, self).__init__(api, resource_uri)

    @property
    def blocks(self):
        """Returns all the blocks of the story."""
        if not self._blocks:
            story_data = self.lazyload_data()
            objects = story_data.get('objects')
            content = ''
            if objects:
                content = objects[0].get('content', [])
            index = 0
            for content_block in json.loads(content):
                name = content_block.get('componentName', '')
                if content_block.get('content'):
                    block = TextBlock(self, index)
                    block.from_dict(content_block)
                elif name == 'TsViewEventList':
                    block = ViewBlock(self, index)
                    block.from_dict(content_block)
                    view_obj = view.View(
                        block.view_id, block.view_name, self._sketch.id,
                        self._api)
                    block.feed(view_obj)
                elif name == 'TsAggregationCompact':
                    block = AggregationBlock(self, index)
                    block.from_dict(content_block)
                    agg_obj = aggregation.Aggregation(self._sketch, self._api)
                    agg_obj.from_store(block.agg_id)
                    block.feed(agg_obj)

                    # Defaults to a table view.
                    if not block.agg_type:
                        block.agg_type = 'table'
                self._blocks.append(block)
        return self._blocks

    @property
    def title(self):
        """Property that returns story title.

        Returns:
            Story name as a string.
        """
        if not self._title:
            story_data = self.lazyload_data()
            objects = story_data.get('objects')
            if objects:
                self._title = objects[0].get('title', 'No Title')
        return self._title

    @property
    def content(self):
        """Property that returns the content of a story.

        Returns:
            Story content as a list of blocks.
        """
        content_list = [x.to_dict() for x in self.blocks]
        return json.dumps(content_list)

    @property
    def size(self):
        """Retiurns the number of blocks stored in the story."""
        return len(self._blocks)

    def __len__(self):
        """Returns the number of blocks stored in the story."""
        _ = self.blocks
        return len(self._blocks)

    def _add_block(self, block, index):
        """Adds a block to the story's content."""
        self._blocks.insert(index, block)
        self.commit()
        self.reset()

    def add_aggregation(self, agg_obj, agg_type='table', index=-1):
        """Adds an aggregation object to the story.

        Args:
            agg_obj: an aggregation object (instance of aggregation.Aggregation)
            agg_type (str): string indicating the type of aggregation, can be:
                "table" or the name of the chart to be used, eg "barcharct",
                "hbarchart". Defaults to "table".
            index: an integer, if supplied determines where the new
                block will be added. If not supplied it will be
                appended at the end.

        Returns:
            Boolean that indicates whether block was successfully added.

        Raises:
            TypeError: if the view object is not of the correct type.
        """
        if not hasattr(agg_obj, 'id'):
            raise TypeError('Aggregation object is not correctly formed.')

        if not hasattr(agg_obj, 'name'):
            raise TypeError('Aggregation object is not correctly formed.')

        if index == -1:
            index = len(self._blocks)

        agg_block = AggregationBlock(self, index)
        agg_block.feed(agg_obj)
        agg_block.agg_type = agg_type

        return self._add_block(agg_block, index)

    def add_text(self, text, index=-1):
        """Adds a text block to the story.

        Args:
            text: the string to add to the story.
            index: an integer, if supplied determines where the new
                block will be added. If not supplied it will be
                appended at the end.

        Returns:
            Boolean that indicates whether block was successfully added.
        """
        if index == -1:
            index = len(self._blocks)
        text_block = TextBlock(self, index)
        text_block.feed(text)

        return self._add_block(text_block, index)

    def add_view(self, view_obj, index=-1):
        """Add a view to the story.

        Args:
            view_obj: a view object (instance of view.View)
            index: an integer, if supplied determines where the new
                block will be added. If not supplied it will be
                appended at the end.

        Returns:
            Boolean that indicates whether block was successfully added.

        Raises:
            TypeError: if the view object is not of the correct type.
        """
        if not hasattr(view_obj, 'id'):
            raise TypeError('View object is not correctly formed.')

        if not hasattr(view_obj, 'name'):
            raise TypeError('View object is not correctly formed.')

        if index == -1:
            index = len(self._blocks)

        view_block = ViewBlock(self, index)
        view_block.feed(view_obj)

        return self._add_block(view_block, index)

    def commit(self):
        """Commit the story to the server."""
        content_list = [x.to_dict() for x in self._blocks]
        content = json.dumps(content_list)

        data = {
            'title': self.title,
            'content': content,
        }
        response = self._api.session.post(
            '{0:s}/{1:s}'.format(self._api.api_root, self.resource_uri),
            json=data)

        return response.status_code in definitions.HTTP_STATUS_CODE_20X

    def delete(self):
        """Delete the story from the sketch.

        Returns:
            Boolean that indicates whether the deletion was successful.
        """
        response = self._api.session.delete(
            '{0:s}/{1:s}'.format(self._api.api_root, self.resource_uri))

        return response.status_code in definitions.HTTP_STATUS_CODE_20X

    def move_to(self, block, new_index):
        """Moves a block from one index to another."""
        if new_index < 0:
            return
        old_index = block.index
        old_block = self._blocks.pop(old_index)
        if old_block.data != block.data:
            raise ValueError('Block is not correctly set.')
        self._blocks.insert(new_index, block)
        self.commit()

    def remove_block(self, index):
        """Removes a block from the story."""
        _ = self._blocks.pop(index)
        self.commit()
        self.reset()

    def reset(self):
        """Refresh story content."""
        self._title = ''
        self._blocks = []
        _ = self.lazyload_data(refresh_cache=True)
        _ = self.blocks

    def to_markdown(self):
        """Return a markdown formatted string with the content of the story."""
        story_dict = self.to_export_format('markdown')
        return story_dict.get('story', '')

    def to_export_format(self, export_format):
        """Returns exported copy of the story as defined in export_format."""
        resource_url = '{0:s}/sketches/{1:d}/stories/{2:d}/'.format(
            self._api.api_root, self._sketch.id, self.id)

        data = {
            'export_format': export_format
        }
        response = self._api.session.post(resource_url, json=data)

        if response.status_code in definitions.HTTP_STATUS_CODE_20X:
            return response.json()

        logger.error(
            'Error exporting story: [{0:d}] {1!s} {2!s}'.format(
                response.status_code, response.reason, response.text))
        return ''

    def to_string(self):
        """Returns a string with the content of all the story."""
        self.reset()
        string_list = []
        for block in self.blocks:
            if block.TYPE == 'text':
                string_list.append(block.text)
            elif block.TYPE == 'view':
                data_frame = self._sketch.explore(
                    view=block.view, as_pandas=True)
                string_list.append(data_frame.to_string(index=False))
            elif block.TYPE == 'aggregation':
                agg_obj = self._sketch.get_aggregation(block.agg_id)
                # TODO: Support charts.
                data_frame = agg_obj.table
                string_list.append(data_frame.to_string(index=False))
        return '\n\n'.join(string_list)
