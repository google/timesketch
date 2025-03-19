# Copyright 2025 Google Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""LogAnalyzer feature for automated log analysis using LLMs."""

# file should be placed in timesketch/lib/llms/features/log_analyzer.py

import logging
import json
from typing import Any, Dict, List
from timesketch.models.sketch import Sketch
from timesketch.lib.llms.features.interface import LLMFeatureInterface

logger = logging.getLogger("timesketch.llm.log_analyzer_feature")

class LogAnalyzer(LLMFeatureInterface):
    """LogAnalyzer feature for automated log analysis."""
    
    NAME = "log_analyzer"
    
    def _get_prompt_template(self) -> str:
        """Returns a hardcoded prompt template for log analysis."""
        return """
        Analyze the security logs from sketch {sketch_id} ({sketch_name}).
        
        Focus on {log_type} logs and identify any potential security incidents or suspicious activity.
        Pay special attention to:
        - Successful/failed authentication attempts
        - Privilege escalation
        - Data exfiltration
        - Command execution
        - Lateral movement
        
        Current query filter: {query_string}
        
        Provide a detailed analysis of the logs, including:
        - Attack stages identified
        - Key findings and investigative questions
        - Specific conclusions with relevant entities (IPs, usernames, etc.)
        """

    def generate_prompt(self, sketch: Sketch, **kwargs: Any) -> str:
        """Generates a prompt for log analysis."""
        form = kwargs.get("form", {})
        log_type = form.get("log_type", "all")
        query_string = form.get("query", "*") or "*"
        
        # Format the prompt with the provided information
        prompt = self._get_prompt_template().format(
            sketch_id=sketch.id,
            sketch_name=sketch.name,
            log_type=log_type,
            query_string=query_string
        )
        
        return prompt

    def process_response(self, llm_response: Any, **kwargs: Any) -> Dict[str, Any]:
        """
        Processes the LLM response and formats it for frontend consumption.
        
        Transforms data from Arcadia's record_id-based structure to a hierarchical question-centric 
        structure where each question has one conclusion and multiple observables.
        
        Args:
            llm_response: The response from the Arcadia LLM provider.
            **kwargs: Additional arguments including sketch_id.
                
        Returns:
            Dict containing hierarchically structured analysis results.
        """
        sketch_id = kwargs.get("sketch_id")
        
        # Handle JSON string response from Arcadia
        if isinstance(llm_response, str):
            try:
                arcadia_response = json.loads(llm_response)
            except json.JSONDecodeError:
                logger.error("Failed to parse Arcadia response as JSON")
                return {"questions": [], "meta": {"error": "Invalid JSON response", "raw_response": llm_response[:200]}}
        else:
            arcadia_response = llm_response
        
        if not isinstance(arcadia_response, dict):
            return {"questions": [], "meta": {"error": "Expected dictionary response"}}

        questions_dict = {}

        for record_id, record_data in arcadia_response.items():
            for conclusion in record_data.get("conclusions", []):
                question_text = conclusion.get("question")
                if not question_text:
                    continue
                
                if question_text not in questions_dict:
                    questions_dict[question_text] = {
                        "text": question_text,
                        "conclusion": conclusion.get("conclusion", ""),  # Use first conclusion as main
                        "observables": []
                    }
                
                # Add record as observable
                observable = {
                    "record_id": int(record_id),
                    "log_name": record_data.get("log_name", "unknown"),
                    "attack_stage": record_data.get("attack_stage", "Unknown"),
                    "observable_type": record_data.get("observable_type"),
                    "conclusion": conclusion.get("conclusion", ""),
                    "entities": conclusion.get("entities", []),
                    "log_details": record_data.get("log_details", {})
                }
                
                questions_dict[question_text]["observables"].append(observable)
        
        questions_list = []
        for question_text, data in questions_dict.items():
            questions_list.append({
                "id": int(record_id),
                "text": question_text,
                "conclusion": data["conclusion"],
                "observables": data["observables"],
                "total_observables": len(data["observables"]),
                "risk_level": "high"
            })
        
        response = {
            "questions": questions_list,
            "meta": {
                "summary": "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. Sed nisi. Nulla quis sem at nibh elementum imperdiet. Duis sagittis ipsum. Praesent mauris. Fusce nec tellus sed augue semper porta. Mauris massa. Vestibulum lacinia arcu eget nulla. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat." ,
                "sketch_id": sketch_id,
                "total_questions": len(questions_list),
                "total_observables": sum(len(q["observables"]) for q in questions_list)
            }
        }
        
        return response
