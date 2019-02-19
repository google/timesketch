"""Sketch analyzer plugin for potential bruteforce."""
from __future__ import unicode_literals

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager

import logging
import re
import sys


class PotentialBruteforceSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for Potential Bruteforce."""

    NAME = 'potential_bruteforce'
	

	
	# List of common logins
	COMMON_NAMES = [
    "admin",
	"user",
	"test",
	"root"]

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
        # TODO: Add Elasticsearch query to get the events you need.
        query = ('(data_type:"syslog:line"'
                 'AND body:"Invalid user")')

        # TODO: Specify what returned fields you need for your analyzer.
        return_fields = ['message', 'data_type', 'source_short']

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        # TODO: Add analyzer logic here.
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
		 ip_address = re.findall(r'\b25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?\.25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?\.25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?\.25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?\b',message)
		        if ip_address is None:
                continue
		 username = re.match()
		 		if username is None:
                continue
		 for username in self._COMMON_NAMES:
		   event.add_tags('common_name
		   ')
		  event.add_attributes({})

        if login_count > 0:
         self.sketch.add_view(
		 view_name='Potential bruteforce', analyzer_name=self.NAME,
		 query_string=query)

        # TODO: Return a summary from the analyzer.
        return 'Potential bruteforce analyzer completed, {0:d} login attempts from {1:d} unknown users and {2:d} IPs found'.format(
    login_count, user_count, ip_count)



manager.AnalysisManager.register_analyzer(PotentialBruteforceSketchPlugin)
