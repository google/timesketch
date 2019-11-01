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
    """Sketch analyzer for chained events.

    The purpose of the chain analyzer is to chain together events that can
    be described as linked, either by sharing some common entitites, or
    one event being a derivative of another event. An example of this
    would be that a browser downloads an executable, which then later gets
    executed. The signs of execution could lie in multiple events, from
    different sources, but they are all linked or chained together. This
    could help an analyst see the connection between these separate but
    chained events. Another example could be a document written and then
    compressed into a ZIP file, which would then be exfilled through some
    means. If the document and the ZIP file are chained together it could be
    easier for the analyst to track the meaning of an exfil event involving the
    compressed file.
    """

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
            chain_manager.ChainPluginsManager.get_plugins(self))
        super(ChainSketchPlugin, self).__init__(index_name, sketch_id)


    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        link_emoji = emojis.get_emoji('LINK')

        number_of_base_events = 0
        counter = collections.Counter()

        # TODO: Have each plugin run in a separate task.
        # TODO: Add a time limit for each plugins run to prevent it from
        #       holding everything up.
        for chain_plugin in self._chain_plugins:
            if chain_plugin.SEARCH_QUERY_DSL:
                search_dsl = chain_plugin.SEARCH_QUERY_DSL
                search_string = None
            else:
                search_dsl = None
                search_string = chain_plugin.SEARCH_QUERY

            return_fields = chain_plugin.EVENT_FIELDS
            return_fields.extend(['chain_id_list', 'chain_plugins'])
            events = self.event_stream(
                query_string=search_string, query_dsl=search_dsl,
                return_fields=return_fields)

            for event in events:
                if not chain_plugin.process_chain(event):
                    continue
                number_of_base_events += 1
                chain_id = uuid.uuid4().hex

                number_chained_events = chain_plugin.build_chain(
                    base_event=event, chain_id=chain_id)
                counter[chain_id] = number_chained_events
                counter['total'] += number_chained_events

                chain_id_list = event.source.get('chain_id_list', [])
                chain_id_list.append(chain_id)
                chain_plugins = event.source.get('chain_plugins', [])
                chain_plugins.append(chain_plugin.NAME)
                attributes = {
                    'chain_id_list': chain_id_list,
                    'chain_plugins': chain_plugins}
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
