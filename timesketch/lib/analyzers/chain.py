"""The sketch analyzer for chained events."""
from __future__ import unicode_literals

import collections
import uuid

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import chain_plugins  # pylint: disable=unused-import
from timesketch.lib.analyzers.chain_plugins import manager as chain_manager


class ChainSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for chained events."""

    NAME = 'chain'

    DEPENDENCIES = frozenset()

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        self._chain_plugins = (
            chain_manager.ChainPluginsManager.GetPlugins(self))
        super(ChainSketchPlugin, self).__init__(index_name, sketch_id)


    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        link_emoji = emojis.get_emoji('LINK')

        number_of_base_events = 0
        counter = collections.Counter()

        for chain_plugin in self._chain_plugins:
            if chain_plugin.SEARCH_QUERY_DSL:
                search_dsl = chain_plugin.SEARCH_QUERY_DSL
                search_string = None
            else:
                search_dsl = None
                search_string = chain_plugin.SEARCH_QUERY

            events = self.event_stream(
                query_string=search_string, query_dsl=search_dsl,
                return_fields=chain_plugin.EVENT_FIELDS)

            for event in events:
                if not chain_plugin.ProcessChain(event):
                    continue
                number_of_base_events += 1
                chain_uuid = uuid.uuid4().hex

                number_chained_events = chain_plugin.BuildChain(
                    base_event=event, chain_uuid=chain_uuid)
                counter[chain_uuid] = number_chained_events
                counter['total'] += number_chained_events

                attributes = {
                    'chain_uuid': chain_uuid,
                    'chain_plugin': chain_plugin.NAME}
                event.add_attributes(attributes)
                event.add_emojis([link_emoji])
                event.commit()

        number_of_chains = len(counter.keys()) - 1
        return (
            '{0:d} base events tagged with a chain UUID for {1:d} '
            'chains for a total of {2:d} events.'.format(
                number_of_base_events, number_of_chains,
                counter['total']))


manager.AnalysisManager.register_analyzer(ChainSketchPlugin)
