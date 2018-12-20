"""Sketch analyzer plugin for browser search."""
from __future__ import unicode_literals

import logging
import re
import sys

# pylint:disable=wrong-import-position
if sys.version_info[0] < 3:
    import urllib as urlparse
    BYTES_TYPE = str
else:
    from urllib import parse as urlparse  # pylint: disable=no-name-in-module
    BYTES_TYPE = bytes

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib import emojis


class BrowserSearchSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for BrowserSearch."""

    NAME = 'browser_search'

    # Here we define filters and callback methods for all hits on each filter.
    _URL_FILTERS = frozenset([
        ('Bing', re.compile(r'bing\.com/search'),
         '_extract_search_query_from_url', 'q'),
        ('DuckDuckGo', re.compile(r'duckduckgo\.com'),
         '_extract_search_query_from_url', 'q'),
        ('GMail', re.compile(r'mail\.google\.com'),
         '_extract_urlpart_search_query', None),
        ('Google Inbox', re.compile(r'inbox\.google\.com'),
         '_extract_urlpart_search_query', None),
        ('Google Docs', re.compile(r'docs\.google\.com'),
         '_extract_search_query_from_url', 'q'),
        ('Google Groups', re.compile(r'groups\.google\.com/a'),
         '_extract_urlpart_search_query', None),
        ('Google Drive', re.compile(r'drive\.google\.com/.+/search'),
         '_extract_search_query_from_url', 'q'),
        ('Google Search',
         re.compile(r'(www\.|[a-zA-Z]\.|/)google\.[a-zA-Z]+/search'),
         '_extract_search_query_from_url', 'q'),
        ('Google Sites', re.compile(r'sites\.google\.'),
         '_extract_search_query_from_url', 'q'),
        ('Yahoo', re.compile(r'yahoo\.com/search'),
         '_extract_search_query_from_url', 'p'),
        ('Yandex', re.compile(r'yandex\.com/search'),
         '_extract_search_query_from_url', 'text'),
        ('Youtube', re.compile(r'youtube\.com'),
         '_extract_search_query_from_url', 'search_query'),
    ])

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(BrowserSearchSketchPlugin, self).__init__(index_name, sketch_id)

    def _decode_url(self, url):
        """Decodes the URL, replaces %XX to their corresponding characters.

        Args:
          url (str): encoded URL.

        Returns:
          str: decoded URL.
        """
        if not url:
            return ''

        decoded_url = urlparse.unquote(url)
        if isinstance(decoded_url, BYTES_TYPE):
            try:
                decoded_url = decoded_url.decode('utf-8')
            except UnicodeDecodeError as exception:
                decoded_url = decoded_url.decode('utf-8', errors='replace')
                logging.warning(
                    'Unable to decode URL: {0:s} with error: {1!s}'.format(
                        url, exception))

        return decoded_url

    def _extract_urlpart_search_query(self, url):
        """Extracts a search query from a URL that uses search/query notation.

        Examples:
            GMail: https://mail.google.com/mail/u/0/#search/query[/?]
            Inbox: https://inbox.google.com/search/<query>
            Groups: https://groups.google.com/a/google.com/forum/#!search/query

        Args:
            url (str): URL.

        Returns:
            str: search query or None if no query was found.
        """
        if 'search/' not in url:
            return None

        _, _, line = url.partition('search/')
        line, _, _ = line.partition('/')
        line, _, _ = line.partition('?')

        search_quoted = line.replace('+', ' ')
        return self._decode_url(search_quoted)

    def _extract_search_query_from_url(self, url, parameter):
        """Extracts a search query from the URL.

        Examples:
            Bing: https://www.bing.com/search?q=query
            GitHub: https://github.com/search?q=query
            Google Drive: https://drive.google.com/drive/search?q=query
            Google Search: https://www.google.com/search?q=query
            Google Sites: https://sites.google.com/site/.*/system/app/pages/
                          search?q=query
            DuckDuckGo: https://duckduckgo.com/?q=query
            Yahoo: https://search.yahoo.com/search?p=query
            Yahoo: https://search.yahoo.com/search;?p=query
            Yandex: https://www.yandex.com/search/?text=query
            YouTube: https://www.youtube.com/results?search_query=query

        Args:
          url (str): URL.
          parameter (str): the parameter that contains the search query.

        Returns:
          str: search query, the search parameter or None if no
              query was found.
        """
        if '{0:s}='.format(parameter) not in url:
            return None

        return self._get_url_parameter_value(url, parameter)

    def _get_url_parameter_value(self, url, parameter):
        """Retrieves the GET parameter from a URL.

        Args:
          url (str): URL.
          parameter (str): the parameter to extract.

        Returns:
          str: the GET parameter value or None if no parameter was found.
        """
        # Make sure we're analyzing the query part of the URL.
        _, _, url = url.partition('?')
        # Look for a key value pair named 'q'.
        _, _, url = url.partition('{0:s}='.format(parameter))
        if not url:
            return ''

        # Strip additional key value pairs.
        parameter, _, _ = url.partition('&')
        parameter = parameter.replace('+', ' ')

        return self._decode_url(parameter)

    def run(self):
        """Entry point for the browser search analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = 'source_short:"WEBHIST"'
        return_fields = ['url']

        # Generator of events based on your query.
        events = self.event_stream(
            query_string=query, return_fields=return_fields)

        simple_counter = 0
        for event in events:
            url = event.source.get('url')

            if url is None:
                continue

            for engine, expression, method_name, parameter in self._URL_FILTERS:
                callback_method = getattr(self, method_name, None)
                if not callback_method:
                    continue

                match = expression.search(url)
                if not match:
                    continue

                if parameter:
                    search_query = callback_method(url, parameter)
                else:
                    search_query = callback_method(url)

                if not search_query:
                    continue

                simple_counter += 1
                event.add_attributes({'search_string': search_query})

                event.add_human_readable('{0:s} search: {1:s}'.format(
                    engine, search_query))
                event.add_emojis([emojis.MAGNIFYING_GLASS])
                event.add_tags(['browser_search'])
                # We break at the first hit of a successful search engine.
                break

        self.sketch.add_view(
            'Browser Search', query_string='tag:"browser_search"')

        return (
            'Browser Search completed with {0:d} search results '
            'extracted.').format(simple_counter)


manager.AnalysisManager.register_analyzer(BrowserSearchSketchPlugin)
