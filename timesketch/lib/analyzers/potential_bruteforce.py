"""Sketch analyzer plugin for potential bruteforce."""
from __future__ import unicode_literals

import logging
import re

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager



class PotentialBruteforceSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for Potential Bruteforce."""

    NAME = 'potential_bruteforce'
	

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.
        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(PotentialBruteforceSketchPlugin, self).__init__(
            index_name, sketch_id)
	


    def run(self):
        """Entry point for the analyzer.
        Returns:
            String with summary of the analyzer result
        """
        # Add Elasticsearch query to get the events you need.
        query = ('(data_type:"syslog:line"'
                 'AND body:"Invalid user")')

        # Specify what returned fields you need for your analyzer.
        return_fields = ['message', 'data_type', 'source_short']
        stop_emoji = emojis.get_emoji('STOP')

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        #  Add analyzer logic here.
        # Methods available to use for sketch analyzers:
        # sketch.get_all_indices()
        # sketch.add_view(name, query_string, query_filter={})
        # event.add_attributes({'foo': 'bar'})
        # event.add_tags(['tag_name'])
        # event_add_label('label')
        # event.add_star()
        # event.add_comment('comment')

        login_count = 0

        for event in events:
            data_type = event.source.get('data_type')
            source_short = event.source.get('source_short')
            message = event.source.get('message')
            ip_address = re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', message)
	    if ip_address:
                event.add_attributes({'ip_address': ip_address})
            if ip_address is None:
                continue
	    username = re.search(r'Invalid user ([a-zA-Z0-9_\.+\-]{1,32}) from', message)
            if username:
                event.add_attributes({'user': username})
	    if username is None:
                continue
            event.add_emojis([stop_emoji])
            event.add_tags(['unknown_user'])

         if login_count > 0:
          self.sketch.add_view(
		 view_name='Potential bruteforce', analyzer_name=self.NAME,
		 query_string=query)


        # TODO: Return a summary from the analyzer.
        return 'Potential bruteforce analyzer completed, {0:d} login attempts from unknown users found'.format(
    login_count)



manager.AnalysisManager.register_analyzer(PotentialBruteforceSketchPlugin)
