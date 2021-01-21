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
"""Timesketch API search object."""
import datetime
import json
import logging

import pandas

from . import error
from . import resource


logger = logging.getLogger('timesketch_api.search')


class Chip:
    """Class definition for a query filter chip."""

    # The type of a chip that is defiend.
    CHIP_TYPE = ''

    # The chip value defines what property or attribute of the
    # chip class will be used to generate the chip value.
    CHIP_VALUE = ''

    # The value of the chip field.
    CHIP_FIELD = ''

    def __init__(self):
        """Initialize the chip."""
        self._active = True
        self._operator = 'must'
        self._chip_field = self.CHIP_FIELD

    @property
    def active(self):
        """A property that returns whether the chip is active or not."""
        return self._active

    @active.setter
    def active(self, active):
        """Decide whether the chip is active or disabled."""
        self._active = bool(active)

    @property
    def chip(self):
        """A property that returns the chip value."""
        return {
            'field': self._chip_field,
            'type': self.CHIP_TYPE,
            'operator': self._operator,
            'active': self._active,
            'value': getattr(self, self.CHIP_VALUE, ''),
        }

    def from_dict(self, chip_dict):
        """Configure the chip from a dictionary."""
        raise NotImplementedError

    def set_include(self):
        """Configure the chip so the content needs to be included in results."""
        self._operator = 'must'

    def set_exclude(self):
        """Configure the chip so content needs to be excluded in results."""
        self._operator = 'must_not'

    def set_optional(self):
        """Configure the chip so the content is optional in results."""
        self._operator = 'should'

    def set_active(self):
        """Set the chip as active."""
        self._active = True

    def set_disable(self):
        """Disable the chip."""
        self._active = False


class DateIntervalChip(Chip):
    """A date interval chip."""

    CHIP_TYPE = 'datetime_interval'
    CHIP_VALUE = 'interval'

    _DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

    def __init__(self):
        """Initialize the chip."""
        super().__init__()
        self._date = None
        self._before = 5
        self._after = 5
        self._unit = 'm'

    def add_interval(self, before, after=None, unit='m'):
        """Set the interval of the chip.

        Args:
            before (int): the number of units that should be included
                before the date.
            after (int): optional number of units after the date. If not
                provided the value of before is used.
            unit (str): optional string with the unit of interval. This can
                be s for seconds, m for minutes, d for days and h for hours.
                The default value is m (minutes).

        Raises:
            ValueError if the unit is not correctly formed.
        """
        if after is None:
            after = before

        self.unit = unit

        self._before = before
        self._after = after

    @property
    def after(self):
        """Property that returns the time interval after the date."""
        return self._after

    @after.setter
    def after(self, after):
        """Make changes to the time interval after the date."""
        self._after = after

    @property
    def before(self):
        """Property that returns the time interval before the date."""
        return self._before

    @before.setter
    def before(self, before):
        """Make changes to the time interval before the date."""
        self._before = before

    @property
    def date(self):
        """Property that returns back the date."""
        if not self._date:
            return ''
        return self._date.strftime(self._DATE_FORMAT)

    @date.setter
    def date(self, date):
        """Make changes to the date."""
        try:
            dt = datetime.datetime.strptime(date, self._DATE_FORMAT)
        except ValueError as exc:
            logger.error(
                'Unable to add date chip, wrong date format', exc_info=True)
            raise ValueError('Wrong date format') from exc
        self._date = dt

    def from_dict(self, chip_dict):
        """Configure the chip from a dictionary."""
        value = chip_dict.get('value')
        if not value:
            return
        date, before, after = value.split()
        self.unit = before[-1]
        self.date = date
        self.before = int(before[1:-1])
        self.after = int(after[1:-1])

    @property
    def interval(self):
        """A property that returns back the full interval."""
        return (
            f'{self.date} -{self.before}{self.unit} +{self.after}{self.unit}')

    @property
    def unit(self):
        """Property that returns back the unit used."""
        return self._unit

    @unit.setter
    def unit(self, unit):
        """Make changes to the unit."""
        if unit not in ('s', 'm', 'd', 'h'):
            raise ValueError(
                'Unable to add interval, needs to be one of: '
                's (seconds), m (minutes), h (hours) or d (days)')
        self._unit = unit


