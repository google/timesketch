# Copyright 2026 Google Inc. All rights reserved.
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
"""Tests for index_name module."""

import unittest
import uuid

from timesketch.lib import index_name


class IndexNameTest(unittest.TestCase):
    """Tests for index_name utility functions."""

    def test_validate_index_prefix(self):
        """Test validate_index_prefix validation rules."""
        # Valid prefixes
        index_name.validate_index_prefix(None)
        index_name.validate_index_prefix("")
        index_name.validate_index_prefix("timesketch-")
        index_name.validate_index_prefix("timesketch_")
        index_name.validate_index_prefix("ts-")
        index_name.validate_index_prefix("ts123-")

        # Non-string prefixes
        with self.assertRaises(ValueError):
            index_name.validate_index_prefix(123)
        with self.assertRaises(ValueError):
            index_name.validate_index_prefix(False)

        # Disallowed prefix formats
        invalid_prefixes = [
            "Timesketch-",  # uppercase
            "-timesketch-",  # starts with hyphen
            "_timesketch-",  # starts with underscore
            "+timesketch-",  # starts with plus
            "timesketch -",  # contains space
            "timesketch/*-",  # contains special characters
        ]
        for inv in invalid_prefixes:
            with self.assertRaises(ValueError):
                index_name.validate_index_prefix(inv)
            with self.assertRaises(ValueError):
                index_name.canonicalize_index_name(None, prefix=inv)
            with self.assertRaises(ValueError):
                index_name.is_canonical_index_name(
                    "timesketch-a89933473b2a48948beee2c7e870209f", prefix=inv
                )

    def test_is_uuid_hex(self):
        """Test is_uuid_hex validation."""
        valid_hex = uuid.uuid4().hex
        self.assertTrue(index_name.is_uuid_hex(valid_hex))
        self.assertTrue(index_name.is_uuid_hex(valid_hex.upper()))
        self.assertTrue(index_name.is_uuid_hex("a89933473b2a48948beee2c7e870209f"))

        # Negative cases
        self.assertFalse(index_name.is_uuid_hex(None))
        self.assertFalse(index_name.is_uuid_hex(""))
        self.assertFalse(index_name.is_uuid_hex(123))
        self.assertFalse(index_name.is_uuid_hex("short"))
        # 31 chars
        self.assertFalse(index_name.is_uuid_hex("a89933473b2a48948beee2c7e870209"))
        # 33 chars
        self.assertFalse(index_name.is_uuid_hex("a89933473b2a48948beee2c7e870209ff"))
        # non-hex
        self.assertFalse(index_name.is_uuid_hex("g89933473b2a48948beee2c7e870209f"))
        self.assertFalse(index_name.is_uuid_hex("malcolm-session-123"))
        self.assertFalse(
            index_name.is_uuid_hex("timesketch-a89933473b2a48948beee2c7e870209f")
        )

    def test_is_canonical_index_name_with_prefix(self):
        """Test is_canonical_index_name when prefix is configured."""
        prefix = "timesketch-"
        valid_hex = "a89933473b2a48948beee2c7e870209f"
        canonical = f"{prefix}{valid_hex}"

        self.assertTrue(index_name.is_canonical_index_name(canonical, prefix=prefix))

        # OpenSearch index names must be lowercase; uppercase is not canonical
        self.assertFalse(
            index_name.is_canonical_index_name(canonical.upper(), prefix=prefix)
        )
        self.assertFalse(
            index_name.is_canonical_index_name(
                f"{prefix}{valid_hex.upper()}", prefix=prefix
            )
        )

        # Bare UUID is not canonical when prefix is required
        self.assertFalse(index_name.is_canonical_index_name(valid_hex, prefix=prefix))

        # Partial prefix or invalid suffixes
        self.assertFalse(index_name.is_canonical_index_name(None, prefix=prefix))
        self.assertFalse(index_name.is_canonical_index_name("", prefix=prefix))
        self.assertFalse(
            index_name.is_canonical_index_name("timesketch-", prefix=prefix)
        )
        self.assertFalse(
            index_name.is_canonical_index_name(
                "timesketch-malcolm-session-123", prefix=prefix
            )
        )
        self.assertFalse(
            index_name.is_canonical_index_name("timesketch-whoops", prefix=prefix)
        )
        self.assertFalse(
            index_name.is_canonical_index_name(
                "timesketch-../../whatever", prefix=prefix
            )
        )
        self.assertFalse(
            index_name.is_canonical_index_name(
                "otherprefix-" + valid_hex, prefix=prefix
            )
        )

    def test_is_canonical_index_name_empty_prefix(self):
        """Test is_canonical_index_name when prefix is empty."""
        valid_hex = "a89933473b2a48948beee2c7e870209f"
        self.assertTrue(index_name.is_canonical_index_name(valid_hex, prefix=""))
        self.assertFalse(
            index_name.is_canonical_index_name(valid_hex.upper(), prefix="")
        )
        self.assertFalse(
            index_name.is_canonical_index_name("timesketch-" + valid_hex, prefix="")
        )
        self.assertFalse(index_name.is_canonical_index_name("arbitrary", prefix=""))
        self.assertFalse(index_name.is_canonical_index_name(None, prefix=""))

    def test_canonicalize_index_name_with_prefix(self):
        """Test canonicalize_index_name when prefix is configured."""
        prefix = "timesketch-"
        bare_uuid = "a89933473b2a48948beee2c7e870209f"

        # None or empty -> generated prefixed UUID
        gen1 = index_name.canonicalize_index_name(None, prefix=prefix)
        self.assertTrue(gen1.startswith(prefix))
        self.assertTrue(index_name.is_canonical_index_name(gen1, prefix=prefix))

        gen2 = index_name.canonicalize_index_name("", prefix=prefix)
        self.assertTrue(gen2.startswith(prefix))
        self.assertTrue(index_name.is_canonical_index_name(gen2, prefix=prefix))
        self.assertNotEqual(gen1, gen2)

        # Bare UUID -> canonicalized to prefixed UUID
        result = index_name.canonicalize_index_name(bare_uuid, prefix=prefix)
        self.assertEqual(result, f"timesketch-{bare_uuid}")

        # Mixed-case bare UUID normalized to lowercase
        result_upper = index_name.canonicalize_index_name(
            bare_uuid.upper(), prefix=prefix
        )
        self.assertEqual(result_upper, f"timesketch-{bare_uuid.lower()}")

        # Already prefixed UUID (including uppercase) -> normalized to lowercase
        prefixed = f"timesketch-{bare_uuid}"
        self.assertEqual(
            index_name.canonicalize_index_name(prefixed, prefix=prefix),
            prefixed,
        )
        self.assertEqual(
            index_name.canonicalize_index_name(prefixed.upper(), prefix=prefix),
            prefixed,
        )

        # Non-string falsy values must raise ValueError
        for non_string_val in [False, 0, [], {}, 0.0]:
            with self.assertRaises(ValueError):
                index_name.canonicalize_index_name(non_string_val, prefix=prefix)

        # Invalid index names must be rejected
        with self.assertRaises(ValueError):
            index_name.canonicalize_index_name("malcolm-session-123", prefix=prefix)

        with self.assertRaises(ValueError):
            index_name.canonicalize_index_name("test3", prefix=prefix)

        with self.assertRaises(ValueError):
            index_name.canonicalize_index_name("timesketch-whoops", prefix=prefix)

        with self.assertRaises(ValueError):
            index_name.canonicalize_index_name(
                "timesketch-../../traversal", prefix=prefix
            )

        with self.assertRaises(ValueError):
            index_name.canonicalize_index_name(123, prefix=prefix)

    def test_canonicalize_index_name_empty_prefix(self):
        """Test canonicalize_index_name when prefix is empty (upstream default)."""
        bare_uuid = "a89933473b2a48948beee2c7e870209f"

        # None or empty -> generated bare UUID
        gen1 = index_name.canonicalize_index_name(None, prefix="")
        self.assertTrue(index_name.is_uuid_hex(gen1))

        # Bare UUID -> bare UUID lowercase
        result = index_name.canonicalize_index_name(bare_uuid, prefix="")
        self.assertEqual(result, bare_uuid)

        # Non-string falsy values must raise ValueError
        for non_string_val in [False, 0, [], {}, 0.0]:
            with self.assertRaises(ValueError):
                index_name.canonicalize_index_name(non_string_val, prefix="")

        # Invalid names
        with self.assertRaises(ValueError):
            index_name.canonicalize_index_name("malcolm-session-123", prefix="")

        with self.assertRaises(ValueError):
            index_name.canonicalize_index_name("test3", prefix="")


if __name__ == "__main__":
    unittest.main()
