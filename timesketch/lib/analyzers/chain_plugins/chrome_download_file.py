# -*- coding: utf-8 -*-
"""Plugin for chaining Chrome downloads to filesystem and execution events."""

from timesketch.lib.analyzers.chain_plugins import interface
from timesketch.lib.analyzers.chain_plugins import manager


class ChromeDownloadFilesystemChainPlugin(interface.BaseChainPlugin):
    """A plugin to chain Chrome downloads to filesystem events."""

    NAME = "chromefilesystem"
    DESCRIPTION = (
        "Plugin to chain Chrome download records to corresponding filesystem "
        "events and execution events."
    )

    SEARCH_QUERY = 'data_type:"chrome:history:file_downloaded"'
    EVENT_FIELDS = ["full_path"]

    def get_chained_events(self, base_event):
        """Yields an event that is chained or linked to the base event.

        Args:
            base_event: the base event of the chain, used to construct further
                queries (instance of Event).

        Yields:
            An event (instance of Event) object that is linked or chained to
            the base event, according to the plugin.
        """
        target = base_event.source.get("full_path", "")
        if not target:
            return
            yield  # pylint: disable=W0101

        if "\\" in target:
            separator = "\\"
        else:
            separator = "/"

        target = target.split(separator)[-1]
        # TODO: Add more checks here, eg; USB, generic execution, etc.
        search_query = (
            '(data_type:"fs:stat" AND filename:"*{0:s}") OR '
            '(data_type:"fs:stat:ntfs" AND name:"{0:s}")'
        ).format(target)
        return_fields = ["filename", "path_hints"]

        events = self.analyzer_object.event_stream(
            search_query, return_fields=return_fields, scroll=False
        )
        for event in events:
            yield event

        exec_query = 'executable:"*{0:s}"'.format(target)
        return_fields = ["executable", "chains"]

        events = self.analyzer_object.event_stream(
            exec_query, return_fields=return_fields, scroll=False
        )
        for event in events:
            yield event


manager.ChainPluginsManager.register_plugin(ChromeDownloadFilesystemChainPlugin)
