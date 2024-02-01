"""The sketch analyzer for chained events."""

from __future__ import unicode_literals

import collections
import uuid

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import chain_plugins  # pylint: disable=unused-import
from timesketch.lib.analyzers.chain_plugins import manager as chain_manager


class ChainSketchPlugin(interface.BaseAnalyzer):
    """Analyzer for chained events.

    The purpose of the chain analyzer is to chain together events that can
    be described as linked, either by sharing some common entities, or
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

    NAME = "chain"
    DISPLAY_NAME = "Chain linked events"
    DESCRIPTION = (
        "Chain together events that can be described as linked, "
        "either by sharing some common entities, or one event being "
        "a derivative of another event"
    )

    DEPENDENCIES = frozenset()

    def __init__(self, index_name, sketch_id, timeline_id=None):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: OpenSearch index name
            sketch_id: Sketch ID
            timeline_id: The ID of the timeline.
        """
        self.index_name = index_name
        self._chain_plugins = chain_manager.ChainPluginsManager.get_plugins(self)
        super().__init__(index_name, sketch_id, timeline_id=timeline_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        link_emoji = emojis.get_emoji("LINK")

        number_of_base_events = 0
        number_of_chains = 0
        counter = collections.Counter()
        events_to_update = {}

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
            events = self.event_stream(
                query_string=search_string,
                query_dsl=search_dsl,
                return_fields=return_fields,
            )

            for event in events:
                if not chain_plugin.process_chain(event):
                    continue
                chain_id = uuid.uuid4().hex

                chained_events = chain_plugin.build_chain(
                    base_event=event, chain_id=chain_id
                )
                number_chained_events = len(chained_events)
                if not number_chained_events:
                    continue

                for chained_event in chained_events:
                    chained_id = chained_event.get("event_id")
                    if chained_id not in events_to_update:
                        default = {"event": chained_event.get("event"), "chains": []}
                        events_to_update[chained_id] = default

                    events_to_update[chained_id]["chains"].append(
                        chained_event.get("chain")
                    )

                number_of_base_events += 1

                counter[chain_plugin.NAME] += number_chained_events
                counter["total"] += number_chained_events

                chain = {
                    "chain_id": chain_id,
                    "plugin": chain_plugin.NAME,
                    "is_base": True,
                    "leafs": number_chained_events,
                }
                if event.event_id not in events_to_update:
                    default = {"event": event, "chains": []}
                    events_to_update[event.event_id] = default
                events_to_update[event.event_id]["chains"].append(chain)
                number_of_chains += 1

        for event_update in events_to_update.values():
            event = event_update.get("event")
            attributes = {"chains": event_update.get("chains")}
            event.add_attributes(attributes)
            event.add_emojis([link_emoji])
            event.commit()

        chain_string = " - ".join(
            [
                "[{0:s}] {1:d}".format(x[0], x[1])
                for x in counter.most_common()
                if x[0] != "total"
            ]
        )
        return (
            "{0:d} base events annotated with a chain UUID for {1:d} "
            "chains for a total of {2:d} events. {3:s}".format(
                number_of_base_events, number_of_chains, counter["total"], chain_string
            )
        )


manager.AnalysisManager.register_analyzer(ChainSketchPlugin)
