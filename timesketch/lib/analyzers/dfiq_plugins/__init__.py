"""DFIQ Analyzer module."""

from timesketch.lib.analyzers.dfiq_plugins import manager as dfiq_analyzer_manager

dfiq_analyzer_manager.load_dfiq_analyzers()
