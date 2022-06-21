# Copyright 2019 Google Inc. All rights reserved.
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
"""Tests for emojis support."""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from timesketch.lib import emojis
from timesketch.lib.testlib import BaseTest


class TestEmojisLib(BaseTest):
    """Tests for the emojis support library."""

    def test_get_emoji(self):
        """Test getting emoji code."""
        skull_emoji = emojis.get_emoji("skull_crossbone")
        skull_code = "&#x2620"

        self.assertEqual(skull_emoji, skull_code)

        locomotive_emoji = emojis.get_emoji("LOCOMOTIVE")
        locomotive_code = "&#x1F682"
        self.assertEqual(locomotive_emoji, locomotive_code)

        does_not_exist = emojis.get_emoji("er_ekki_til")
        self.assertEqual(does_not_exist, "")

    def test_get_helper_from_unicode(self):
        """Test getting helper text from an emoji code."""
        skull_emoji = emojis.get_emoji("skull_crossbone")
        skull_helper = emojis.get_helper_from_unicode(skull_emoji)
        helper_text = "Suspicious entry"

        self.assertEqual(skull_helper, helper_text)

        does_not_exist = emojis.get_helper_from_unicode("er_ekki_til")
        self.assertEqual(does_not_exist, "")

    def test_get_emojis_as_dict(self):
        """Test getting emojis as a dictionary."""
        skull_code = "&#x2620"
        helper_text = "Suspicious entry"
        emojis_dict = emojis.get_emojis_as_dict()
        skull_helper = emojis_dict.get(skull_code)
        self.assertEqual(skull_helper, helper_text)

        does_not_exist = emojis_dict.get("finns_inte")
        self.assertIsNone(does_not_exist)
