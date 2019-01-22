"""Sketch analyzer plugin for feature extraction."""
from __future__ import unicode_literals

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class AccountFinderSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for AccountFinder."""

    NAME = 'account_finder'
    DEPENDENCIES = frozenset(['feature_extraction'])

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
        return_fields = ['found_account', 'tag']

        accounts_found = {}

        events = self.event_stream(
            query_string='_exists_:found_account AND _exists_:tag',
            return_fields=return_fields)

        for event in events:
            event_tags = event.source.get('tag')
            for account_tag in event_tags:
                # There could be other tags on these events; only get the ones
                # related to accounts
                if ' Account' not in account_tag:
                    continue

                found_account = event.source.get('found_account')

                accounts_found.setdefault(account_tag, {})
                accounts_found[account_tag].setdefault(found_account, 0)
                accounts_found[account_tag][found_account] += 1

        return '{0:s} identified use of the following accounts: {1!s}'\
            .format(self.NAME, accounts_found)


manager.AnalysisManager.register_analyzer(AccountFinderSketchPlugin)
