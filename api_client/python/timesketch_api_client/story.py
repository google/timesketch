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

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Union

import pandas as pd

from . import aggregation
from . import error
from . import resource
from . import search

if TYPE_CHECKING:
    from .client import TimesketchApi
    from .sketch import Sketch
    from .view import View

logger = logging.getLogger("timesketch_api.story")


class BaseBlock:
    """Base block object."""

    # A string representation of the type of block.
    TYPE = ""

    def __init__(self, story: Story, index: int) -> None:
        """Initialize the base block.

        Args:
            story (Story): Story object.
            index (int): Index of the block.
        """
        self.index = index
        self._story = story

        self._data: Any = None

    @property
    def data(self) -> Union[Dict[str, Any], str, List[Any], None]:
        """Returns the building block."""
        return self.to_dict()

    @data.setter
    def data(self, data: Any) -> None:
        """Feeds data to the block.

        Args:
            data (str): Data to feed to the block.
        """
        self._data = data
        self._story.commit()

    @property
    def json(self) -> Union[Dict[str, Any], str, List[Any], None]:
        """Returns the building block."""
        return self.to_dict()

    def _get_base(self) -> Dict[str, Any]:
        """Returns a base building block."""
        return {
            "componentName": "",
            "componentProps": {},
            "content": "",
            "edit": False,
            "showPanel": False,
            "isActive": False,
        }

    def delete(self) -> None:
        """Remove block from index."""
        self._story.remove_block(self.index)

    def feed(self, data: Any) -> None:
        """Feed data into the block.

        Args:
            data (list): Data to feed into the block.
        """
        self._data = data

    def from_dict(self, data_dict: Dict[str, Any]) -> None:
        """Feed a block from a block dict.

        Args:
            data_dict (dict): Dictionary with block data.
        """
        raise NotImplementedError

    def move_down(self) -> None:
        """Moves a block down one location in the index."""
        new_index = self.index + 1
        self._story.move_to(self, new_index)
        self.index = new_index

    def move_up(self) -> None:
        """Moves a block up one location in the index."""
        new_index = self.index - 1
        self._story.move_to(self, new_index)
        self.index = new_index

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dict with the block data.

        Raises:
            ValueError: if the block has not been fed with data.
            TypeError: if the data that was fed is of the wrong type.

        Returns:
            A dict with the block data.
        """
        raise NotImplementedError

    def reset(self) -> None:
        """Resets the data in the block."""
        self._data = None


class ViewBlock(BaseBlock):
    """Block object for views."""

    TYPE = "view"

    def __init__(self, story: Story, index: int) -> None:
        """Initialize the view block.

        Args:
            story (Story): Story object.
            index (int): Index of the block.
        """
        super().__init__(story, index)
        self._view_id = 0
        self._view_name = ""

    @property
    def view(self) -> Any:
        """Returns the view."""
        return self._data

    @view.setter
    def view(self, new_view: View) -> None:
        """Sets a new view to the block.

        Args:
            new_view (View): View object.
        """
        self.data = new_view

    @property
    def view_id(self) -> int:
        """Returns the view ID."""
        if self._data and hasattr(self._data, "id"):
            return int(self._data.id)
        return self._view_id

    @property
    def view_name(self) -> str:
        """Returns the view name."""
        if self._data and hasattr(self._data, "name"):
            return str(self._data.name)
        return self._view_name

    def from_dict(self, data_dict: Dict[str, Any]) -> None:
        """Feed a block from a block dict.

        Args:
            data_dict (dict): Dictionary with block data.
        """
        props = data_dict.get("componentProps", {})
        view_dict = props.get("view")
        if not view_dict:
            raise TypeError("View not defined")

        self._view_id = view_dict.get("id", 0)
        self._view_name = view_dict.get("name", "")

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dict with the block data.

        Raises:
            ValueError: if the block has not been fed with data.
            TypeError: if the data that was fed is of the wrong type.

        Returns:
            A dict with the block data.
        """
        if not self._data:
            raise ValueError("No data has been fed to the block.")

        view_obj = self._data
        if not hasattr(view_obj, "id"):
            raise TypeError("View object is not correctly formed.")

        if not hasattr(view_obj, "name"):
            raise TypeError("View object is not correctly formed.")

        view_block = self._get_base()
        view_block["componentName"] = "TsViewEventList"
        view_block["componentProps"]["view"] = {
            "id": view_obj.id,
            "name": view_obj.name,
        }

        return view_block


