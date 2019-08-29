"""Expert sesssionizer plugins, configured for specific types of activity"""

from __future__ import unicode_literals

from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.sessionizer import SessionizerSketchPlugin


class WebActivitySessionizerSketchPlugin(SessionizerSketchPlugin):
    NAME = 'web_activity_sessionizer'
    max_time_diff_micros = 600000000 # 10 minutes
    query = 'source_short:"WEBHIST"'
    session_type = 'web_activity'

manager.AnalysisManager.register_analyzer(WebActivitySessionizerSketchPlugin)
