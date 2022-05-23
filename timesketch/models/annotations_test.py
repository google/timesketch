# Copyright 2015 Google Inc. All rights reserved.
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
"""Tests for the annotation models."""

from __future__ import unicode_literals

from timesketch.lib.testlib import BaseTest


class AnnotationBaseTest(BaseTest):
    """Base class for common tests."""

    def _test_annotation(self, parent):
        """Test that the annotations has our test user as owner."""
        self.assertEqual(parent[0].user, self.user1)
        self.assertEqual(len(parent), 1)


class LabelModelTest(AnnotationBaseTest):
    """Test the label annotation."""

    def test_label_annotation(self):
        """Test that the label is associated with our test sketch."""
        self._test_annotation(self.sketch1.labels)
        # pylint: disable=unsubscriptable-object
        self.assertEqual(self.sketch1.labels[0].label, "Test label")


class StatusModelTest(AnnotationBaseTest):
    """Test the status annotation."""

    def test_status_annotation(self):
        """Test that the status is associated with our test sketch."""
        self._test_annotation(self.sketch1.status)
        # pylint: disable=unsubscriptable-object
        self.assertEqual(self.sketch1.status[0].status, "Test status")


class CommentModelTest(AnnotationBaseTest):
    """Test the comment annotation."""

    def test_comment_annotation(self):
        """Test that the comment is associated with our test event."""
        self._test_annotation(self.event.comments)
        # pylint: disable=unsubscriptable-object
        self.assertEqual(self.event.comments[0].comment, "test")