class TextBlock(BaseBlock):
    """Block object for text."""

    TYPE = "text"

    @property
    def text(self) -> str:
        """Returns the text."""
        if not self._data:
            return ""
        return str(self._data)

    @text.setter
    def text(self, new_text: str) -> None:
        """Sets a new text to the block.

        Args:
            new_text (str): New text to set.
        """
        self.data = new_text

    def from_dict(self, data_dict: Dict[str, Any]) -> None:
        """Feed a block from a block dict.

        Args:
            data_dict (dict): Dictionary with block data.
        """
        text = data_dict.get("content", "")
        self.feed(text)

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dict with the block data.

        Raises:
            ValueError: if the block has not been fed with data.
            TypeError: if the data that was fed is of the wrong type.

        Returns:
            A dict with the block data.
        """
        if not self._data:
            raise ValueError("No data has been fed to the block.")

        if not isinstance(self._data, str):
            raise TypeError("Data to a text block needs to be a string.")

        text_block = self._get_base()
        text_block["content"] = self._data

        return text_block


class AggregationBlock(BaseBlock):
    """Block object for aggregation."""

    TYPE = "aggregation"

    def __init__(self, story: Story, index: int) -> None:
        """Initialize the aggregation block.

        Args:
            story (Story): Story object.
            index (int): Index of the block.
        """
        super().__init__(story, index)
        self._agg_id = 0
        self._agg_name = ""
        self._agg_dict: Dict[str, Any] = {}
        self._chart_type = "table"

    @property
    def aggregation(self) -> Optional[aggregation.Aggregation]:
        """Returns the aggregation object."""
        if self._data:
            return self._data
        return None

    @aggregation.setter
    def aggregation(self, agg_obj: aggregation.Aggregation) -> None:
        """Set the aggregation object.

        Args:
            agg_obj (Aggregation): Aggregation object.
        """
        self._data = agg_obj

    @property
    def agg_name(self) -> str:
        """Returns the aggregation name."""
        return self._agg_name

    @property
    def agg_id(self) -> int:
        """Returns the aggregation ID."""
        return self._agg_id

    @property
    def chart_type(self) -> str:
        """Returns the aggregation type."""
        return self._chart_type

    @chart_type.setter
    def chart_type(self, new_type: str) -> None:
        """Sets the aggregation type.

        Args:
            new_type (str): Type of the chart.
        """
        self._chart_type = new_type

    @property
    def table(self) -> pd.DataFrame:
        """Returns a table view, as a pandas DataFrame."""
        if not self._data:
            return pd.DataFrame()
        return self._data.table

    @property
    def chart(self) -> Any:
        """Returns a chart back from the aggregation."""
        if not self._data:
            return None
        return self._data.chart

    def from_dict(self, data_dict: Dict[str, Any]) -> None:
        """Feed a block from a block dict.

        Args:
            data_dict (dict): Dictionary with block data.
        """
        component = data_dict.get("componentName", "N/A")
        if component != "TsAggregationCompact":
            raise TypeError("Not an aggregation block.")

        props = data_dict.get("componentProps", {})
        agg_dict = props.get("aggregation")
        if not agg_dict:
            raise TypeError("Aggregation not defined")

        self._agg_id = agg_dict.get("id", 0)
        self._agg_name = agg_dict.get("name", "")
        self._chart_type = agg_dict.get("chart_type", "table")
        self._agg_dict = agg_dict

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dict with the block data.

        Raises:
            ValueError: if the block has not been fed with data.
            TypeError: if the data that was fed is of the wrong type.

        Returns:
            A dict with the block data.
        """
        if not (self._data or self._agg_dict):
            raise ValueError("No data has been fed to the block.")

        aggregation_obj = self._data
        if aggregation_obj:
            if not hasattr(aggregation_obj, "id"):
                raise TypeError("Aggregation object is not correctly formed.")

            if not hasattr(aggregation_obj, "name"):
                raise TypeError("Aggregation object is not correctly formed.")

            name = aggregation_obj.name
            description = aggregation_obj.description
            agg_id = aggregation_obj.id
            agg_type = aggregation_obj.aggregator_name
            created_at = aggregation_obj.created_at
            updated_at = aggregation_obj.updated_at
            parameters = json.dumps(aggregation_obj.parameters)
            user = aggregation_obj.user
        else:
            name = self._agg_name
            description = self._agg_dict.get("description", "")
            agg_id = self._agg_id
            agg_type = self._agg_dict.get("agg_type")
            created_at = self._agg_dict.get("created_at")
            updated_at = self._agg_dict.get("updated_at")
            parameters = self._agg_dict.get("parameters", "{}")
            user = self._agg_dict.get("user", {})

        aggregation_block = self._get_base()
        aggregation_block["componentName"] = "TsAggregationCompact"
        aggregation_block["componentProps"]["aggregation"] = {
            "id": agg_id,
            "name": name,
            "chart_type": self.chart_type,
            "agg_type": agg_type,
            "description": description,
            "created_at": created_at,
            "updated_at": updated_at,
            "parameters": parameters,
            "user": user,
        }

        return aggregation_block