class DateRangeChip(Chip):
    """A date range chip."""

    CHIP_TYPE = 'datetime_range'
    CHIP_VALUE = 'date_range'

    _DATE_FORMAT = '%Y-%m-%dT%H:%M:%S'

    def __init__(self):
        """Initialize the date range."""
        super().__init__()
        self._start_date = None
        self._end_date = None

    def add_end_time(self, end_time):
        """Add an end time to the range.

        Args:
            end_time (str): date string using the format '%Y-%m-%dT%H:%M:%s'

        Raises:
            ValueError: if the date format is incorrectly formatted.
        """
        try:
            dt = datetime.datetime.strptime(end_time, self._DATE_FORMAT)
        except ValueError as exc:
            logger.error(
                'Unable to add date chip, wrong date format', exc_info=True)
            raise ValueError('Wrong date format') from exc
        self._end_date = dt

    def add_start_time(self, start_time):
        """Add a start time to the range.

        Args:
            start_time (str): date string using the format '%Y-%m-%dT%H:%M:%s'

        Raises:
            ValueError: if the date format is incorrectly formatted.
        """
        try:
            dt = datetime.datetime.strptime(start_time, self._DATE_FORMAT)
        except ValueError as exc:
            logger.error(
                'Unable to add date chip, wrong date format', exc_info=True)
            raise ValueError('Wrong date format') from exc
        self._start_date = dt

    @property
    def end_time(self):
        """Property that returns the end time of a range."""
        if not self._end_date:
            return ''
        return self._end_date.strftime(self._DATE_FORMAT)

    @end_time.setter
    def end_time(self, end_time):
        """Sets the new end time."""
        self.add_end_time(end_time)

    @property
    def date_range(self):
        """Property that returns back the range."""
        return f'{self.start_time},{self.end_time}'

    @date_range.setter
    def date_range(self, date_range):
        """Sets the new range of the date range chip."""
        start_time, end_time = date_range.split(',')
        self.add_start_time(start_time)
        self.add_end_time(end_time)

    def from_dict(self, chip_dict):
        """Configure the chip from a dictionary."""
        chip_value = chip_dict.get('value')
        if not chip_value:
            return
        start, end = chip_value.split(',')
        self.start_time = start
        self.end_time = end

    @property
    def start_time(self):
        """Property that returns the start time of a range."""
        if not self._start_date:
            return ''
        return self._start_date.strftime(self._DATE_FORMAT)

    @start_time.setter
    def start_time(self, start_time):
        """Sets the new start time of a range."""
        self.add_start_time(start_time)


class LabelChip(Chip):
    """Label chip."""

    CHIP_TYPE = 'label'
    CHIP_VALUE = 'label'

    def __init__(self):
        """Initialize the chip."""
        super().__init__()
        self._label = ''

    def from_dict(self, chip_dict):
        """Configure the chip from a dictionary."""
        chip_value = chip_dict.get('value')
        if not chip_value:
            return

        self.label = chip_value

    @property
    def label(self):
        """Property that returns back the label."""
        return self._label

    @label.setter
    def label(self, label):
        """Make changes to the label."""
        self._label = label

    def use_comment_label(self):
        """Use the comment label."""
        self._label = '__ts_comment'

    def use_star_label(self):
        """Use the star label."""
        self._label = '__ts_star'


class TermChip(Chip):
    """Term chip definition."""

    CHIP_TYPE = 'term'
    CHIP_VALUE = 'query'

    def __init__(self):
        """Initialize the chip."""
        super().__init__()
        self._query = ''

    @property
    def field(self):
        """Property that returns back the field used to match against."""
        return self._chip_field

    @field.setter
    def field(self, field):
        """Make changes to the field used to match against."""
        self._chip_field = field

    def from_dict(self, chip_dict):
        """Configure the term chip from a dictionary."""
        chip_value = chip_dict.get('value')
        if not chip_value:
            return

        self.field = chip_dict.get('field')
        self.query = chip_value

    @property
    def query(self):
        """Property that returns back the query."""
        return self._query

    @query.setter
    def query(self, query):
        """Make changes to the query."""
        self._query = query


