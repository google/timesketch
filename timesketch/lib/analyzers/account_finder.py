"""Sketch analyzer plugin for feature extraction."""
from __future__ import unicode_literals

import logging
import re

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class AccountFinderSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for AccountFinder."""

    NAME = 'account_finder'

    # CONFIG_FILE = 'accounts.yaml'

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(AccountFinderSketchPlugin, self).__init__(
            index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """

        # config = interface.get_yaml_config(self.CONFIG_FILE)
        #
        # if not config:
        #     return 'Unable to parse the config file.'
        #
        # return_strings = []
        #
        # for name, feature_config in config.iteritems():
        #     accounts_found = self.extract_account(name, feature_config)
        #     if accounts_found['total_events'] > 0:
        #         number_found = accounts_found.pop('total_events')
        #         return_strings.append("Total {} found: {}".format(name, str(number_found)))
        #         for account, count in accounts_found.iteritems():
        #             return_strings.append("{}: {}".format(account, count))
        #
        # return ', '.join(return_strings)

        return_fields = ['tags', 'found_account']

        events = self.event_stream(
            query_string="tag:* AND found_account:*",
            return_fields=return_fields)

        accounts_found = {}

        for event in events:
            account_type = event.source.get('tag')

            if account_type not in accounts_found:
                accounts_found[account_type] = {}

            found_account = event.source.get('found_account')
            if found_account not in accounts_found[account_type]:
                accounts_found[account_type][found_account] = 1

            else:
                accounts_found[account_type][found_account] += 1

        return str(accounts_found)

    def extract_account(self, name, config):
        """Extract accounts from events.

        Args:
            name: String with the name describing the account to be extracted.
            config: A dict that contains the configuration for the account
                extraction. See ~/config/accounts.yaml for fields and further
                documentation of what needs to be defined.

        Returns:
            String with summary of the analyzer result.
        """
        query = config.get('query_string')
        query_dsl = config.get('query_dsl')
        attribute = config.get('attribute')

        if not attribute:
            logging.warning('No attribute defined.')
            return ''

        store_as = config.get('store_as')
        if not store_as:
            logging.warning('No attribute defined to store results in.')
            return ''

        tags = config.get('tags', [])

        expression_string = config.get('re')
        if not expression_string:
            logging.warning('No regular expression defined.')
            return ''
        try:
            expression = re.compile(expression_string)
        except re.error as exception:
            logging.warning((
                'Regular expression failed to compile, with '
                'error: {0:s}').format(exception))
            return ''

        emoji_names = config.get('emojis', [])
        emojis_to_add = [emojis.get_emoji(x) for x in emoji_names]

        return_fields = [attribute]

        events = self.event_stream(
            query_string=query, query_dsl=query_dsl,
            return_fields=return_fields)

        accounts_found = {}

        event_counter = 0
        for event in events:
            attribute_field = event.source.get(attribute)
            if isinstance(attribute_field, (str, unicode)):
                attribute_value = attribute_field.lower()
            elif isinstance(attribute_field, (list, tuple)):
                attribute_value = ','.join(attribute_field)
            elif isinstance(attribute_field, (int, float)):
                attribute_value = attribute_field
            else:
                attribute_value = None

            if not attribute_value:
                continue

            result = expression.findall(attribute_value)
            if not result:
                continue

            result = result[0]
            if result not in accounts_found:
                accounts_found[result] = 1
            else:
                accounts_found[result] += 1

            event_counter += 1
            event.add_attributes({store_as: result})
            if emojis_to_add:
                event.add_emojis(emojis_to_add)

            if tags:
                event.add_tags(tags)

        create_view = config.get('create_view', False)
        if create_view and event_counter:
            if query:
                query_string = query
            else:
                query_string = query_dsl
            self.sketch.add_view(name, query_string)

        accounts_found['total_events'] = event_counter
        return accounts_found


manager.AnalysisManager.register_analyzer(AccountFinderSketchPlugin)
