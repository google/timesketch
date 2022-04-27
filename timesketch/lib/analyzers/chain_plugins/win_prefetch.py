# -*- coding: utf-8 -*-
"""This file contains the plugin for executables in Windows prefetch files."""

from timesketch.lib.analyzers.chain_plugins import interface
from timesketch.lib.analyzers.chain_plugins import manager


class WinPrefetchChainPlugin(interface.BaseChainPlugin):
    """A plugin to chain prefetch records to other events."""

    NAME = "winprefetch"
    DESCRIPTION = (
        "Plugin to chain prefetch records that show executions on a Windows "
        "system to other events with that executable in it."
    )

    SEARCH_QUERY = 'data_type:"windows:prefetch:execution"'
    EVENT_FIELDS = ["executable"]

    def process_chain(self, base_event):
        """Determine if the extracted event fits the criteria of the plugin.

        Args:
            base_event: an event object (instance of Event).

        Returns:
            boolean to determine whether a chain should be generated from
            the event or not. By default this returns True.
        """
        target = base_event.source.get("executable", "")
        return target.lower().endswith(".exe")

    def get_chained_events(self, base_event):
        """Yields an event that is chained or linked to the base event.

        Args:
            base_event: the base event of the chain, used to construct further
                queries (instance of Event).

        Yields:
            An event (instance of Event) object that is linked or chained to
            the base event, according to the plugin.
        """
        target = base_event.source.get("executable", "")
        if not target:
            return
            yield  # pylint: disable=W0101

        search_query = 'url:"*{0:s}*"'.format(target)
        return_fields = ["url"]

        events = self.analyzer_object.event_stream(
            search_query, return_fields=return_fields, scroll=False
        )
        for event in events:
            url = event.source.get("url", "")
            if target.lower() in url.lower():
                yield event

        lnk_query = "parser:lnk"
        return_fields = ["link_target"]

        events = self.analyzer_object.event_stream(
            lnk_query, return_fields=return_fields, scroll=False
        )
        for event in events:
            link_target = event.source.get("link_target", "")
            if target.lower() in link_target.lower():
                yield event


manager.ChainPluginsManager.register_plugin(WinPrefetchChainPlugin)
