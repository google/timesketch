"""Sketch analyzer plugin for browser search."""

from __future__ import unicode_literals

import logging
import re

import six

from six.moves import urllib_parse as urlparse

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import utils
from timesketch.lib import emojis


logger = logging.getLogger("timesketch.analyzers.browser_search")


class BrowserSearchSketchPlugin(interface.BaseAnalyzer):
    """Sketch analyzer for BrowserSearch."""

    NAME = "browser_search"
    DISPLAY_NAME = "Browser search terms"
    DESCRIPTION = "Extract search terms from various search providers"

    DEPENDENCIES = frozenset(["domain"])

    # A list of fields to include in the view output.
    _FIELDS_TO_INCLUDE = ["domain", "url", "search_string"]

    # Here we define filters and callback methods for all hits on each filter.
    _URL_FILTERS = frozenset(
        [
            (
                "Bing",
                re.compile(r"bing\.com/search"),
                "_extract_search_query_from_url",
                "q",
            ),
            (
                "DuckDuckGo",
                re.compile(r"duckduckgo\.com"),
                "_extract_search_query_from_url",
                "q",
            ),
            (
                "GMail",
                re.compile(r"mail\.google\.com"),
                "_extract_urlpart_search_query",
                None,
            ),
            (
                "Google Inbox",
                re.compile(r"inbox\.google\.com"),
                "_extract_urlpart_search_query",
                None,
            ),
            (
                "Google Docs",
                re.compile(r"docs\.google\.com"),
                "_extract_search_query_from_url",
                "q",
            ),
            (
                "Google Groups",
                re.compile(r"groups\.google\.com/a"),
                "_extract_urlpart_search_query",
                None,
            ),
            (
                "Google Drive",
                re.compile(r"drive\.google\.com/.+/search"),
                "_extract_search_query_from_url",
                "q",
            ),
            (
                "Google",
                re.compile(r"(www\.|[a-zA-Z]\.|/)google\.[a-zA-Z]+/search"),
                "_extract_search_query_from_url",
                "q",
            ),
            (
                "Google Sites",
                re.compile(r"sites\.google\."),
                "_extract_search_query_from_url",
                "q",
            ),
            (
                "LinkedIn",
                re.compile(r"linkedin\.com/search"),
                "_extract_search_query_from_url",
                "keywords",
            ),
            (
                "Yahoo",
                re.compile(r"yahoo\.com/search"),
                "_extract_search_query_from_url",
                "p",
            ),
            (
                "Yandex",
                re.compile(r"yandex\.com/search"),
                "_extract_search_query_from_url",
                "text",
            ),
            (
                "Youtube",
                re.compile(r"youtube\.com"),
                "_extract_search_query_from_url",
                "search_query",
            ),
        ]
    )

    def _decode_url(self, url):
        """Decodes the URL, replaces %XX to their corresponding characters.

        Args:
          url (str): encoded URL.

        Returns:
          str: decoded URL.
        """
        if not url:
            return ""

        # pylint: disable=too-many-function-args
        decoded_url = urlparse.unquote(url)
        if isinstance(decoded_url, six.binary_type):
            try:
                decoded_url = decoded_url.decode("utf-8")
            except UnicodeDecodeError as exception:
                decoded_url = decoded_url.decode("utf-8", errors="replace")
                logger.warning(
                    "Unable to decode URL: {0:s} with error: {1!s}".format(
                        url, exception
                    )
                )

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
        if "search/" not in url:
            return None

        _, _, line = url.partition("search/")
        line, _, _ = line.partition("/")
        line, _, _ = line.partition("?")

        search_quoted = line.replace("+", " ")
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
        if "{0:s}=".format(parameter) not in url:
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
        _, _, url = url.partition("?")
        # Look for a key value pair named 'q'.
        _, _, url = url.partition("{0:s}=".format(parameter))
        if not url:
            return ""

        # Strip additional key value pairs.
        parameter, _, _ = url.partition("&")
        parameter = parameter.replace("+", " ")

        return self._decode_url(parameter)

    def run(self):
        """Entry point for the browser search analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = 'source_short:"WEBHIST" OR source:"WEBHIST"'
        return_fields = ["url", "datetime"]
        search_emoji = emojis.get_emoji("MAGNIFYING_GLASS")

        # Generator of events based on your query.
        events = self.event_stream(query_string=query, return_fields=return_fields)

        simple_counter = 0
        for event in events:
            url = event.source.get("url")

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
                datetime = event.source.get("datetime")
                day, _, _ = datetime.partition("T")
                event.add_attributes(
                    {
                        "search_string": search_query,
                        "search_engine": engine,
                        "search_day": "D:{0:s}".format(day),
                    }
                )

                event.add_human_readable(
                    "{0:s} search query: {1:s}".format(engine, search_query), self.NAME
                )
                event.add_emojis([search_emoji])
                event.add_tags(["browser-search"])
                # We break at the first hit of a successful search engine.
                break

            # Commit the event to the datastore.
            event.commit()

        if simple_counter > 0:
            view = self.sketch.add_view(
                view_name="Browser Search",
                analyzer_name=self.NAME,
                query_string='tag:"browser-search"',
                additional_fields=self._FIELDS_TO_INCLUDE,
            )

            top_search_name = f"Top 20 browser search queries ({self.timeline_name})"
            top_search_params = {
                "aggregator_name": "top_terms",
                "aggregator_class": "apex",
                "aggregator_parameters": {
                    "fields": [{"field": "search_string", "type": "text"}],
                    "aggregator_options": {
                        "metric": "value_count",
                        "max_items": 20,
                        "timeline_ids": [self.timeline_id],
                    },
                    "chart_type": "table",
                    "chart_options": {
                        "chartTitle": top_search_name,
                        "height": 600,
                        "width": 800,
                    },
                },
            }
            agg_obj = self.sketch.add_apex_aggregation(
                name=top_search_name,
                params=top_search_params,
                chart_type="table",
                description="Created by the browser search analyzer",
                label="informational",
                view_id=view.id,
            )

            top_days_name = f"Top 20 days of search queries ({self.timeline_name})"
            top_days_params = {
                "aggregator_name": "top_terms",
                "aggregator_class": "apex",
                "aggregator_parameters": {
                    "fields": [{"field": "search_day", "type": "text"}],
                    "aggregator_options": {
                        "metric": "value_count",
                        "max_items": 20,
                        "timeline_ids": [self.timeline_id],
                    },
                    "chart_type": "table",
                    "chart_options": {
                        "chartTitle": top_days_name,
                        "height": 600,
                        "width": 800,
                    },
                },
            }
            agg_days = self.sketch.add_apex_aggregation(
                name=top_days_name,
                params=top_days_params,
                chart_type="bar",
                description="Created by the browser search analyzer",
                label="informational",
                view_id=view.id,
            )

            top_engines_name = f"Top 20 Search Engines ({self.timeline_name})"
            top_engines_params = {
                "aggregator_name": "top_terms",
                "aggregator_class": "apex",
                "aggregator_parameters": {
                    "fields": [{"field": "domain", "type": "text"}],
                    "aggregator_options": {
                        "metric": "value_count",
                        "max_items": 20,
                        "query_string": 'tag:"browser-search"',
                        "timeline_ids": [self.timeline_id],
                    },
                    "chart_type": "bar",
                    "chart_options": {
                        "chartTitle": top_days_name,
                        "height": 600,
                        "width": 800,
                    },
                },
            }
            agg_engines = self.sketch.add_apex_aggregation(
                name=top_engines_name,
                params=top_engines_params,
                chart_type="table",
                description="Created by the browser search analyzer",
                label="informational",
                view_id=view.id,
            )

            story = self.sketch.add_story(
                "{0:s} - {1:s}".format(utils.BROWSER_STORY_TITLE, self.timeline_name)
            )
            story.add_text(utils.BROWSER_STORY_HEADER, skip_if_exists=True)

            story.add_text(
                "## Browser Search Analyzer.\n\nThe browser search "
                "analyzer takes URLs usually reserved for browser "
                "search queries and extracts the search string."
                "In this timeline the analyzer discovered {0:d} "
                "browser searches.\n\nThis is a summary of "
                "it's findings for the timeline **{1:s}**.".format(
                    simple_counter, self.timeline_name
                )
            )

            story.add_text("The top 20 most commonly discovered searches were:")
            story.add_aggregation(agg_obj)
            story.add_text("The domains used to search:")
            story.add_aggregation(agg_engines)
            story.add_text("And the most common days of search:")
            story.add_aggregation(agg_days)
            story.add_text("And an overview of all the discovered search terms:")
            story.add_view(view)

        return (
            "Browser Search completed with {0:d} search results " "extracted."
        ).format(simple_counter)


manager.AnalysisManager.register_analyzer(BrowserSearchSketchPlugin)