class Search(resource.SketchResource):
    """Search object."""

    DEFAULT_SIZE_LIMIT = 10000

    def __init__(self, sketch):
        resource_uri = f'sketches/{sketch.id}/explore/'
        super().__init__(sketch=sketch, resource_uri=resource_uri)

        self._aggregations = ''
        self._chips = []
        self._created_at = ''
        self._description = ''
        self._indices = '_all'
        self._max_entries = self.DEFAULT_SIZE_LIMIT
        self._name = ''
        self._query_dsl = ''
        self._query_filter = {}
        self._query_string = ''
        self._raw_response = None
        self._return_fields = ''
        self._scrolling = None
        self._searchtemplate = ''
        self._updated_at = ''

    def _extract_chips(self, query_filter):
        """Extract chips from a query_filter."""
        chips = query_filter.get('chips', [])
        if not chips:
            return

        for chip_dict in chips:
            chip_type = chip_dict.get('type')
            if not chip_type:
                continue

            chip = None
            if chip_type == 'datetime_interval':
                chip = DateIntervalChip()
            elif chip_type == 'datetime_range':
                chip = DateRangeChip()
            elif chip_type == 'label':
                chip = LabelChip()
            elif chip_type == 'term':
                chip = TermChip()

            if not chip:
                continue
            chip.from_dict(chip_dict)

            active = chip_dict.get('active', True)
            chip.active = active

            operator = chip_dict.get('operator', 'must')
            if operator == 'must':
                chip.set_include()
            elif operator == 'must_not':
                chip.set_exclude()

            self.add_chip(chip)

    def _execute_query(self, file_name=''):
        """Execute a search request and store the results.

        Args:
            file_name (str): optional file path to a filename that
                all the results will be saved to. If not provided
                the results will be stored in the search object.
        """
        query_filter = self.query_filter
        if not isinstance(query_filter, dict):
            raise ValueError(
                'Unable to query with a query filter that isn\'t a dict.')

        stop_size = self._max_entries
        scrolling = not bool(stop_size and (
            stop_size < self.DEFAULT_SIZE_LIMIT))

        if self.scrolling is not None:
            scrolling = self.scrolling

        form_data = {
            'query': self._query_string,
            'filter': query_filter,
            'dsl': self._query_dsl,
            'fields': self._return_fields,
            'enable_scroll': scrolling,
            'file_name': file_name,
        }

        response = self.api.session.post(
            f'{self.api.api_root}/{self.resource_uri}', json=form_data)
        if not error.check_return_status(response, logger):
            error.error_message(
                response, message='Unable to query results',
                error=ValueError)

        if file_name:
            with open(file_name, 'wb') as fw:
                fw.write(response.content)
            return

        response_json = error.get_response_json(response, logger)

        scroll_id = response_json.get('meta', {}).get('scroll_id', '')
        form_data['scroll_id'] = scroll_id

        count = len(response_json.get('objects', []))
        total_count = count
        while count > 0:
            if self._max_entries and total_count >= self._max_entries:
                break

            if not scroll_id:
                logger.debug('No scroll ID, will stop.')
                break

            more_response = self.api.session.post(
                f'{self.api.api_root}/{self.resource_uri}', json=form_data)
            if not error.check_return_status(more_response, logger):
                error.error_message(
                    response, message='Unable to query results',
                    error=ValueError)
            more_response_json = error.get_response_json(more_response, logger)
            count = len(more_response_json.get('objects', []))
            total_count += count
            response_json['objects'].extend(
                more_response_json.get('objects', []))
            more_meta = more_response_json.get('meta', {})
            added_time = more_meta.get('es_time', 0)
            response_json['meta']['es_time'] += added_time

        total_elastic_count = response_json.get(
            'meta', {}).get('es_total_count', 0)
        if total_elastic_count != total_count:
            logger.info(
                '%d results were returned, but '
                '%d records matched the search query',
                total_count, total_elastic_count)

        self._raw_response = response_json

    def add_chip(self, chip):
        """Add a chip to the ..."""
        self._chips.append(chip)
        self.commit()

    def add_date_range(self, start_time, end_time):
        """Add a date range chip to the search query.

        Args:
            start_time (str): a string with the start time of the range,
                the format should be '%Y-%m-%dT%H:%M:%S'
            end_time (str): a string with the end time of the range,
                the format should be '%Y-%m-%dT%H:%M:%S'
        """
        chip = DateRangeChip()
        chip.start_time = start_time
        chip.end_time = end_time
        self.add_chip(chip)

    @property
    def chips(self):
        """Property that returns all the chips in the search object."""
        return self._chips

    def commit(self):
        """Commit changes to the search object."""
        self._raw_response = None
        super().commit()

    @property
    def created_at(self):
        """Property that returns back the creation time of a search."""
        return self._created_at

    def delete(self):
        """Deletes the saved search from the store."""
        if not self._resource_id:
            logger.warning(
                'Unable to delete the saved search, it does not appear to be '
                'saved in the first place.')
            return False

        resource_url = (
            f'{self.api.api_root}/sketches/{self._sketch.id}/views/'
            f'{self._resource_id}/')
        response = self.api.session.delete(resource_url)
        return error.check_return_status(response, logger)

    @property
    def description(self):
        """Property that returns back the description of the saved search."""
        return self._description

    @description.setter
    def description(self, description):
        """Make changes to the saved search description field."""
        self._description = description
        self.commit()

    def from_manual(  # pylint: disable=arguments-differ
            self,
            query_string=None,
            query_dsl=None,
            query_filter=None,
            return_fields=None,
            max_entries=None,
            **kwargs):
        """Explore the sketch.

        Args:
            query_string (str): Elasticsearch query string.
            query_dsl (str): Elasticsearch query DSL as JSON string.
            query_filter (dict): Filter for the query as a dict.
            return_fields (str): A comma separated string with a list of fields
                that should be included in the response. Optional and defaults
                to None.
            max_entries (int): Optional integer denoting a best effort to limit
                the output size to the number of events. Events are read in,
                10k at a time so there may be more events in the answer back
                than this number denotes, this is a best effort.
            kwargs (dict[str, object]): Depending on the resource they may
                require different sets of arguments to be able to run a raw
                API request.

        Raises:
            ValueError: if unable to query for the results.
            RuntimeError: if the query is missing needed values, or if the
                sketch is archived.
        """
        super().from_manual(**kwargs)
        if not (query_string or query_filter or query_dsl):
            raise RuntimeError('You need to supply a query')

        self._username = self.api.current_user.username
        self._name = 'From Explore'
        self._description = 'From Explore'

        if query_filter:
            self.query_filter = query_filter

        self._query_string = query_string
        self._query_dsl = query_dsl
        self._return_fields = return_fields

        if max_entries:
            self._max_entries = max_entries

        # TODO: Make use of search templates and aggregations.
        #self._searchtemplate = data.get('searchtemplate', 0)
        #self._aggregations = data.get('aggregation', 0)

        self._created_at = datetime.datetime.now(
            datetime.timezone.utc).isoformat()
        self._updated_at = self._created_at

        self.resource_data = {}

    def from_saved(self, search_id):  # pylint: disable=arguments-differ
        """Initialize the search object from a saved search.

        Args:
            search_id: integer value for the saved
                search (primary key).
        """
        resource_uri = f'sketches/{self._sketch.id}/views/{search_id}/'
        resource_data = self.api.fetch_resource_data(resource_uri)

        data = resource_data.get('objects', [None])[0]
        if not data:
            logger.error('Unable to get any data back from a saved search.')
            return

        label_string = data.get('label_string', '')
        if label_string:
            self._labels = json.loads(label_string)
        else:
            self._labels = []

        self._aggregations = data.get('aggregation', 0)
        self._created_at = data.get('created_at', '')
        self._description = data.get('description', '')
        self._name = data.get('name', '')
        self.query_dsl = data.get('query_dsl', '')
        query_filter = data.get('query_filter', '')
        if query_filter:
            filter_dict = json.loads(query_filter)
            if 'fields' in filter_dict:
                fields = filter_dict.pop('fields')
                return_fields = [x.get('field') for x in fields]
                self.return_fields = ','.join(return_fields)

            self.query_filter = filter_dict
        self._query_string = data.get('query_string', '')
        self._resource_id = search_id
        self._searchtemplate = data.get('searchtemplate', 0)
        self._updated_at = data.get('updated_at', '')
        self._username = data.get('user', {}).get('username', 'System')

        self.resource_data = data

    @property
    def indices(self):
        """Return the current set of indices used in the search."""
        return self._indices

    @indices.setter
    def indices(self, indices):
        """Make changes to the current set of indices."""
        if not isinstance(indices, list):
            logger.warning(
                'Indices needs to be a list of strings (indices that were '
                'passed in were not a list).')
            return
        if not all([isinstance(x, str) for x in indices]):
            logger.warning(
                'Indices needs to be a list of strings, not all entries '
                'in the indices list are strings.')
            return

        # Indices here can be either a list of timeline names or a list of
        # search indices. We need to verify that these exist before saving
        # them.
        timelines = {
            t.index_name: t.name for t in self._sketch.list_timelines()}

        new_indices = []
        for index in indices:
            if index in timelines:
                new_indices.append(index)
                continue

            if index in timelines.values():
                for index_name, timeline_name in timelines.items():
                    if timeline_name == index:
                        new_indices.append(index_name)
                        break

        if not new_indices:
            logger.warning('No valid indices found, not changin the value.')
            return

        self._indices = new_indices

    @property
    def max_entries(self):
        """Return the maximum number of entries in the return value."""
        return self._max_entries

    @max_entries.setter
    def max_entries(self, max_entries):
        """Make changes to the max entries of return values."""
        self._max_entries = max_entries
        if max_entries < self.DEFAULT_SIZE_LIMIT:
            _ = self.query_filter
            self._query_filter['size'] = max_entries
            self._query_filter['terminate_after'] = max_entries
        self.commit()

    @property
    def name(self):
        """Property that returns the query name."""
        return self._name

    @name.setter
    def name(self, name):
        """Make changes to the saved search name."""
        self._name = name
        self.commit()

    def order_ascending(self):
        """Set the order of objects returned back ascending."""
        # Trigger a creation of a query filter if it does not exist.
        _ = self.query_filter
        self._query_filter['order'] = 'asc'

    def order_descending(self):
        """Set the order of objects returned back descending."""
        # Trigger a creation of a query filter if it does not exist.
        _ = self.query_filter
        self._query_filter['order'] = 'desc'

    @property
    def query_dsl(self):
        """Property that returns back the query DSL."""
        return self._query_dsl

    @query_dsl.setter
    def query_dsl(self, query_dsl):
        """Make changes to the query DSL of the search."""
        if query_dsl and isinstance(query_dsl, str):
            query_dsl = json.loads(query_dsl)

        # Special condition of an empty DSL.
        if query_dsl == '""':
            query_dsl = ''

        self._query_dsl = query_dsl
        self.commit()

    @property
    def query_filter(self):
        """Property that returns the query filter."""
        if not self._query_filter:
            self._query_filter = {
                'time_start': None,
                'time_end': None,
                'size': self.DEFAULT_SIZE_LIMIT,
                'terminate_after': self.DEFAULT_SIZE_LIMIT,
                'indices': self.indices,
                'order': 'asc',
                'chips': [],
            }

        query_filter = self._query_filter
        query_filter['chips'] = [x.chip for x in self._chips]
        query_filter['indices'] = self.indices
        return query_filter

    @query_filter.setter
    def query_filter(self, query_filter):
        """Make changes to the query filter."""
        if isinstance(query_filter, str):
            try:
                query_filter = json.loads(query_filter)
            except json.JSONDecodeError as exc:
                raise ValueError('Unable to parse the string as JSON') from exc

        if not isinstance(query_filter, dict):
            raise ValueError('Query filter needs to be a dict.')
        self._query_filter = query_filter
        self._extract_chips(query_filter)
        self.commit()

    @property
    def query_string(self):
        """Property that returns back the query string."""
        return self._query_string

    @query_string.setter
    def query_string(self, query_string):
        """Make changes to the query string of a saved search."""
        self._query_string = query_string
        self.commit()

    def remove_chip(self, chip_index):
        """Remove a chip from the saved search."""
        chip_len = len(self._chips)
        if chip_index > (chip_len + 1):
            raise ValueError(
                f'Unable to remove chip, only {chip_len} chips stored '
                f'(no index {chip_index})')

        try:
            _ = self._chips.pop(chip_index)
        except IndexError as exc:
            raise ValueError(
                f'Unable to remove index {chip_index}, out of range') from exc

        self.commit()

    @property
    def return_fields(self):
        """Property that returns the return_fields."""
        return self._return_fields

    @return_fields.setter
    def return_fields(self, return_fields):
        """Make changes to the return fields."""
        self._return_fields = return_fields
        self.commit()

    @property
    def return_size(self):
        """Return the maximum number of entries in the return value."""
        return self._max_entries

    @return_size.setter
    def return_size(self, return_size):
        """Make changes to the maximum number of entries in the return."""
        self._max_entries = return_size

    def save(self):
        """Save the search in the database.

        Raises:
            ValueError: if there are values missing in order to save the query.
        """
        if not self.name:
            raise ValueError(
                'No name for the query saved. Please select a name first.')

        if not (self.query_string or self.query_dsl):
            raise ValueError(
                'Need to have either a query DSL or a query string to be '
                'able to save the search.')

        if not self.description:
            logger.warning(
                'No description selected for search, saving without one')

        if self._resource_id:
            resource_url = (
                f'{self.api.api_root}/sketches/{self._sketch.id}/views/'
                f'{self._resource_id}/')
        else:
            resource_url = (
                f'{self.api.api_root}/sketches/{self._sketch.id}/views/')

        query_filter = self.query_filter
        if self.return_fields:
            sketch_data = self._sketch.data
            sketch_meta = sketch_data.get('meta', {})
            mappings = sketch_meta.get('mappings', [])

            use_mappings = []
            for field in self.return_fields.split(','):
                field = field.strip().lower()
                for map_entry in mappings:
                    if map_entry.get('field', '').lower() == field:
                        use_mappings.append(map_entry)
            query_filter['fields'] = use_mappings

        data = {
            'name': self.name,
            'description': self.description,
            'query': self.query_string,
            'filter': query_filter,
            'dsl': self.query_dsl,
            'labels': json.dumps(self.labels),
        }
        response = self.api.session.post(resource_url, json=data)
        status = error.check_return_status(response, logger)
        if not status:
            error.error_message(
                response, 'Unable to save search', error=RuntimeError)

        response_json = error.get_response_json(response, logger)
        search_dict = response_json.get('objects', [{}])[0]
        self._resource_id = search_dict.get('id', 0)
        return f'Saved search to ID: {self._resource_id}'

    @property
    def scrolling(self):
        """Returns whether scrolling is enabled or not."""
        return self._scrolling

    def scrolling_disable(self):
        """"Disables scrolling."""
        self._scrolling = False

    def scrolling_enable(self):
        """Enable scrolling."""
        self._scrolling = True

    def to_dict(self):
        """Returns a dict with the respone of the query."""
        if not self._raw_response:
            self._execute_query()

        return self._raw_response

    def to_file(self, file_name):
        """Saves the content of the query to a file.

        Args:
            file_name (str): Full path to a file that will store the results
                of the query to as a ZIP file. The ZIP file will contain a
                METADATA file and a CSV with the results from the query.

        Returns:
            Boolean that determines if it was successful.
        """
        old_scrolling = self.scrolling
        self._scrolling = True
        self._execute_query(file_name=file_name)
        self._scrolling = old_scrolling
        return True

    def to_pandas(self):
        """Returns a pandas DataFrame with the response of the query."""
        if not self._raw_response:
            self._execute_query()

        return_list = []
        timelines = {
            t.index_name: t.name for t in self._sketch.list_timelines()}

        return_field_list = []
        return_fields = self._return_fields
        if return_fields:
            if return_fields.startswith('\''):
                return_fields = return_fields[1:]
            if return_fields.endswith('\''):
                return_fields = return_fields[:-1]
            return_field_list = return_fields.split(',')

        for result in self._raw_response.get('objects', []):
            source = result.get('_source', {})
            if not return_fields or '_id' in return_field_list:
                source['_id'] = result.get('_id')
            if not return_fields or '_type' in return_field_list:
                source['_type'] = result.get('_type')
            if not return_fields or '_index' in return_field_list:
                source['_index'] = result.get('_index')
            if not return_fields or '_source' in return_field_list:
                source['_source'] = timelines.get(result.get('_index'))

            return_list.append(source)

        data_frame = pandas.DataFrame(return_list)
        if 'datetime' in data_frame:
            try:
                data_frame['datetime'] = pandas.to_datetime(data_frame.datetime)
            except pandas.errors.OutOfBoundsDatetime:
                pass
        elif 'timestamp' in data_frame:
            try:
                data_frame['datetime'] = pandas.to_datetime(
                    data_frame.timestamp / 1e6, utc=True, unit='s')
            except pandas.errors.OutOfBoundsDatetime:
                pass

        return data_frame

    @property
    def updated_at(self):
        """Property that returns back the updated time of a search."""
        return self._updated_at
