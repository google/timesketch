# -*- coding: utf-8 -*-
"""This file contains an interface for chain analyzer plugins."""
import abc

from timesketch.lib import emojis


class BaseChainPlugin(object):
    """A base plugin for the chain analyzer.

    This is an interface for the chain analyzer plugins.

    """
    NAME = 'chain'
    DESCRIPTION = ''

    # A string value that defines the search query used to find the original
    # event that starts the chain. In order for this plugin to work
    # either the SEARCH_QUERY or SEARCH_QUERY_DSL needs to be defined.
    SEARCH_QUERY = ''

    # Defines the original event search query DSL. If this attribute
    # is defined the SEARCH_QUERY attribute is ignored.
    SEARCH_QUERY_DSL = ''

    # Defines the fields that need to be returned as part of the
    # event object.
    EVENT_FIELDS = []

    _EMOJIS = [emojis.get_emoji('LINK')]

    def __init__(self, analyzer_object):
        """Initialize the plugin."""
        super(BaseChainPlugin, self).__init__()
        self.analyzer_object = analyzer_object

    def ProcessChain(self, base_event):
        """Determine if the extracted event fits the criteria of the plugin.

        Args:
            base_event: an event object (instance of Event).

        Returns:
            boolean to determine whether a chain should be generated from
            the event or not. By default this returns True.
        """
        if base_event:
            return True
        return True

    def BuildChain(self, base_event, chain_uuid):
        """Build chain from base event.

        Args:
            base_event: the base event of the chain, used to construct further
                queries (instance of Event).
            chain_uuid: a string with the chain UUID value.

        Returns:
            An integer with the total number of discovered events.
        """
        total_events = 0
        for event in self.GetChainedEvent(base_event):
            attributes = {
                'chain_uuid': chain_uuid,
                'chain_plugin': self.NAME}

            event.add_attributes(attributes)
            event.add_emojis(self._EMOJIS)
            event.commit()
            total_events += 1
        return total_events

    @abc.abstractmethod
    def GetChainedEvents(self, base_event):
        """Yields an event that is chained or linked to the base event.

        Args:
            base_event: the base event of the chain, used to construct further
                queries (instance of Event).

        Yields:
            An event (instance of Event) object that is linked or chained to
            the base event, according to the plugin.
        """
