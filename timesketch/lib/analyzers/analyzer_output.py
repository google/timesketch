# -*- coding: utf-8 -*-
# Copyright 2023 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""A class to store analyzer output"""

import logging
import json

from enum import IntEnum

log = logging.getLogger("timesketch")


class Priority(IntEnum):
    """Reporting priority enum to store common values.

    Priorities can be anything in the range of 0-100, where 0 is the highest
    priority.
    """
    LOW = 80
    MEDIUM = 50
    HIGH = 20
    CRITICAL = 10


class AnalyzerOutputException(Exception):
    """Analyzer output exception."""


class AnalyzerOutput:
    """A class to record analyzer output."""

    def __init__(self, analyzer_id: str, analyzer_name: str):
        self.platform = "timesketch"
        self.analyzer_identifier = analyzer_id
        self.analyzer_name = analyzer_name
        self.result_status = "Success"
        self.dfiq_question_id = ""
        self.dfiq_question_conclusion = ""
        self.result_priority = "LOW"
        self.result_summary = ""
        self.result_markdown = ""
        self.references = []
        self.attributes = []

    def validate(self) -> None:
        """Validates the analyzer output and raises exception."""
        if not self.analyzer_identifier:
            raise AnalyzerOutputException("Analyzer identifier is empty")

        if not self.analyzer_name:
            raise AnalyzerOutputException("Analyzer name is empty")

        if self.result_status.lower() not in ["success", "failed"]:
            raise AnalyzerOutputException(
                f"Unknown result status {self.result_status}")

        priority_list = ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        if self.result_priority.upper() not in priority_list:
            raise AnalyzerOutputException(
                    f"Unknown result priority value {self.result_priority}")

        if not self.result_summary:
            raise AnalyzerOutputException("Result summary is empty")

    def __str__(self) -> str:
        """Returns string output of AnalyzerOutput."""
        output = {
            "platform": self.platform,
            "analyzer_identifier": self.analyzer_identifier,
            "analyzer_name": self.analyzer_name,
            "result_status": self.result_status,
            "dfiq_question_id": self.dfiq_question_id,
            "dfiq_question_conclusion": self.dfiq_question_conclusion,
            "result_priority": self.result_priority,
            "result_summary": self.result_summary,
            "result_markdown": self.result_markdown,
            "references": self.references,
        }

        return json.dumps(output)
