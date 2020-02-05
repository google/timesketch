"""Expert sesssionizer plugins, configured for specific types of activity"""

from __future__ import unicode_literals

from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers.sessionizer import SessionizerSketchPlugin


class WebActivitySessionizerSketchPlugin(SessionizerSketchPlugin):
    """Sessionizer for web activity events"""
    NAME = 'web_activity_sessionizer'
    max_time_diff_micros = 600000000  # 10 minutes
    query = 'source_short:"WEBHIST"'
    session_type = 'web_activity'


class SSHBruteforceSessionizerSketchPlugin(SessionizerSketchPlugin):
    """Sessionizer for SSH bruteforce attacks, where the events that form an
    attack are repeated password failures or attempts to login as a user
    that does not exist."""
    NAME = 'ssh_bruteforce_sessionizer'
    max_time_diff_micros = 10000000 # 10 seconds
    query = 'reporter:"sshd" AND ((message:"invalid user" AND NOT message:' \
        '("keyboard-interactive" OR "connection closed")) OR message:(' \
        '"message repeated" AND "failed password for"))'
    session_type = 'ssh_bruteforce'


manager.AnalysisManager.register_analyzer(WebActivitySessionizerSketchPlugin)
manager.AnalysisManager.register_analyzer(SSHBruteforceSessionizerSketchPlugin)