class AggregationGroupBlock(BaseBlock):
    """Block object for aggregation groups."""

    TYPE = "aggregation_group"

    def __init__(self, story: Story, index: int) -> None:
        """Initialize the aggregation group block.

        Args:
            story (Story): Story object.
            index (int): Index of the block.
        """
        super().__init__(story, index)
        self._group_id = 0
        self._group_name = ""

    @property
    def group(self) -> Optional[aggregation.AggregationGroup]:
        """Returns the aggregation group object."""
        if self._data:
            return self._data
        return None

    @group.setter
    def group(self, group_obj: aggregation.AggregationGroup) -> None:
        """Set the aggregation group object.

        Args:
            group_obj (AggregationGroup): AggregationGroup object.
        """
        self._data = group_obj

    @property
    def group_name(self) -> str:
        """Returns the aggregation group name."""
        return self._group_name

    @property
    def group_id(self) -> int:
        """Returns the aggregation group ID."""
        return self._group_id

    @property
    def table(self) -> pd.DataFrame:
        """Returns a table view, as a pandas DataFrame."""
        if not self._data:
            return pd.DataFrame()
        return self._data.table

    @property
    def chart(self) -> Any:
        """Returns a chart back from the aggregation."""
        if not self._data:
            return None
        return self._data.chart

    def from_dict(self, data_dict: Dict[str, Any]) -> None:
        """Feed a block from a block dict.

        Args:
            data_dict (dict): Dictionary with block data.
        """
        component = data_dict.get("componentName", "N/A")
        if component != "TsAggregationGroupCompact":
            raise TypeError("Not an aggregation group block.")

        props = data_dict.get("componentProps", {})
        group_dict = props.get("aggregation_group")
        if not group_dict:
            raise TypeError("Aggregation group not defined")

        self._group_id = group_dict.get("id", 0)
        self._group_name = group_dict.get("name", "")

    def to_dict(self) -> Dict[str, Any]:
        """Returns a dict with the block data.

        Raises:
            ValueError: if the block has not been fed with data.
            TypeError: if the data that was fed is of the wrong type.

        Returns:
            A dict with the block data.
        """
        if not self._data:
            raise ValueError("No data has been fed to the block.")

        group_obj = self._data
        if not hasattr(group_obj, "id"):
            raise TypeError("Aggregation group object is not correctly formed.")

        if not hasattr(group_obj, "aggregations"):
            raise TypeError("Aggregation group object is not correctly formed.")

        group_block = self._get_base()
        group_block["componentName"] = "TsAggregationGroupCompact"
        group_block["componentProps"]["aggregation_group"] = {
            "id": group_obj.id,
            "name": group_obj.name,
        }

        return group_block


