"""Sketch analyzer plugin for detecting gaps in EVTX files."""

from __future__ import unicode_literals

import logging

import datetime
import pandas as pd
import numpy as np

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


logger = logging.getLogger("timesketch.analyzer.evtxgap")


def get_range(my_list, complete_list):
    """Yields a 2-tuple with ranges within a list.

    Args:
        my_list (list): The list that contains potential ranges.
        complete_list (list): The list that contains all potential
            values for comparison.

    Yields:
        Tuple[int, int]: A 2-tuple with the start and end of the range.
    """
    list_length = len(my_list)
    cur_first = my_list[0]

    for index in range(0, list_length):
        cur_item = my_list[index]
        try:
            cur_index = complete_list.index(cur_item)
        except ValueError:
            logger.error(
                "Value in list does not exist in the complete list, and "
                "therefore unable to extract a range."
            )
            return
        if index == list_length - 1:
            yield (cur_first, cur_item)
            continue

        if my_list[index + 1] != complete_list[cur_index + 1]:
            yield (cur_first, cur_item)
            cur_first = my_list[index + 1]


class EvtxGapPlugin(interface.BaseAnalyzer):
    """Analyzer for detecting gaps in EVTX records."""

    NAME = "evtx_gap"
    DISPLAY_NAME = "EVTX gap"
    DESCRIPTION = "Detect gaps in EVTX logs"

    DEPENDENCIES = frozenset()

    # The title of the story the analyzer generates.
    STORY_TITLE = "EVTX Gap Analysis"

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        query = 'data_type:"windows:evtx:record"'

        return_fields = ["datetime", "timestamp", "record_number", "source_name"]

        # Generator of events based on your query.
        event_frame = self.event_pandas(
            query_string=query, indices=[self.index_name], return_fields=return_fields
        )

        if not event_frame.shape[0]:
            return "No EVTX events discovered."

        # 1. Find gaps in ranges of record numbers.
        record_gaps = {}
        for source in event_frame.source_name.unique():
            source_frame = event_frame[event_frame.source_name == source]
            # Find the lowest and highest record number for the source.
            low, high = (
                source_frame.sort_values(by="record_number")
                .iloc[[0, -1]]
                .record_number.values
            )
            if isinstance(low, str):
                low = int(low)
            if isinstance(high, str):
                high = int(high)

            record_numbers = set(source_frame.record_number.unique())
            record_numbers = {int(x) for x in record_numbers}
            all_numbers = {int(x) + low for x in range(0, high - low + 1)}

            missing_records = all_numbers.difference(record_numbers)
            if not missing_records:
                continue

            if len(missing_records) > len(all_numbers) / 2:
                # Let's rather calculate the ranges of records instead of
                # missing records.
                if record_numbers:
                    record_ranges = list(
                        get_range(
                            sorted(list(record_numbers)), sorted(list(all_numbers))
                        )
                    )
                else:
                    record_ranges = []

                record_gaps[source] = {"included": record_ranges}
            else:
                if missing_records:
                    missing_ = list(
                        get_range(
                            sorted(list(missing_records)), sorted(list(all_numbers))
                        )
                    )
                else:
                    missing_ = []
                record_gaps[source] = {"missing": missing_}

        # 2. Find gaps in ranges of days with/without records.
        event_frame["datetime"] = pd.to_datetime(event_frame.datetime)
        event_frame["day"] = event_frame.datetime.dt.strftime("%Y%m%d")
        group = event_frame[["day", "timestamp"]].groupby("day", as_index=False)

        event_count = group.count()
        event_count["count"] = event_count["timestamp"]
        del event_count["timestamp"]
        event_count.sort_values(by="day", inplace=True)

        # Generate a list of all days in between the first and last date
        # that we see of EVTX records.
        first_day_str = event_count.day.head(1).values[0]
        last_day_str = event_count.day.tail(1).values[0]

        first_date = datetime.datetime.strptime(first_day_str, "%Y%m%d")
        last_date = datetime.datetime.strptime(last_day_str, "%Y%m%d")

        day_delta = last_date - first_date

        all_days = []
        for day_count in range(day_delta.days + 1):
            day = first_date + datetime.timedelta(days=day_count)
            all_days.append(int(day.strftime("%Y%m%d")))

        current_days = [int(day) for day in event_count.day.values]
        missing_days = list(set(all_days).difference(set(current_days)))

        if missing_days:
            missing_ranges = list(get_range(missing_days, all_days))
        else:
            missing_ranges = []

        if not (missing_ranges and record_gaps):
            return (
                "No gaps were identified in the EVTX logs, that is not to say "
                "there aren't any gaps, just that these tests weren't able "
                "to find ones."
            )

        story = self.sketch.add_story(
            "{0:s} - {1:s}".format(self.STORY_TITLE, self.timeline_name)
        )
        story.add_text(
            "This story is the result of the EVTX Gap analyzer. It attempts "
            "to detect gaps in EVTX files found in index "
            "[{0:s}](/sketch/{1:d}/explore?index={2:s}) using two different "
            "methods.\n\nFirst of all it looks at missing entries in record "
            "numbers and secondly it attempts to look at gaps in days with "
            "no records.\n\nThis may be an indication of someone clearing "
            "the logs, yet it may be an indication of something else. At "
            "least this should be interpreted as something that warrants a "
            "second look.\n\n"
            "This will obviously not catch every instance of someone clearing "
            "EVTX records, even if that's done in bulk. Therefore it should "
            "not be interpreted that if this analyzer does not discover "
            "something that the records have not been wiped. Please verify "
            "the results given by this analyzer.".format(
                self.timeline_name, self.sketch.id, self.index_name
            )
        )

        text_items = [
            "Overview of file:",
            "",
            " + First day of logs: {0:s}".format(first_date.strftime("%Y-%m-%d")),
            " + Last day of logs: {0:s}".format(last_date.strftime("%Y-%m-%d")),
            " + Number of entries: {0:d}".format(event_frame.shape[0]),
            " + Number of unique log sources: {0:d}".format(
                len(event_frame.source_name.unique())
            ),
        ]
        story.add_text("\n".join(text_items))

        params = {
            "field": "source_name",
            "supported_charts": "hbarchart",
            "index": [self.timeline_id],
            "query_string": 'data_type:"windows:evtx:record"',
        }
        agg_sources = self.sketch.add_aggregation(
            name="Top EVTX Sources",
            agg_name="query_bucket",
            agg_params=params,
            chart_type="hbarchart",
            description="Created by the EVTX Gap analyzer",
        )
        story.add_aggregation(agg_sources)

        text_items = []

        if missing_ranges:
            for day_range in missing_ranges:
                first, last = day_range
                if first == last:
                    text_items.append(" + Missing logs from **{0:d}**".format(first))
                else:
                    text_items.append(
                        " + Missing logs from: **{0:d}** all the way up to "
                        "**{1:d}**".format(first, last)
                    )

        counter_array = event_count["count"].values
        quarter = np.percentile(counter_array, 25)

        rare_days = event_count[event_count["count"] < quarter]

        for _, day in rare_days.iterrows():
            text_items.append(
                " + Day {0:s} only had {1:d} entries".format(day.day, day["count"])
            )

        text_items.append(
            '\n**"Rare days" reference days that had fewer than {0:d} '
            "records in them, which is considered to be less than the 25th "
            "percentile of all events in a given day.**".format(int(quarter))
        )

        if text_items:
            story.add_text(
                "## Event Frequency Analysis.\n\nBy looking at the number of "
                "entries per day and analyzing days that had few or no "
                "records the following gaps were discovered:\n\n{0:s}".format(
                    "\n".join(text_items)
                )
            )

        agg_obj = None
        if missing_days:
            rows_to_append = []
            for missing_day in missing_days:
                rows_to_append.append(
                    {"day": str(missing_day), "timestamp": 0, "count": 0}
                )
            df_append = pd.DataFrame(rows_to_append)
            event_count = event_count.append(df_append, sort=False)
            event_count.sort_values(by="day", inplace=True)
            if "timestamp" in event_count:
                del event_count["timestamp"]

            if event_count.shape[0]:
                params = {
                    "data": event_count.to_dict("records"),
                    "title": "Event Records Per Day",
                    "supported_charts": "barchart",
                    "field": "day",
                    "order_field": "day",
                }
                agg_obj = self.sketch.add_aggregation(
                    name="Event Records Per Day",
                    agg_name="manual_feed",
                    agg_params=params,
                    chart_type="barchart",
                    description="Created by the EVTX Gap analyzer",
                    label="informational",
                )
                story.add_aggregation(agg_obj)

        if record_gaps:
            text_items = []
            for source, record_dict in record_gaps.items():
                text_items.append("  + Source: **{0:s}**".format(source))
                if "missing" in record_dict:
                    text = "missing"
                    record_gap = record_dict["missing"]
                else:
                    text = "defined (those not defined are missing)"
                    record_gap = record_dict["included"]

                for gap in record_gap:
                    first, last = gap

                    if first == last:
                        text_items.append(
                            "    - Record number: {0:d} is {1:s}".format(first, text)
                        )
                    else:
                        text_items.append(
                            "    - Records from number {0:d} all the way "
                            "up to {1:d} are {2:s}".format(first, last, text)
                        )
            story.add_text(
                "## Event Record Number Analysis.\n\nBy looking at the record "
                "numbers and attempting to identify jumps in numbers "
                "the following gaps were discovered:\n\n{0:s}".format(
                    "\n".join(text_items)
                )
            )

        return (
            "Gaps were detected in the EVTX record. Please see generated "
            "story for further details."
        )


manager.AnalysisManager.register_analyzer(EvtxGapPlugin)
