# Copyright 2024 Google Inc. All rights reserved.
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
"""Tests for the status race condition."""

from timesketch.lib.testlib import BaseTest
from timesketch.models import db_session, session_maker
from timesketch.models.sketch import SearchIndex

class StatusRaceTest(BaseTest):
    """Test the status race condition."""

    def test_reproduce_race_condition(self):
        """Reproduce the race condition by simulating concurrent sessions."""
        # 1. Create a search index
        si = SearchIndex(
            name="test_race",
            description="test",
            user=self.user1,
            index_name="test_race",
        )
        db_session.add(si)
        db_session.commit()
    
        # Trigger initial status 'new' and commit it.
        _ = si.get_status
        db_session.commit()
        self.assertEqual(len(si.status), 1)

        # 2. Simulate two workers using DIFFERENT session objects on the SAME DB.
        # Since this is SQLite in BaseTest, it uses a file-based or shared cache DB?
        # Actually, BaseTest setup usually creates a clean DB.
        
        session1 = db_session
        session2 = session_maker()
        
        # Fetch object in both sessions
        si1 = session1.get(SearchIndex, si.id)
        si2 = session2.get(SearchIndex, si.id)
    
        # Call set_status with DIFFERENT values in BOTH workers.
        # Worker 1 sets to 'status_A'
        si1.set_status("status_A")
        session1.commit()
        
        # Worker 2 sets to 'status_B'
        si2.set_status("status_B")
        session2.commit()
        session2.close()
    
        # 3. Verify exactly one status should remain, and it should be 'status_B'
        session1.expire_all()
        si_final = session1.get(SearchIndex, si.id)
        
        status_count = len(si_final.status)
        print(f"\nDEBUG: Final status count for object {si_final.id} is {status_count}")
        
        # Access get_status to verify no warning is triggered
        current_status = si_final.get_status
        print(f"DEBUG: Current status from get_status: {current_status.status}")
        
        self.assertEqual(status_count, 1, "Should have exactly one status after fix")
        self.assertEqual(current_status.status, 'status_B', "Last writer should win and overwrite previous")