class Story(resource.BaseResource):
    """Story object.

    Attributes:
        id: Primary key of the story.
    """

    def __init__(self, story_id: int, sketch: Sketch, api: TimesketchApi) -> None:
        """Initializes the Story object.

        Args:
            story_id (int): The primary key ID of the story.
            sketch (Sketch): The sketch object (instance of Sketch).
            api: Instance of a TimesketchApi object.
        """
        self.id = story_id
        self._api = api
        self._title = ""
        self._blocks: List[BaseBlock] = []
        self._sketch = sketch

        resource_uri = "sketches/{0:d}/stories/{1:d}/".format(sketch.id, self.id)
        super().__init__(api, resource_uri)

    @property
    def blocks(self) -> List[BaseBlock]:
        """Returns all the blocks of the story."""
        if not self._blocks:
            story_data = self.lazyload_data(refresh_cache=True)
            objects = story_data.get("objects")
            content = ""
            if objects:
                content = objects[0].get("content", "[]")
            index = 0
            for content_block in json.loads(content):
                name = content_block.get("componentName", "")
                if content_block.get("content"):
                    block: BaseBlock = TextBlock(self, index)
                    block.from_dict(content_block)
                elif name == "TsViewEventList":
                    block = ViewBlock(self, index)
                    block.from_dict(content_block)
                    search_obj = search.Search(sketch=self._sketch)
                    search_obj.from_saved(block.view_id)
                    block.feed(search_obj)
                elif name == "TsAggregationCompact":
                    block = AggregationBlock(self, index)
                    block.from_dict(content_block)
                    agg_obj = aggregation.Aggregation(self._sketch)
                    agg_obj.from_saved(block.agg_id)
                    block.feed(agg_obj)

                    # Defaults to a table view.
                    if not block.chart_type:
                        block.chart_type = "table"
                elif name == "TsAggregationGroupCompact":
                    block = AggregationGroupBlock(self, index)
                    block.from_dict(content_block)
                    group_obj = aggregation.AggregationGroup(self._sketch)
                    group_obj.from_saved(block.group_id)
                    block.feed(group_obj)
                else:
                    continue

                self._blocks.append(block)
                index += 1
        return self._blocks

    @property
    def title(self) -> str:
        """Property that returns story title.

        Returns:
            Story name as a string.
        """
        if not self._title:
            story_data = self.lazyload_data()
            objects = story_data.get("objects")
            if objects:
                self._title = objects[0].get("title", "No Title")
        return self._title

    @property
    def content(self) -> str:
        """Property that returns the content of a story.

        Returns:
            Story content as a list of blocks.
        """
        content_list = [x.to_dict() for x in self.blocks]
        return json.dumps(content_list)

    @property
    def size(self) -> int:
        """Retiurns the number of blocks stored in the story."""
        return len(self._blocks)

    def __len__(self) -> int:
        """Returns the number of blocks stored in the story."""
        _ = self.blocks
        return len(self._blocks)

    def _add_block(self, block: BaseBlock, index: int) -> bool:
        """Adds a block to the story's content.

        Args:
            block (StoryBlock): Story block object.
            index (int): Index to add the block at.
        """
        self._blocks.insert(index, block)
        self.commit()
        self.reset()
        return True

    def add_aggregation(
        self,
        agg_obj: aggregation.Aggregation,
        chart_type: str = "table",
        index: int = -1,
    ) -> bool:
        """Adds an aggregation object to the story.

        Args:
            agg_obj (aggregation.Aggregation): an aggregation object
            chart_type (str): string indicating the type of aggregation, can be:
                "table" or the name of the chart to be used, eg "barcharct",
                "hbarchart". Defaults to "table".
            index (int): an integer, if supplied determines where the new
                block will be added. If not supplied it will be
                appended at the end.

        Returns:
            Boolean that indicates whether block was successfully added.

        Raises:
            TypeError: if the aggregation object is not of the correct type.
        """
        if not hasattr(agg_obj, "id"):
            raise TypeError("Aggregation object is not correctly formed.")

        if not hasattr(agg_obj, "name"):
            raise TypeError("Aggregation object is not correctly formed.")

        if index == -1:
            index = len(self._blocks)

        agg_block = AggregationBlock(self, index)
        agg_block.feed(agg_obj)
        agg_block.chart_type = chart_type

        return self._add_block(agg_block, index)

    def add_text(self, text: str, index: int = -1) -> bool:
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

    def add_view(self, view_obj: Any, index: int = -1) -> bool:
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
        return self.add_saved_search(view_obj, index)

    def add_saved_search(self, search_obj: search.Search, index: int = -1) -> bool:
        """Add a saved search to the story.

        Args:
            search_obj (search.Search): a search object
            index (int): an integer, if supplied determines where the new
                block will be added. If not supplied it will be
                appended at the end.

        Returns:
            Boolean that indicates whether block was successfully added.

        Raises:
            TypeError: if the search object is not of the correct type.
        """
        if not hasattr(search_obj, "id"):
            raise TypeError("View object is not correctly formed.")

        if not hasattr(search_obj, "name"):
            raise TypeError("View object is not correctly formed.")

        if index == -1:
            index = len(self._blocks)

        view_block = ViewBlock(self, index)
        view_block.feed(search_obj)

        return self._add_block(view_block, index)

    def commit(self) -> bool:
        """Commit the story to the server."""
        content_list = [x.to_dict() for x in self._blocks]
        content = json.dumps(content_list)

        data = {
            "title": self.title,
            "content": content,
        }
        response = self._api.session.post(
            "{0:s}/{1:s}".format(self._api.api_root, self.resource_uri), json=data
        )

        return error.check_return_status(response, logger)

    def delete(self) -> bool:
        """Delete the story from the sketch.

        Returns:
            Boolean that indicates whether the deletion was successful.
        """
        response = self._api.session.delete(
            "{0:s}/{1:s}".format(self._api.api_root, self.resource_uri)
        )

        return error.check_return_status(response, logger)

    def move_to(self, block: BaseBlock, new_index: int) -> None:
        """Moves a block from one index to another.

        Args:
            block (StoryBlock): Story block object.
            new_index (int): Index to move the block to.
        """
        if new_index < 0:
            return
        old_index = block.index
        old_block = self._blocks.pop(old_index)
        if old_block.data != block.data:
            raise ValueError("Block is not correctly set.")
        self._blocks.insert(new_index, block)
        self.commit()

    def remove_block(self, index: int) -> None:
        """Removes a block from the story.

        Args:
            index (int): Index of the block to remove.
        """
        _ = self._blocks.pop(index)
        self.commit()
        self.reset()

    def reset(self) -> None:
        """Refresh story content."""
        self._title = ""
        self._blocks = []
        _ = self.lazyload_data(refresh_cache=True)
        _ = self.blocks

    def to_html(self) -> str:
        """Returns HTML formatted string with the content of the story."""
        story_dict = self.to_export_format("html")
        return str(story_dict.get("story", ""))

    def to_markdown(self) -> str:
        """Returns markdown formatted string with the content of the story."""
        story_dict = self.to_export_format("markdown")
        return str(story_dict.get("story", ""))

    def to_export_format(self, export_format: str) -> Dict[str, Any]:
        """Returns exported copy of the story as defined in export_format.

        Args:
            export_format (str): The format to export the story as.
        """
        resource_url = "{0:s}/sketches/{1:d}/stories/{2:d}/".format(
            self._api.api_root, self._sketch.id, self.id
        )

        data = {"export_format": export_format}
        response = self._api.session.post(resource_url, json=data)

        return error.get_response_json(response, logger)

    def to_string(self) -> str:
        """Returns a string with the content of all the story."""
        self.reset()
        string_list: List[str] = []
        for block in self.blocks:
            if block.TYPE == "text":
                string_list.append(str(block.data))
            elif block.TYPE == "view":
                # Type casting for search_obj as it is expected to be search.Search
                search_obj: Optional[search.Search] = block.view
                if search_obj is None:
                    logging.warning("Block has no view. Skipping")
                    continue
                data_frame = search_obj.to_pandas()
                string_list.append(data_frame.to_string(index=False))
            elif block.TYPE == "aggregation":
                agg_obj = self._sketch.get_aggregation(block.agg_id)
                # TODO: Support charts.
                data_frame = agg_obj.table
                string_list.append(data_frame.to_string(index=False))
        return "\n\n".join(string_list)
