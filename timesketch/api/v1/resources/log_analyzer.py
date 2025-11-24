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
"""Resources for log analyzer features."""

from flask_restful import Resource
from flask_login import login_required


class LogAnalyzerPromptResource(Resource):
    """Resource for the log analyzer default prompt."""

    @login_required
    def get(self):
        """Handles GET requests to the resource.

        Returns:
            A dictionary containing the default prompt.
        """
        return {"default_prompt": "Analyze the attached logs for any signs of a compromise."}
