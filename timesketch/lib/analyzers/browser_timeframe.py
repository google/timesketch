"""Sketch analyzer plugin for browser timeframe."""

from __future__ import unicode_literals

import collections
import pandas as pd

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import utils


def get_list_of_consecutive_sequences(hour_list):
    """Returns a list of runs from a list of numbers.

    Args:
        hour_list: a list of integers.

    Returns:
        A list of tuples, where each tuple indicates the first
        and last record of a consecutive run of numbers, eg
        list 1, 2, 3, 7, 8, 9 would produce the output
        of (1,3), (7, 9).
    """
    runs = []
    if not hour_list:
        return runs

    start = hour_list[0]
    now = start
    for hour in hour_list[1:]:
        if hour == (now + 1):
            now = hour
            continue

        runs.append((start, now))
        start = hour
        now = start

    if not runs:
        runs = [(hour_list[0], hour_list[-1])]

    last_start, last_end = runs[-1]

    if (start != last_start) and (last_end != now):
        runs.append((start, now))

    return runs


def fix_gap_in_list(hour_list):
    """Returns a list with gaps in it fixed.

    Args:
        hour_list: a list of integers in a sequence, potentially
            with holes in the sequence.

    Returns:
        A list that consists of the input numbers with single
        integer gaps filled. The list should not have more than
        two runs. Therefore if there are more than two runs after
        all gaps have been filled the "extra" runs will be dropped.
    """
    if not hour_list:
        return hour_list

    runs = get_list_of_consecutive_sequences(hour_list)
    len_runs = len(runs)

    for i in range(0, len_runs - 1):
        _, upper = runs[i]
        next_lower, _ = runs[i + 1]
        if (upper + 1) == (next_lower - 1):
            hour_list.append(upper + 1)

    hours = sorted(hour_list)
    runs = get_list_of_consecutive_sequences(hour_list)

    if len(runs) <= 2:
        return hours
    if len_runs < len(runs):
        return fix_gap_in_list(hours)

    # Now we need to remove runs, we only need the first and last.
    run_start = runs[0]
    run_end = runs[-1]
    hours = list(range(0, run_start[1] + 1))
    hours.extend(range(run_end[0], run_end[1] + 1))

    return sorted(hours)


def get_active_hours(frame):
    """Return a list of the hours with the most activity within a frame.

    Args:
        frame: a pandas DataFrame object that contains a datetime column.

    Returns:
        A tuple that contains three items:
            1. list of hours where the most activity within the DataFrame
            occurs.
            2. the threshold used to determine what is considered to be
            an active hour.
            3. a DataFrame object containing the aggregation.

    """
    frame_count = frame[["datetime", "hour"]].groupby("hour", as_index=False).count()
    frame_count["count"] = frame_count["datetime"]
    del frame_count["datetime"]

    stats = frame_count["count"].describe()

    # Define few different options for the threshold value of what constitutes
    # an active hour. Then we choose the method that has the highest active
    # hour count, as long as it is between 3 and 12 hours.
    thresholds = {
        stats["75%"] - stats["mean"]: 0,
        stats["75%"]: 0,
        stats["50%"]: 0,
        stats["25%"]: 0,
    }
    for threshold in thresholds:
        threshold_filter = frame_count["count"] >= threshold
        hours = list(frame_count[threshold_filter].hour.values)
        hours = sorted(hours)

        hour_len = len(hours)
        if 3 <= hour_len <= 12:
            thresholds[threshold] = hour_len

    threshold_counter = collections.Counter(thresholds)
    threshold, _ = threshold_counter.most_common(1)[0]

    threshold_filter = frame_count["count"] >= threshold
    hours = list(frame_count[threshold_filter].hour.values)
    hours = sorted(hours)
    runs = get_list_of_consecutive_sequences(hours)

    # There should either be a single run or at most two.
    number_runs = len(runs)
    if number_runs == 1:
        return hours, threshold, frame_count

    if number_runs == 2 and runs[0][0] == 0:
        # Two runs, first one starts at hour zero.
        return hours, threshold, frame_count

    return fix_gap_in_list(hours), threshold, frame_count


