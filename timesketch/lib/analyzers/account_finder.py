"""Sketch analyzer plugin for feature extraction."""

from __future__ import unicode_literals

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


class AccountFinderSketchPlugin(interface.BaseAnalyzer):
    """Sketch analyzer for AccountFinder."""

    NAME = "account_finder"
    DISPLAY_NAME = "Account finder"
    DESCRIPTION = "List accounts detected by the feature extraction analyzer."

    DEPENDENCIES = frozenset(["feature_extraction"])

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result.
        """
        return_fields = ["found_account", "tag"]

        accounts_found = {}

        events = self.event_stream(
            query_string="_exists_:found_account AND _exists_:tag",
            return_fields=return_fields,
        )

        for event in events:
            event_tags = event.source.get("tag")
            for account_tag in event_tags:
                # There could be other tags on these events; only get the ones
                # related to accounts
                if "-account" not in account_tag:
                    continue

                # Add the account tags to the output data
                self.output.add_created_tags([account_tag])

                found_account = event.source.get("found_account")

                accounts_found.setdefault(account_tag, {})
                accounts_found[account_tag].setdefault(found_account, 0)
                accounts_found[account_tag][found_account] += 1

        if accounts_found:
            self.output.result_status = "SUCCESS"
            self.output.result_priority = "LOW"
            self.output.result_summary = (
                "{0:s} identified use of the following accounts: {1!s}".format(
                    self.DISPLAY_NAME, accounts_found
                )
            )
            return str(self.output)

        self.output.result_status = "SUCCESS"
        self.output.result_priority = "NOTE"
        self.output.result_summary = "{0:s} was unable to extract any accounts.".format(
            self.DISPLAY_NAME
        )
        return str(self.output)


manager.AnalysisManager.register_analyzer(AccountFinderSketchPlugin)
