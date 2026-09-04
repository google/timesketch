"""Tests for the LLM Log Analyzer."""

import json
from unittest import mock

from timesketch.lib.analyzers import llm_log_analyzer
from timesketch.lib.testlib import BaseTest
from timesketch.lib.testlib import MockDataStore
from timesketch.models.sketch import Story


class TestLLMLogAnalyzer(BaseTest):
    """Tests the LLM Log Analyzer."""

    @mock.patch("timesketch.lib.analyzers.interface.OpenSearchDataStore", MockDataStore)
    @mock.patch.object(
        llm_log_analyzer.llm_provider_manager.LLMManager, "create_provider"
    )
    @mock.patch.object(
        llm_log_analyzer.feature_manager.FeatureManager, "get_feature_instance"
    )
    def test_non_secgemini_provider_story(self, mock_feature, mock_provider):
        """A non-SecGemini provider can create a successful report story."""
        provider = mock.Mock(spec=["NAME"])
        provider.NAME = "local_provider"
        mock_provider.return_value = provider

        feature = mock.Mock()
        feature.NAME = "log_analyzer"
        feature.execute.return_value = {
            "status": "success",
            "events_exported": 1,
            "total_findings_processed": 1,
            "errors_encountered": 0,
            "full_response_text": "complete report",
        }
        mock_feature.return_value = feature

        analyzer = llm_log_analyzer.LLMLogAnalyzer("test_index", 1, timeline_id=1)
        result = json.loads(analyzer.run())

        self.assertEqual(result["result_status"], "SUCCESS")
        story = Story.query.filter_by(
            sketch_id=1, title="Full AI Log Analysis Report - [N/A]"
        ).one()
        self.assertIn("complete report", story.content)