class BrowserTimeframeSketchPlugin(interface.BaseAnalyzer):
    """Analyzer for BrowserTimeframe."""

    NAME = "browser_timeframe"
    DISPLAY_NAME = "Browser timeframe"
    DESCRIPTION = (
        "Determine user activity hours by finding the frequency of browsing events"
    )

    DEPENDENCIES = frozenset()

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        # TODO: Once we can identify user generated events this should be
        # updated to include all user generated events instead of focusing
        # solely on browser events.
        query = 'source_short:"WEBHIST" OR source:"WEBHIST"'

        return_fields = ["datetime", "timestamp", "url", "tag", "__ts_emojis"]

        data_frame = self.event_pandas(query_string=query, return_fields=return_fields)

        if not data_frame.shape[0]:
            return "No browser events discovered."

        sleeping_emoji = emojis.get_emoji("SLEEPING_FACE")

        # This query filters out all timestamps that have a zero timestamp as
        # well as those that occur after 2038-01-01, this may need to be
        # changed in the future.
        data_frame["timestamp"] = pd.to_numeric(data_frame.timestamp)
        data_frame = data_frame[
            (data_frame.timestamp > 0) & (data_frame.timestamp < 2145916800000000)
        ]

        data_frame["datetime"] = pd.to_datetime(
            data_frame.timestamp / 1e6, utc=True, unit="s"
        )
        data_frame["hour"] = pd.to_numeric(data_frame.datetime.dt.strftime("%H"))

        total_count = data_frame.shape[0]
        activity_hours, threshold, aggregation = get_active_hours(data_frame)

        if not activity_hours:
            return "Did not discover any activity hours."

        hour_count = dict(aggregation.values.tolist())
        data_frame_outside = data_frame[~data_frame.hour.isin(activity_hours)]

        for event in utils.get_events_from_data_frame(
            data_frame_outside, self.datastore
        ):
            event.add_tags(["outside-active-hours"])
            hour = event.source.get("hour")
            this_hour_count = hour_count.get(hour)
            event.add_attributes(
                {
                    "activity_summary": (
                        "Number of events for this hour ({0:d}): {1:d}, with the "
                        "threshold value: {2:0.2f}"
                    ).format(hour, this_hour_count, threshold),
                    "hour_count": this_hour_count,
                }
            )
            event.add_emojis([sleeping_emoji])
            event.commit()

        tagged_events, _ = data_frame_outside.shape
        if tagged_events:
            story = self.sketch.add_story(
                "{0:s} - {1:s}".format(utils.BROWSER_STORY_TITLE, self.timeline_name)
            )
            story.add_text(utils.BROWSER_STORY_HEADER, skip_if_exists=True)

            # Find some statistics about the run time of the analyzer.
            percent = (tagged_events / total_count) * 100.0
            last_hour = activity_hours[0]
            end = 0
            for hour in activity_hours[1:]:
                if hour != last_hour + 1:
                    end = hour
                    break
                last_hour = hour

            if not end:
                first = activity_hours[0]
                last = activity_hours[-1]
            else:
                first = end
                index = activity_hours.index(end)
                last = activity_hours[index - 1]

            story.add_text(
                "## Browser Timeframe Analyzer\n\nThe browser timeframe "
                "analyzer discovered {0:d} browser events that occurred "
                "outside of the typical browsing window of this browser "
                "history ({1:s}), or around {2:0.2f}%  of the {3:d} total "
                "events.\n\nThe analyzer determines the activity hours by "
                "finding the frequency of browsing events per hour, and then "
                "discovering the longest block of most active hours before "
                "proceeding with flagging all events outside of that time "
                "period. This information can be used by other analyzers "
                "or by manually looking for other activity within the "
                "inactive time period to find unusual actions.\n\n"
                "The hours considered to be active hours are the hours "
                "between {4:02d} and {5:02d} (hours in UTC) and the "
                "threshold used to determine if an hour was considered to be "
                "active was: {6:0.2f}.".format(
                    tagged_events,
                    self.timeline_name,
                    percent,
                    total_count,
                    first,
                    last,
                    threshold,
                )
            )

            group = self.sketch.add_aggregation_group(
                name="Browser Activity Per Hour",
                description="Created by the browser timeframe analyzer",
            )
            group.set_layered()

            params = {
                "data": aggregation.to_dict(orient="records"),
                "title": "Browser Activity Per Hour ({0:s})".format(self.timeline_name),
                "field": "hour",
                "order_field": "hour",
            }
            agg_obj = self.sketch.add_aggregation(
                name="Browser Activity Per Hour ({0:s})".format(self.timeline_name),
                agg_name="manual_feed",
                agg_params=params,
                chart_type="barchart",
                description="Created by the browser timeframe analyzer",
                label="informational",
            )
            group.add_aggregation(agg_obj)

            lines = [{"hour": x, "count": threshold} for x in range(0, 24)]
            params = {
                "data": lines,
                "title": "Browser Timeframe Threshold ({0:s})".format(
                    self.timeline_name
                ),
                "field": "hour",
                "order_field": "hour",
                "chart_color": "red",
            }
            agg_line = self.sketch.add_aggregation(
                name="Browser Activity Per Hour ({0:s})".format(self.timeline_name),
                agg_name="manual_feed",
                agg_params=params,
                chart_type="linechart",
                description="Created by the browser timeframe analyzer",
                label="informational",
            )
            group.add_aggregation(agg_line)
            story.add_aggregation_group(group)

        return (
            "Tagged {0:d} out of {1:d} events as outside of normal " "active hours."
        ).format(tagged_events, total_count)


manager.AnalysisManager.register_analyzer(BrowserTimeframeSketchPlugin)
