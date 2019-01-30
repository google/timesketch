"""Sketch analyzer plugin for browser timeframe."""
from __future__ import unicode_literals

import pandas as pd

from timesketch.lib import emojis
from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import utils


def get_runs(hour_list):
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
    runs = get_runs(hour_list)
    len_runs = len(runs)

    for i in range(0, len_runs - 1):
        _, upper = runs[i]
        next_lower, _ = runs[i+1]
        if (upper + 1) == (next_lower - 1):
            hour_list.append(upper + 1)

    hours = sorted(hour_list)
    runs = get_runs(hour_list)

    if len(runs) <= 2:
        return hours
    elif len_runs < len(runs):
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
    frame_count = frame[['datetime', 'hour']].groupby(
        'hour', as_index=False).count()
    frame_count['count'] = frame_count['datetime']
    del frame_count['datetime']

    stats = frame_count['count'].describe()

    # We use the 75% value - mean of all counts as the "bar" to which we
    # determine an hour to be active.
    threshold = stats['75%'] - stats['mean']

    threshold_filter = frame_count['count'] >= threshold
    hours = list(frame_count[threshold_filter].hour.values)
    hours = sorted(hours)

    runs = get_runs(hours)

    # There should either be a single run or at most two.
    number_runs = len(runs)
    if number_runs == 1:
        return hours, threshold, frame_count

    elif number_runs == 2 and runs[0][0] == 0:
        # Two runs, first one starts at hour zero.
        return hours, threshold, frame_count

    return fix_gap_in_list(hours), threshold, frame_count


class BrowserTimeframeSketchPlugin(interface.BaseSketchAnalyzer):
    """Sketch analyzer for BrowserTimeframe."""

    NAME = 'browser_timeframe'
    DEPENDENCIES = frozenset()

    def __init__(self, index_name, sketch_id):
        """Initialize The Sketch Analyzer.

        Args:
            index_name: Elasticsearch index name
            sketch_id: Sketch ID
        """
        self.index_name = index_name
        super(BrowserTimeframeSketchPlugin, self).__init__(
            index_name, sketch_id)

    def run(self):
        """Entry point for the analyzer.

        Returns:
            String with summary of the analyzer result
        """
        # TODO: Once we can identify user generated events this should be
        # updated to include all user generated events instead of focusing
        # solely on browser events.
        query = 'source_short:"WEBHIST"'
        return_fields = ['timestamp', 'url', 'tag', '__ts_emojis']

        data_frame = self.event_pandas(
            query_string=query, return_fields=return_fields)

        if not data_frame.shape[0]:
            return 'No browser events discovered.'

        sleeping_emoji = emojis.get_emoji('SLEEPING_FACE')

        data_frame['timestamp'] = pd.to_numeric(data_frame.timestamp)
        data_frame['datetime'] = pd.to_datetime(
            data_frame.timestamp / 1e6, utc=True, unit='s')
        data_frame['hour'] = pd.to_numeric(
            data_frame.datetime.dt.strftime('%H'))

        total_count = data_frame.shape[0]
        activity_hours, threshold, aggregation = get_active_hours(data_frame)

        hour_count = dict(aggregation.values.tolist())
        data_frame_outside = data_frame[~data_frame.hour.isin(activity_hours)]

        for event in utils.get_events_from_data_frame(
                data_frame_outside, self.datastore):
            event.add_tags(['outside-active-hours'])
            hour = event.source.get('hour')
            this_hour_count = hour_count.get(hour)
            event.add_attributes(
                {'activity_summary': (
                    'Number of events for this hour ({0:d}): {1:d}, with the '
                    'threshold value: {2:0.2f}').format(
                        hour, this_hour_count, threshold),
                 'hour_count': this_hour_count})
            event.add_emojis([sleeping_emoji])
            event.commit()

        return (
            'Tagged {0:d} out of {1:d} events as outside of normal '
            'active hours.').format(data_frame_outside.shape[0], total_count)


manager.AnalysisManager.register_analyzer(BrowserTimeframeSketchPlugin)
