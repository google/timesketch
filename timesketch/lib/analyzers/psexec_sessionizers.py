"""Psexec sequence activity sessionizing sketch analyzer plugins."""

from __future__ import unicode_literals

from timesketch.lib.analyzers import manager
from timesketch.lib.analyzers import sequence_sessionizer

# TODO Add PSEXEC sequence sessionizer for the source side.

DEST_SEQ = [
    {
        "data_type": "windows:evtx:record",
        "message": "A service was installed in the system.",
    },
    {"data_type": "windows:prefetch:execution", "executable": "PSEXESVC.EXE"},
]


class DestPsexecSessionizerSketchPlugin(
    sequence_sessionizer.SequenceSessionizerSketchPlugin
):
    """Sessionizer for seqeunced psexec activity on the server."""

    NAME = "dest_psexec_sessionizer"
    query = "PSEXEC OR PSEXESVC OR PSEXESVC.EXE"
    event_seq = DEST_SEQ
    session_type = "psexec_dest"
    return_fields = None


manager.AnalysisManager.register_analyzer(DestPsexecSessionizerSketchPlugin)
