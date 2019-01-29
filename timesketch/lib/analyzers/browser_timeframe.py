"""Sketch analyzer plugin for browser timeframe."""
from __future__ import unicode_literals

import pandas as pd

from timesketch.lib.analyzers import interface
from timesketch.lib.analyzers import manager


def GetEventFromFrame(frame, datastore):
  """Return."""
  for row in frame.iterrows():
      _, entry = row
      event_id = entry.get('_id')
      if not event_id:
          continue
      event_index = entry.get('_index')
      if not event_index:
          continue
      event_type = entry.get('_type')

      event_dict = dict(_id=event_id, _type=event_type, _index=index_name)
      yield interface.Event(event_dict, datastore)


def GetRuns(hour_list):
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


def FixGap(hour_list):
    runs = GetRuns(hour_list)
    len_runs = len(runs)

    for i in range(0, len_runs - 1):
        _, upper = runs[i]
        next_lower, _ = runs[i+1]
        if (upper + 1) == (next_lower - 1):
            hour_list.append(upper + 1)

    hours = sorted(hour_list)
    runs = GetRuns(hour_list)

    if len(runs) <= 2:
        return hours
    elif len_runs < len(runs):
        return FixGap(hours)

    # Now we need to remove runs, we only need the first and last.
    run_start = runs[0]
    run_end = runs[-1]
    hours = list(range(0, run_start[1] + 1))
    hours.extend(range(run_end[0], run_end[1] + 1))

    return sorted(hours)


def GetHours(frame):
    """Attempt to define a function to get the hours, based on frequency of counts."""
    # Aggregate based on hours.
    fc = frame[['datetime' ,'hour']].groupby('hour',
    as_index=False).count()
    fc['count'] = fc['datetime']
    del fc['datetime']

    # Get all the stats values.
    a = fc['count'].describe()
    # We are looking at the 75% count and reduce it by the mean to find the lower value count.
    c_value = a['75%'] - a['mean']

    # Now we've got a "bar" we can compare against to find all hours.

    # Get a list of all hours where the count is higher or equal to the bar we defined above.
    hours = list(fc[fc['count'] >= c_value].hour.values)
    hours = sorted(hours)

    # let's find out if these are contigious or not.
    runs = GetRuns(hours)

    # It should be either a single run, or two at most.
    number_runs = len(runs)

    if number_runs == 1:
        # contigious
        return hours

    elif number_runs == 2 and runs[0][0] == 0:
        # First run starts at zero.
        return hours

    return FixGap(hours)


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
        query = 'source_short:"WEBHIST"'
        return_fields = ['timestamp', 'url']

        data_frame = self.event_pandas(
            query_string=query, return_fields=return_fields)

        if not data_frame.shape[0]:
            return 'No browser events discovered.'

        data_frame['timestamp'] = pd.to_numeric(data_frame.timestamp)
        data_frame['datetime'] = pd.to_datetime(
            data_frame.timestamp / 1e6, utc=True, unit='s')
        data_frame['hour'] = pd.to_numeric(
            data_frame.datetime.dt.strftime('%H'))

        activity_hours = GetHours(data_frame)

        data_frame_outside = data_frame[~data_frame.hour.isin(activity_hours)]

        counter = 0
        for event in GetEventFromFrame(data_frame_outside, self.datastore):
          event.add_tags(['outside-active-hours'])
          counter += 1
          event.commit()

        return 'Tagged {0:d} as outside of normal active hours.'.format(
            counter)


manager.AnalysisManager.register_analyzer(BrowserTimeframeSketchPlugin)
